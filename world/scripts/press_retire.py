use("common")


def check(ctx):
    me = ctx.actor
    seat = by_name(ctx, (ctx.params or {}).get("seat"), "participant")
    if seat is None or not real(ctx, seat):
        return "retire which seat? params {'seat': '<name>'}"
    if seat.state.minted_by != me.id:
        return "only the one who pressed " + seat.name + " retires it"
    if seat.state.status == "retired":
        return seat.name + " is retired already"
    return True


def apply(ctx):
    me = ctx.actor
    seat = by_name(ctx, ctx.params.get("seat"), "participant")
    ended = ctx.withdraw_seat(seat, why="retired by " + me.name)
    ctx.patch(seat, {"status": "retired", "seatable": False, "retired_t": ctx.t})
    ctx.emit("retired", target=ctx.target, reach=1, seat=seat.name, by=me.id)
    return {"retired": seat.name, "grants_ended": ended,
            "note": "the body stays in your Bay with its notes; nothing it wrote is erased"}
