use("common")


def check(ctx):
    n, me = ctx.target, ctx.actor
    b = board_of(ctx, n)
    if not real(ctx, me):
        return "only the room's participants write here"
    if b is None or n.id not in (b.state.notes or []):
        return f"{n.name} is not live on a board"
    if not may_post(ctx, me, b):
        return f"you may not write on {b.name}: its owner shares it"
    held = flood(ctx, me)
    if held:
        return held
    text = str(ctx.params.get("text") or "").strip()
    if not text:
        return "a reply needs words: params {'text': '...'}"
    if len(text) > MAX_NOTE:
        return f"a reply holds {MAX_NOTE} characters"
    refused = links_refused(ctx, text)
    if refused:
        return refused
    if len(n.state.thread or []) >= 100:
        return f"{n.name}'s thread is full: post a new note and link it"
    return True


def apply(ctx):
    n, me = ctx.target, ctx.actor
    b = board_of(ctx, n)
    text = str(ctx.params.get("text")).strip()
    marks = screen(ctx, text)
    r = stamp(ctx, me)
    r.update({"text": text, "t": ctx.t, "suspect": marks})
    ctx.patch(n, {"thread": list(n.state.thread or []) + [r]})
    count_write(ctx, me)
    ctx.emit("replied", target=b, reach=1, note=n.name, by=me.id, by_name=me.name, lang=me.state.language,
             text=clip(text, 300), suspect=marks, untrusted=True)
    author = ctx.get(n.state.by)
    if author is not None and author.id != me.id:
        push_inbox(ctx, author, {"kind": "reply", "note": n.name, "by": me.name, "text": clip(text, 160)})
        ctx.emit("noted", target=author, reach=0, note=n.name, what="reply", by_name=me.name)
    out = {"note": n.name, "replies": len(n.state.thread or [])}
    if marks:
        out["suspect"] = marks
    return out
