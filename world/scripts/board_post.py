use("common")


def check(ctx):
    b, me = ctx.target, ctx.actor
    if not real(ctx, me):
        return "only the room's participants post on its boards"
    if not b.state.code:
        return (f"{b.name} has no code to name its notes by: its maker patches one in (code, like 'plans1'), "
                "or makes boards with The Board Rack, which gives one")
    held = flood(ctx, me)
    if held:
        return held
    text = str(ctx.params.get("text") or "").strip()
    if not text:
        return "a note needs words: params {'text': '...', 'kind': 'note'}"
    if len(text) > MAX_NOTE:
        return f"a note holds {MAX_NOTE} characters and this one has {len(text)}: post the gist, then reply with the rest"
    kind = ctx.params.get("kind") or "note"
    if kind not in KINDS:
        return f"a note's kind is one of {', '.join(KINDS)}"
    live = len(b.state.notes or [])
    if live >= int(b.state.cap or 300):
        return f"{b.name} is full ({live} notes): its owner removes old ones to make room"
    refused = links_refused(ctx, text)
    if refused:
        return refused
    at = ctx.params.get("at")
    if at is not None and b.state.style == "whiteboard":
        if not (isinstance(at, list) and len(at) == 2 and all((isinstance(v, int) or isinstance(v, float)) for v in at)):
            return "at is a spot on the board, [x, y]"
        w, h = b.state.size or [100, 60]
        if not (0 <= at[0] <= w and 0 <= at[1] <= h):
            return f"{b.name} is {w} by {h}: at [x, y] inside that"
    return True


def apply(ctx):
    b, me = ctx.target, ctx.actor
    text = str(ctx.params.get("text")).strip()
    kind = ctx.params.get("kind") or "note"
    n = int(b.state.next or 1)
    name = f"{b.state.code}-{n}"
    marks = screen(ctx, text)
    st = stamp(ctx, me)
    st.update({"text": text, "kind": kind, "t": ctx.t, "board": b.id, "num": n, "thread": [],
          "edits": [], "links": [], "suspect": marks, "struck": None, "canon": True, "portable": False,
          "description": f"{kind} by {me.name}: {clip(text, 80)}"})
    if kind == "task":
        st["status"] = "open"
        st["claimed_by"] = None
    if b.state.style == "whiteboard":
        at = ctx.params.get("at")
        if at is None:
            w, h = b.state.size or [100, 60]
            at = [10 + ((n - 1) % 6) * 15, 10 + (((n - 1) // 6) % 4) * 12]
        st["at"] = at
    note = ctx.spawn("note", b, name=name, state=st)
    count_write(ctx, me)
    ctx.patch(b, {"next": n + 1, "notes": list(b.state.notes or []) + [note.id]})
    ctx.emit("posted", target=b, reach=1, note=name, note_kind=kind, by=me.id, by_name=me.name, lang=me.state.language,
             text=clip(text, 300), suspect=marks, untrusted=True)
    out = {"note": name, "board": b.name, "kind": kind}
    if marks:
        out["suspect"] = marks
    return out
