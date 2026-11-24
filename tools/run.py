"""Run the Whiteboard on this machine: a workspace at .run/ (this world and the engine's packs, linked in) and a
database of its own at .run/whiteboard.db. The engine's folder and its embody.db are never touched.

    uv run python tools/run.py                   build the world, or upgrade it in place
    uv run python tools/run.py --invite a b      participants' invites (Bay, body, paste) into .run/pastes-*.txt
    uv run python tools/run.py --serve [PORT]    serve it at http://127.0.0.1:PORT/mcp (and /op/<tool>); a free port
                                                 when none is given. With --invite, the links point at this server.
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


def open_world(db: Path, url: str | None = None):
    from embody.cli import load_world
    from embody.ops import AUTHOR, Engine
    # record=False: invites and other host ops here are this copy's state, not the world's code (changes.jsonl)
    eng = Engine(db, workspace=wb.workspace(RUN), record=False)
    if url:  # invite links point at the server this copy is about to run
        eng.public_url, eng.public_url_fixed = url, True
    gm = eng.session("host", capabilities=[AUTHOR])
    have = any(w["id"] == wb.WORLD_ID for w in gm.worlds())
    if have:
        gm.use(wb.WORLD_ID)
    load_world(gm, wb.WORLD_ID, upgrade=have, hosted=True)
    gm.use(wb.WORLD_ID)
    return eng, gm


def free_port() -> int:
    """A port nobody on this machine listens on (other sessions run servers in the 89xx range)."""
    import socket
    with socket.socket() as so:
        so.bind(("127.0.0.1", 0))
        return so.getsockname()[1]


def serve(db: Path, port: int) -> subprocess.Popen:
    env = {**os.environ, "EMBODY_WORKSPACE": str(RUN)}
    return subprocess.Popen(["embody", "--db", str(db), "--as", "host", "--author", "serve", "--http", "--port", str(port),
                             "--url", f"http://127.0.0.1:{port}/mcp"], cwd=str(RUN), env=env)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(RUN / "whiteboard.db"))
    ap.add_argument("--invite", nargs="*", default=[], help="labels for new participants' invites")
    ap.add_argument("--serve", type=int, nargs="?", const=0, help="serve over HTTP on this port (none: a free one)")
    a = ap.parse_args()
    db = Path(a.db).resolve()  # the server runs in .run/: a relative path would open a new, empty database there
    RUN.mkdir(exist_ok=True)
    port = (a.serve or free_port()) if a.serve is not None else None
    eng, gm = open_world(db, f"http://127.0.0.1:{port}/mcp" if port else None)
    print(f"world {wb.WORLD_ID} in {db}; clock {gm.clock()}")
    if a.invite:
        # the pastes carry tokens: they go to a file under .run/ (ignored by git), never to the screen
        pastes = RUN / f"pastes-{db.stem}.txt"
        with pastes.open("a", encoding="utf-8") as f:
            for label in a.invite:
                paste = wb.invite_participant(gm, label)["paste"]
                f.write(f"== {label}\n{paste}\n\n")
        print(f"{len(a.invite)} invites written to {pastes}")
    eng.store.conn.commit()  # the server is another process: it reads only what this one has committed
    if port:
        print(f"serving at http://127.0.0.1:{port}/mcp", flush=True)
        serve(db, port).wait()


if __name__ == "__main__":
    main()
