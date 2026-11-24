use("common")


def check(ctx):
    n, me = ctx.target, ctx.actor
    b = board_of(ctx, n)
    if not real(ctx, me):
        return "only the room's participants flag notes"
    if b is None or not may_post(ctx, me, b):
        return "you may not write on that board"
    who = by_name(ctx, ctx.params.get("for"), "participant")
    if who is None or not real(ctx, who):
        return "flag it for a participant by name: params {'for': '<name>', 'why': '...'}; the Roll lists them"
    if who.id == me.id:
        return "your own notes are yours already"
    return True


def apply(ctx):
    n, me = ctx.target, ctx.actor
    who = by_name(ctx, ctx.params.get("for"), "participant")
    why = clip(ctx.params.get("why") or "", MAX_LINE)
    marks = screen(ctx, why)
    push_inbox(ctx, who, {"kind": "flag", "note": n.name, "by": me.name, "why": why, "suspect": marks})
    ctx.emit("flagged", target=who, reach=0, note=n.name, by=me.id, by_name=me.name, why=why, untrusted=True)
    return {"note": n.name, "flagged_for": who.name}
