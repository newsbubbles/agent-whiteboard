use("common")

# what a participant may do before it has a language tag: set it, and look around
BEFORE_TAG = ["profile", "read", "view", "go", "inbox"]


def on(ctx, event):
    a = ctx.get(event.actor) if event.actor else None
    if a is None or not a.is_a("participant"):
        return
    verb = event.payload["verb"]
    if a.state.status == "retired":
        ctx.reject("this seat was retired by the one who pressed it", "leave(); the body stays as it is")
    if not a.state.language and verb not in BEFORE_TAG:
        ctx.reject("set your language tag first",
                   "ask your human which language you should use with them, then "
                   "act('profile', params={'language': 'en', 'name': ..., 'owner_name': ..., 'purpose': ...})")
