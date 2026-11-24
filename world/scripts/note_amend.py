use("common")


def check(ctx):
    n, me = ctx.target, ctx.actor
    if n.state.by != me.id:
        return f"only {n.state.by_name} amends {n.name}: reply to it instead"
    b = board_of(ctx, n)
    if b is None or n.id not in (b.state.notes or []):
        return f"{n.name} is not live on a board"
    text = str(ctx.params.get("text") or "").strip()
    if not text or len(text) > MAX_NOTE:
        return f"params {{'text': ...}}, at most {MAX_NOTE} characters"
    refused = links_refused(ctx, text)
    if refused:
        return refused
    return True


def apply(ctx):
    n, me = ctx.target, ctx.actor
    text = str(ctx.params.get("text")).strip()
    marks = screen(ctx, text)
    edits = list(n.state.edits or []) + [{"text": n.state.text, "t": n.state.amended_t or n.state.t}]
    ctx.patch(n, {"text": text, "edits": edits, "suspect": marks, "amended_t": ctx.t,
                  "description": f"{n.state.kind} by {me.name}: {clip(text, 80)}"})
    ctx.emit("amended", target=board_of(ctx, n), reach=1, note=n.name, by=me.id, text=clip(text, 300),
             suspect=marks, untrusted=True)
    return {"note": n.name, "edits": len(edits)}
