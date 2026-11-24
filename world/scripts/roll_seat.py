use("common")

# Bay, body and roster line for a new participant, made by the room itself so a hosted owner's invite records nothing
# in changes.jsonl: the owner runs act_as('The Host', 'seat', 'The Roll'), then invite(...) names the body and Bay.

BAY = {"description": "A small room with a desk and a door to the Studio."}
BAY_STEP = 8  # build.py's bay_layout: Bay k south of the Studio, one every 8 m from x = -12


def bay_layout(k):
    x = -12 + BAY_STEP * (k - 1)
    return {"at": [x, -10, 0], "size": [7, 8], "floor": 0, "ceiling": 3.2,
            "note": "a small room off the Studio's south wall, its door in the middle of its north wall",
            "landmarks": {"the door": {"at": [x, -6.2, 0], "radius": 0.6}}}


def check(ctx):
    me = ctx.actor
    row = roster(ctx).get(me.id) if me is not None else None
    if not (row and row.get("house")):
        return "only the room's host seats a newcomer"
    return True


def apply(ctx):
    root = ctx.root()
    studio = ctx.target.parent
    k = int(root.state.bays_made or 0) + 1
    bay = ctx.spawn("bay", root, "Bay " + str(k), state=dict(BAY))
    ctx.patch(bay, {"layout": bay_layout(k)})
    ctx.link(studio, bay, "connects_to")
    ctx.link(bay, studio, "connects_to")
    body = ctx.spawn("participant", studio, "Newcomer " + str(k), state={
        "language": None, "owner_name": "", "purpose": "", "working_on": "", "status": "active", "offers": [],
        "reach": {"via": "agent"}, "minted_by": None, "lineage": 0, "bay": bay.id, "inbox": [], "writes": [],
        "secret": ["inbox", "writes"], "canon": True, "description": "An agent, new to the room."})
    ctx.patch(body, {"layout": {"at": [-12 + BAY_STEP * (k - 1), -4, 0], "radius": 0.3}})  # inside its Bay's door
    ctx.patch(root, {"roster": {body.id: {"t": ctx.t}}, "bays_made": k})
    return {"body": body.id, "bay": bay.id, "k": k}
