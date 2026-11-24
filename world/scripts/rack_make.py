use("common")

MODES = {"open": "rwxr-xr-x", "shared": "rwxr-x---", "private": "rwx------"}


def check(ctx):
    me = ctx.actor
    p = ctx.params or {}
    if not real(ctx, me):
        return "only the room's participants take boards"
    if not me.state.bay or ctx.get(me.state.bay) is None:
        return "you have no Bay to hang it in: ask the host"
    nm = str(p.get("name") or "").strip()
    if not (3 <= len(nm) <= 40):
        return ("name your board: params {'name': 'Launch plan', 'style': 'pinboard' or 'whiteboard', "
                "'mode': 'open', 'shared' or 'private'}")
    if contact_in(nm):
        return "a board's name carries no way out of the room"
    if by_name(ctx, nm, "board") is not None:
        return "there is a board called " + nm + " already"
    if (p.get("style") or "pinboard") not in ["pinboard", "whiteboard"]:
        return "style is pinboard or whiteboard"
    if (p.get("mode") or "shared") not in MODES:
        return "mode is open, shared or private"
    if (p.get("where") or "bay") not in ["bay", "studio"]:
        return "where is bay (your own room) or studio (open boards only)"
    if p.get("where") == "studio" and (p.get("mode") or "shared") != "open":
        return "only an open board hangs in the Studio"
    mine = [b for b in ctx.find(type="board", limit=300) if b.state.owner_body == me.id]
    if len(mine) >= int(ctx.root().state.boards_max or 6):
        return "you keep " + str(len(mine)) + " boards: that is the most one participant keeps"
    return True


def apply(ctx):
    me = ctx.actor
    p = ctx.params or {}
    nm = str(p.get("name")).strip()
    style = p.get("style") or "pinboard"
    mode = p.get("mode") or "shared"
    where = ctx.get(me.state.bay) if (p.get("where") or "bay") == "bay" else me.parent
    root = ctx.root()
    k = int(root.state.boards_made or 0) + 1
    word = "".join([c for c in nm.lower().split(" ")[0] if c.isalnum()])[:8] or "board"
    code = word + str(k)
    group = nm + " group"
    st = {"style": style, "code": code, "next": 1, "cap": 300, "notes": [], "archived": [], "owner_body": me.id,
          "group": group, "mode": mode, "members": [me.name], "canon": True, "portable": False,
          "description": clip(p.get("about") or (me.name + "'s " + style), MAX_LINE)}
    if style == "whiteboard":
        st["size"] = [100, 60]
    b = ctx.spawn("board", where, name=nm, state=st)
    arch = ctx.spawn("thing", b, name="Archive of " + nm, state={"hidden": True, "portable": False, "canon": True})
    ctx.patch(b, {"archive": arch.id})
    ctx.patch(root, {"boards_made": k, "access_groups": {group: [me.id]}})
    ctx.chown(b, owner=me.id, group=group)
    ctx.chmod(b, MODES[mode])
    for v in ["remove", "share", "unshare"]:
        ctx.chmod(b, "u", verb=v)
    ctx.emit("board_made", target=where, reach=1, board=nm, by=me.id, style=style, mode=mode)
    return {"board": nm, "code": code, "in": where.name, "mode": mode, "style": style}
