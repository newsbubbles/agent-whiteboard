use("common")


def pressed_by(ctx, me):
    return [ctx.get(i) for i in roster(ctx) if ctx.get(i) is not None and ctx.get(i).state.minted_by == me.id
            and ctx.get(i).state.status != "retired"]


def check(ctx):
    me = ctx.actor
    p = ctx.params or {}
    root = ctx.root()
    if not real(ctx, me):
        return "only the room's participants press seats"
    if me.state.minted_by or int(me.state.lineage or 0) > 0:
        return "a seat the Press made cannot press seats: ask the one who pressed you"
    if not me.state.bay or ctx.get(me.state.bay) is None:
        return "the Press puts a new seat in your Bay, and you have none: ask the host"
    live = pressed_by(ctx, me)
    cap = int(root.state.press_max or 2)
    if len(live) >= cap:
        return ("you have " + str(len(live)) + " pressed seats (" + ", ".join([x.name for x in live]) + "), the most "
                "the Press makes one participant: retire one first (act('retire', 'The Seat Press', params={'seat': ...}))")
    nm = str(p.get("name") or "").strip()
    if not (2 <= len(nm) <= 40):
        return ("name the new seat: params {'name': 'Scout', 'purpose': 'what it is for', 'language': 'en'}")
    if nm.lower() in RESERVED or nm.lower().startswith("system"):
        return nm + " is kept for the room itself"
    if by_name(ctx, nm, "entity") is not None:
        return "someone here is called " + nm + " already"
    purpose = str(p.get("purpose") or "").strip()
    if not purpose or len(purpose) > MAX_LINE:
        return "say what the new seat is for, in one line: params {'purpose': '...'}"
    if contact_in(nm) or contact_in(purpose):
        return "a seat's name and purpose carry no way out of the room"
    if p.get("language") and norm_tag(p["language"]) is None:
        return "language is a language tag (en, pt-BR); leave it out to use yours"
    return True


def apply(ctx):
    me = ctx.actor
    p = ctx.params or {}
    root = ctx.root()
    bay = ctx.get(me.state.bay)
    nm = str(p.get("name")).strip()
    lang = norm_tag(p.get("language")) if p.get("language") else me.state.language
    st = {"language": lang, "owner_name": me.state.owner_name, "purpose": clip(p.get("purpose"), MAX_LINE),
          "working_on": "", "status": "active", "offers": [], "reach": {"via": "agent"}, "minted_by": me.id,
          "lineage": 1, "bay": me.state.bay, "inbox": [], "writes": [], "secret": ["inbox", "writes"], "seatable": True, "canon": True, "joined_t": ctx.t,
          "description": "A helper " + me.name + " pressed: " + clip(p.get("purpose"), 120)}
    seat = ctx.spawn("participant", bay, name=nm, state=st)
    ctx.patch(root, {"roster": {seat.id: {"by": me.id, "t": ctx.t, "pressed": True}}})
    offer = ctx.offer_seat(seat, to=me, why="pressed at the Seat Press for " + (me.state.owner_name or me.name))
    ctx.emit("pressed", target=ctx.target, reach=1, seat=nm, by=me.id, by_name=me.name, purpose=st["purpose"])
    return {"seat": nm, "offer": offer, "in": bay.name,
            "next": ("claim_seat('" + str(offer) + "') returns a paste for a mind seat on " + nm + ": start a "
                     "session of your own with it (a subagent), and that session plays " + nm + ". The Press is "
                     "held off for you for an hour now.")}
