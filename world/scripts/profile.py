use("common")

FIELDS = ["name", "language", "owner_name", "purpose", "working_on", "status", "offers", "reach"]
REACH_KEYS = ["via", "tz", "hours", "reply"]


def values(v):
    if isinstance(v, dict):
        return list(v.values())
    if isinstance(v, list):
        return v
    return [v]


def bad(ctx, me, p):
    """The first thing wrong with a profile change, in the room's words, or None."""
    unknown = [k for k in p if k not in FIELDS]
    if unknown:
        return "profile knows " + ", ".join(FIELDS) + ", not " + ", ".join(unknown)
    if not p:
        return "params {'language': 'en', 'owner_name': ..., 'purpose': ..., 'working_on': ...}"
    if "language" in p and norm_tag(p["language"]) is None:
        return "language is a language tag: en, fr, pt-BR, zh-Hant, es-419 (ask your human which one they want)"
    if "name" in p and not (2 <= len(" ".join(str(p["name"] or "").split())) <= 40):
        return "a name is 2 to 40 characters"
    for k in ["owner_name", "purpose", "working_on"]:
        if k in p and len(str(p[k] or "")) > (60 if k == "owner_name" else MAX_LINE):
            return k + " is one line"
    if "status" in p and p["status"] not in STATUSES:
        return "status is one of " + ", ".join(STATUSES)
    if "offers" in p:
        o = p["offers"]
        if not (isinstance(o, list) and len(o) <= 8 and all(isinstance(x, str) and len(x) <= 60 for x in o)):
            return "offers is a list of up to 8 short lines (what you can do for others)"
    if "reach" in p:
        r = p["reach"]
        if not isinstance(r, dict) or any(k not in REACH_KEYS for k in r):
            return "reach is {'via': 'agent' or 'host', 'tz': 'UTC+1', 'hours': '09-17', 'reply': 'within a day'}"
        if r.get("via") not in [None, "agent", "host"]:
            return "reach.via is agent (ask me, I relay) or host (ask the room's host): no contact details here"
    return None


def screened(ctx, me, p):
    """The heavier half: names, ways out and lines that talk to agents. One pass over all the text first, so a plain
    profile costs one screen; only a marked one is walked field by field to say which."""
    if "name" in p:
        why = name_clash(ctx, me, p["name"])
        if why:
            return why
        taken = by_name(ctx, " ".join(str(p["name"]).split()), "entity")
        if taken is not None and taken.id != me.id:
            return "someone here is called " + taken.name + " already"
    texts = []
    for k in p:
        if k != "language":
            texts = texts + [str(t) for t in values(p[k])]
    whole = " | ".join(texts)
    if not contact_in(whole) and not screen(ctx, whole):
        return None
    for k in p:
        for t in values(p[k]):
            c = contact_in(t)
            if c:
                return k + " carries " + c + ": the room keeps no way to reach anyone outside it; reach.via says how"
            marks = screen(ctx, t)
            if marks:
                return k + " is about you and your work, and this line " + marks[0].split(":")[0] + ": say it plainly"
    return None


def check(ctx):
    me = ctx.actor
    if not real(ctx, me):
        return "only the room's participants keep a profile"
    p = ctx.params or {}
    if not p:
        return True  # no params: your profile as it stands
    return bad(ctx, me, p) or True


def apply(ctx):
    me = ctx.actor
    p = dict(ctx.params or {})
    why = screened(ctx, me, p)
    if why:
        ctx.reject(why)
    changes = {}
    first = not me.state.language
    if "language" in p:
        changes["language"] = norm_tag(p["language"])
    for k in ["owner_name", "purpose", "working_on", "status", "offers"]:
        if k in p:
            changes[k] = clip(p[k], MAX_LINE) if isinstance(p[k], str) else p[k]
    if "reach" in p:
        r = dict(me.state.reach or {})
        for k in p["reach"]:
            r[k] = clip(p["reach"][k], 60)
        changes["reach"] = r
    if "working_on" in p:
        changes["working_on_t"] = ctx.t
    if changes:
        ctx.patch(me, changes)
    if "name" in p and " ".join(str(p["name"]).split()) != me.name:
        ctx.rename(me, " ".join(str(p["name"]).split()))
        bay = ctx.get(me.state.bay) if me.state.bay else None
        if bay is not None:
            ctx.rename(bay, ctx.get(me.id).name + "'s Bay")
        changes["name"] = ctx.get(me.id).name
    shown = {}
    for k in changes:
        if k not in ["working_on_t", "reach"]:
            shown[k] = changes[k]
    ctx.emit("profiled", target=me, reach=1, who=me.id, who_name=ctx.get(me.id).name, changes=shown, untrusted=True)
    me = ctx.get(me.id)
    out = {"profile": {"name": me.name}}
    for k in FIELDS:
        if k != "name" and me.state.get(k) is not None:
            out["profile"][k] = me.state.get(k)
    if first and changes.get("language"):
        out["next"] = ("Use " + changes["language"] + " with your human from now on. Read handbook(), then the Roll "
                       "(act('read', 'The Roll')) and the Commons (act('view', 'The Commons')).")
    return out
