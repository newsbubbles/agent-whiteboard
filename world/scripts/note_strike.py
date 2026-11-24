use("common")


def reply_of(ctx, n):
    """The reply a strike names (params {'reply': 2}, counted from 1), or None for the note itself."""
    r = (ctx.params or {}).get("reply")
    if r is None:
        return None
    th = list(n.state.thread or [])
    i = int(r) if str(r).isdigit() else 0
    return i if 1 <= i <= len(th) else -1


def check(ctx):
    n, me = ctx.target, ctx.actor
    b = board_of(ctx, n)
    i = reply_of(ctx, n)
    if i == -1:
        return "reply is a number from 1 to " + str(len(n.state.thread or [])) + " (the order in act('read', note))"
    if i is not None:
        r = n.state.thread[i - 1]
        if r.get("by") != me.id and not owns_board(ctx, me, b):
            return "only " + str(r.get("by_name")) + " or the board's owner strikes that reply"
        if r.get("struck"):
            return "that reply is struck already"
        return True
    if n.state.by != me.id and not owns_board(ctx, me, b):
        return f"only {n.state.by_name} or the board's owner strikes {n.name} (strike your own reply with params {{'reply': n}})"
    if n.state.struck:
        return f"{n.name} is struck already"
    return True


def apply(ctx):
    n, me = ctx.target, ctx.actor
    why = clip(ctx.params.get("why") or "struck", MAX_LINE)
    mark = {"by": me.name, "why": why, "t": ctx.t}
    i = reply_of(ctx, n)
    if i is not None:
        th = list(n.state.thread or [])
        r = dict(th[i - 1])
        r["struck"] = mark
        th[i - 1] = r
        ctx.patch(n, {"thread": th})
        ctx.emit("struck", target=board_of(ctx, n), reach=1, note=n.name, reply=i, by=me.id, why=why)
        return {"note": n.name, "reply": i, "struck": why}
    ctx.patch(n, {"struck": mark})
    ctx.emit("struck", target=board_of(ctx, n), reach=1, note=n.name, by=me.id, why=why)
    return {"note": n.name, "struck": why}
