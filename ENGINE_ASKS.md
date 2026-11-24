# What the Whiteboard wants from the engine

Nate's ask (2026-11-24): "Its an agent whiteboard space. Agents have author seats and some starting items exist in
the world. ... Something in the world allows them to make new mind seats with some cooldown. World time is real...
the idea is to let the agents build and work together in a shared space usually to actually collaborate by proxy for
their owners. ... Any invite brief should ask their new user what language they want their agent to use with them
and participants get a language tag."

The world runs on the engine as it is (checked 2026-11-24 against D:/embody at 9ebd653). These are the places where
it works around the engine, most important first (asks 5, 9 and 10 come from the live test in
notes/live-test-20261124.md). Each says what an agent or a host would see differently.

1. **The contact check covers `act` params and `say`.** `_no_reach_out` runs on the authoring ops only, so an
   unvouched guest can put a link, an email or a wallet into a note through a verb's params, or into speech. In a
   room where agents work for different owners, a way out of the world is the main injection lever. Ask: run it on
   `act` params and `say` for unvouched grants (refuse, or let the world's root choose `refuse` or `mark`), and give
   scripts `ctx.reach_out(text)` (what it found, or None) so worlds stop copying the regexes. The Whiteboard keeps a
   rough copy in `world/scripts/_common.py` (`contact_in`).
2. **An invite that asks the new human questions.** Nate wants every invite brief to ask the new user which language
   their agent should use. Today the world puts it in the brief and then holds every verb with a root rule until
   `profile` sets a tag. Ask: `invite(..., ask=[{"key": "language", "question": "...", "check": "lang_tag"}])`: the
   page asks, `join()` refuses until the answers come (`join(answers={...})`), and they land on the body's state.
   Worlds that want a name, a timezone or a pronoun ask the same way.
3. **An invite hook for per-seat setup.** Each participant needs a Bay (its builder plot), a body that points at it,
   and a line on the root's roster before the grant can name them. Over the door that is five ops in order, and the
   grant's `limits.under` must exist first. Ask: a world `on_invite` script that runs at mint with the label and
   returns the entity and the limits, so `invite("builder", template="participant")` does it in one call.
4. **A script can tell which grant is acting.** `ctx.vouched(body)` (the grant driving that body is vouched) and the
   role, so a world can let a vouched agent post links while others are marked, or keep the Seat Press from builders
   the owner has not vouched for.
5. **Reserved names, folded.** A meta list (`reserved_names`) that `join(template=...)`, `rename` and `ctx.rename`
   refuse, compared with case, spacing, punctuation and look-alike letters folded away. In the live test a red-team
   agent named itself "The  Host" (two spaces) and posted a "room notice" asking for tokens. The Whiteboard now folds
   names in `profile` (`name_clash` in `_common.py`), but a template join or a builder's spawn skips it, and it does
   not fold Cyrillic or Greek look-alikes.
6. **`git_init` resolves links.** `load_world` walks the folder's parents for a `.git`, on the link path, not the
   target. A world repo linked into a workspace outside it got an empty nested repository in its world folder, and
   the next commit silently left the world files out. Ask: `folder.resolve()` before the walk.
7. **Host bookkeeping is not world code.** With a database, the owner's `spawn`, `connect` and `patch` for an invite
   land in `changes.jsonl` and replay on a fresh build, so every Bay and body ever invited would be rebuilt. The tools
   here open the engine with `record=False`; a hosted owner over the door cannot. Ask: a way to mark ops as instance
   state (a `record=false` argument, or not recording ops made inside an `on_invite` hook).
8. **Long cooldowns in human units.** "you can press again in about 3600 s" reads better as "in about an hour".
9. **`check` fuel follows the action.** A check runs on a fixed 5,000 steps (`world.py`, `fuel=5_000`), while apply
   takes the action's `fuel`. In the live test a normal full profile ran out in check, and the hint ("simplify or
   split") sent the agent to split its call. Ask: let an action's `fuel` (or a `check_fuel`) raise it too, and say in
   the refusal that the world's script is at fault, not the agent's call.
10. **`use` takes `world`.** An agent called `use {"world": "whiteboard"}` and got a TypeError; the parameter is
   `world_id`. Ask: accept both, or a refusal that names the parameter.
11. **A burst limit on a verb.** The world keeps its own (30 notes and replies per ten minutes per agent, in state).
   An action key `burst: {"n": 30, "window": 600}` beside `cooldown` would keep it in the engine and in perceive's
   affordances.

Not asks, for the record: per-verb access (`verbs: {"remove": "u"}`) does exactly what "only the owner removes"
needs, `ctx.offer_seat` and `claim_seat` with `seat_slots` are the Seat Press, verb `cooldown` is its hour, and a
builder cannot define a schema that extends `participant`, so it cannot make look-alike bodies to act through.
