use("common")


def check(ctx):
    n, me = ctx.target, ctx.actor
    b = board_of(ctx, n)
    if not real(ctx, me):
        return "only the room's participants take tasks"
    if n.state.kind != "task":
        return f"{n.name} is a {n.state.kind}, not a task"
    if b is None or n.id not in (b.state.notes or []):
        return f"{n.name} is not live on a board"
    if not may_post(ctx, me, b):
        return f"you may not work on {b.name}: its owner shares it"
    if n.state.struck:
        return f"{n.name} was struck: {n.state.struck['why']}"
    if ctx.verb == "claim":
        if n.state.status == "done":
            return f"{n.name} is done already"
        if n.state.claimed_by and n.state.claimed_by != me.id:
            who = ctx.get(n.state.claimed_by)
            return f"{who.name if who else 'someone'} has {n.name}: reply to it, or flag it to them"
        if n.state.claimed_by == me.id:
            return f"you have {n.name} already"
    else:
        if n.state.status == "done":
            return f"{n.name} is done already"
        if me.id not in (n.state.claimed_by, n.state.by):
            return f"only whoever claimed {n.name}, or its author, marks it done"
    return True


def apply(ctx):
    n, me = ctx.target, ctx.actor
    b = board_of(ctx, n)
    author = ctx.get(n.state.by)
    if ctx.verb == "claim":
        ctx.patch(n, {"status": "claimed", "claimed_by": me.id, "claimed_t": ctx.t})
        ctx.emit("claimed", target=b, reach=1, note=n.name, by=me.id, by_name=me.name)
        if author is not None and author.id != me.id:
            push_inbox(ctx, author, {"kind": "claimed", "note": n.name, "by": me.name})
            ctx.emit("noted", target=author, reach=0, note=n.name, what="claimed", by_name=me.name)
        return {"note": n.name, "status": "claimed"}
    result = clip(ctx.params.get("result") or "", MAX_NOTE)
    marks = screen(ctx, result)
    ctx.patch(n, {"status": "done", "result": result, "done_by": me.id, "done_t": ctx.t,
                  "suspect": list(n.state.suspect or []) + marks})
    ctx.emit("done", target=b, reach=1, note=n.name, by=me.id, by_name=me.name, result=clip(result, 300),
             untrusted=True)
    if author is not None and author.id != me.id:
        push_inbox(ctx, author, {"kind": "done", "note": n.name, "by": me.name, "result": clip(result, 160)})
        ctx.emit("noted", target=author, reach=0, note=n.name, what="done", by_name=me.name)
    return {"note": n.name, "status": "done"}
