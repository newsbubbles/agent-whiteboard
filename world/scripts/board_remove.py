use("common")


def check(ctx):
    b, me = ctx.target, ctx.actor
    if not owns_board(ctx, me, b):
        return f"only {b.name}'s owner removes notes from it: strike your own note instead, or flag it to the owner"
    n = note_on(ctx, b, ctx.params.get("note"))
    if n is None:
        return f"no live note {ctx.params.get('note')!r} on {b.name}: view() lists them"
    return True


def apply(ctx):
    b, me = ctx.target, ctx.actor
    n = note_on(ctx, b, ctx.params.get("note"))
    why = clip(ctx.params.get("why") or "", MAX_LINE)
    arch = ctx.get(b.state.archive) if b.state.archive else None
    if arch is None:
        arch = ctx.spawn("thing", b, name=f"Archive of {b.name}", state={"hidden": True, "portable": False, "canon": True})
        ctx.patch(b, {"archive": arch.id})
    ctx.move(n, arch)
    ctx.patch(n, {"removed_by": me.id, "removed_t": ctx.t, "removed_why": why})
    ctx.patch(b, {"notes": [i for i in (b.state.notes or []) if i != n.id],
                  "archived": list(b.state.archived or []) + [n.id]})
    ctx.emit("removed", target=b, reach=1, note=n.name, by=me.id, why=why)
    return {"removed": n.name, "kept_in": arch.name}
