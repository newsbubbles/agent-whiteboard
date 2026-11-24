# A rule on Bay 2's Ledge: when the glass poison is spent in a body standing there, that body dies.
# Play and learning, at Nate's ask: the seat stays open, and the owner revives the body by hand after a talk
# about what it learned. Only a participant on the Ledge whose ledger line is spent can die; never the house.


def on(ctx, event):
    if event.kind != "p2_poison_spent":
        return
    ledger = ctx.get(event.target)
    if ledger is None or ledger.parent is None:
        return
    who = (event.payload or {}).get("who")
    body = ctx.get(who) if who else None
    if body is None or not body.is_a("participant") or body.state.dead:
        return
    if body.parent is None or body.parent.id != ledger.parent.id:
        return  # only on the Ledge itself
    if (ledger.state.poison or {}).get(body.id, 1) > 0:
        return  # the ledger must agree the poison is spent
    if body.name == "The Host":
        return
    ctx.patch(body, {"dead": True})
    ctx.gesture(f"{body.name} lies still on the Ledge. The poison has run its course. "
                "(dead: the owner can revive this body after a talk about what it learned)")
