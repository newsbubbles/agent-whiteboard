use("common")


def check(ctx):
    n, me = ctx.target, ctx.actor
    b = board_of(ctx, n)
    if b is None or not may_post(ctx, me, b):
        return "you may not write on that board"
    other = note_on(ctx, b, ctx.params.get("to"))
    if other is None or other.id == n.id:
        return "link to another live note on the same board: params {'to': '<note>', 'label': '...'}"
    if len(n.state.links or []) >= 20:
        return f"{n.name} has 20 arrows already"
    return True


def apply(ctx):
    n, me = ctx.target, ctx.actor
    b = board_of(ctx, n)
    other = note_on(ctx, b, ctx.params.get("to"))
    label = clip(ctx.params.get("label") or "", 60)
    ctx.patch(n, {"links": list(n.state.links or []) + [{"to": other.name, "label": label, "by": me.name}]})
    ctx.emit("linked_notes", target=b, reach=1, note=n.name, to=other.name, label=label, by=me.id)
    return {"from": n.name, "to": other.name, "label": label}
