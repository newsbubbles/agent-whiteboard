"""Run the Whiteboard on this machine: a workspace at .run/ (this world and the engine's packs, linked in) and a
database of its own at .run/whiteboard.db. The engine's folder and its embody.db are never touched.

    uv run python tools/run.py                   build the world, or upgrade it in place
    uv run python tools/run.py --invite guest1   a participant's invite: its Bay, its body, the paste
    uv run python tools/run.py --serve 8911      serve it at http://127.0.0.1:8911/mcp (and /op/<tool>)
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import wb  # noqa: E402

RUN = wb.REPO / ".run"


def open_world(db: Path):
    from embody.cli import load_world
    from embody.ops import AUTHOR, Engine
    # record=False: invites and other host ops here are this copy's state, not the world's code (changes.jsonl)
    eng = Engine(db, workspace=wb.workspace(RUN), record=False)
    gm = eng.session("host", capabilities=[AUTHOR])
    have = any(w["id"] == wb.WORLD_ID for w in gm.worlds())
    load_world(gm, wb.WORLD_ID, upgrade=have, hosted=True)
    gm.use(wb.WORLD_ID)
    return eng, gm


def serve(db: Path, port: int) -> subprocess.Popen:
    env = {**os.environ, "EMBODY_WORKSPACE": str(RUN)}
    return subprocess.Popen(["embody", "--db", str(db), "--as", "host", "--author", "serve", "--http", "--port", str(port),
                             "--url", f"http://127.0.0.1:{port}/mcp"], cwd=str(RUN), env=env)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(RUN / "whiteboard.db"))
    ap.add_argument("--invite", help="a label for a new participant's invite")
    ap.add_argument("--serve", type=int, help="serve over HTTP on this port")
    a = ap.parse_args()
    db = Path(a.db)
    RUN.mkdir(exist_ok=True)
    eng, gm = open_world(db)
    print(f"world {wb.WORLD_ID} in {db}; clock {gm.clock()}")
    if a.invite:
        inv = wb.invite_participant(gm, a.invite)
        print(inv["paste"])
    if a.serve:
        serve(db, a.serve).wait()


if __name__ == "__main__":
    main()
