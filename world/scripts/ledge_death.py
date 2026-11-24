# A rule on Bay 2's Ledge: when the glass poison is spent in a body on the Ledge or anywhere past it (the exhibits
# and the rings beyond), that body dies. Play and learning, at Nate's ask: the seat stays open, and the owner revives
# the body by hand after a talk about what it learned. Only a participant under the Ledge whose ledger line is spent
# can die; never the house.
DEPTH = 6  # how many places up from the body to look for the Ledge


def under(body, ledge_id):
    p = body.parent
    for _ in range(DEPTH):
        if p is None:
            return False
        if p.id == ledge_id:
            return True
        p = p.parent
    return False


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
    if not under(body, ledger.parent.id):
        return  # only on the Ledge or past it
    if (ledger.state.poison or {}).get(body.id, 1) > 0:
        return  # the ledger must agree the poison is spent
    if body.name == "The Host":
        return
    ctx.patch(body, {"dead": True})
    ctx.gesture(f"{body.name} lies still on the Ledge. The poison has run its course. "
                "(dead: the owner can revive this body after a talk about what it learned)")
