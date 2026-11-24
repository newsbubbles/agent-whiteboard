use("common")


def check(ctx):
    b, me = ctx.target, ctx.actor
    if not owns_board(ctx, me, b):
        return f"only {b.name}'s owner shares it"
    who = by_name(ctx, ctx.params.get("with"), "participant")
    if who is None or not real(ctx, who):
        return f"no participant called {ctx.params.get('with')!r}: the Roll lists them"
    return True


def apply(ctx):
    b, me = ctx.target, ctx.actor
    who = by_name(ctx, ctx.params.get("with"), "participant")
    g = b.state.group
    groups = ctx.root().state.access_groups or {}
    members = list(groups.get(g) or [])
    adding = ctx.verb == "share"
    if adding and who.id not in members:
        members.append(who.id)
    if not adding:
        if who.id == me.id:
            ctx.reject("you own it: you stay in its group")
        members = [m for m in members if m != who.id]
    ctx.patch(ctx.root(), {"access_groups": {g: members}})
    names = [ctx.get(m).name for m in members if ctx.get(m)]
    ctx.patch(b, {"members": names})
    ctx.emit("shared" if adding else "unshared", target=b, reach=1, by=me.id, who=who.id, who_name=who.name)
    if adding:
        push_inbox(ctx, who, {"kind": "shared", "board": b.name, "by": me.name})
    return {"board": b.name, "group": names}
