use("common")


def check(ctx):
    n, me = ctx.target, ctx.actor
    b = board_of(ctx, n)
    if b is None or b.state.style != "whiteboard":
        return "only notes on a whiteboard have a spot"
    if n.state.by != me.id and not owns_board(ctx, me, b):
        return f"only {n.state.by_name} or the board's owner moves {n.name}"
    at = ctx.params.get("at")
    if not (isinstance(at, list) and len(at) == 2 and all((isinstance(v, int) or isinstance(v, float)) for v in at)):
        return "params {'at': [x, y]}"
    w, h = b.state.size or [100, 60]
    if not (0 <= at[0] <= w and 0 <= at[1] <= h):
        return f"{b.name} is {w} by {h}"
    return True


def apply(ctx):
    n = ctx.target
    ctx.patch(n, {"at": ctx.params.get("at")})
    ctx.emit("placed", target=board_of(ctx, n), reach=1, note=n.name, at=ctx.params.get("at"), by=ctx.actor.id)
    return {"note": n.name, "at": ctx.params.get("at")}
