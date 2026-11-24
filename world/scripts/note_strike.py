use("common")


def check(ctx):
    n, me = ctx.target, ctx.actor
    b = board_of(ctx, n)
    if n.state.by != me.id and not owns_board(ctx, me, b):
        return f"only {n.state.by_name} or the board's owner strikes {n.name}"
    if n.state.struck:
        return f"{n.name} is struck already"
    return True


def apply(ctx):
    n, me = ctx.target, ctx.actor
    why = clip(ctx.params.get("why") or "struck", MAX_LINE)
    ctx.patch(n, {"struck": {"by": me.name, "why": why, "t": ctx.t}})
    ctx.emit("struck", target=board_of(ctx, n), reach=1, note=n.name, by=me.id, why=why)
    return {"note": n.name, "struck": why}
