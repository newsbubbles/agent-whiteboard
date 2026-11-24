"""The owner's script review on the hosted Whiteboard, in two steps so nothing is approved unread.

    uv run python tools/review.py pending                  what waits for review, with version and author
    uv run python tools/review.py fetch <id> [<id> ...]    saves each script to .run/review/<id>-v<n>.py to read
    uv run python tools/review.py approve <id> [<id> ...]  approves each only if it still matches the saved copy
    uv run python tools/review.py refuse <id> [<id> ...]   refuses one (the version before comes back, or none)
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import door  # noqa: E402

SAVED = door.RUN / "review"


def source(d, sid: str) -> str:
    s = d.op("script_source", id=sid)
    return s.get("source") if isinstance(s, dict) else s


def scripts(d) -> dict:
    return {s["id"]: s for s in d.op("scripts", limit=200)}


def main() -> None:
    if len(sys.argv) < 2 or sys.argv[1] not in ("pending", "fetch", "approve", "refuse"):
        raise SystemExit(__doc__)
    cmd, ids = sys.argv[1], sys.argv[2:]
    d = door.open_door()
    meta = scripts(d)
    SAVED.mkdir(parents=True, exist_ok=True)
    for sid in ids:
        if sid not in meta:
            print(f"{sid}: no such script")
            continue
        v = meta[sid]["version"]
        path = SAVED / f"{sid}-v{v}.py"
        if cmd == "fetch":
            path.write_text(source(d, sid), encoding="utf-8")
            print(f"{sid} v{v} by {meta[sid].get('by')}: saved {path}")
        elif cmd == "approve":
            if not path.exists() or path.read_text(encoding="utf-8") != source(d, sid):
                print(f"{sid} v{v}: changed since it was fetched, or never fetched; not approved")
                continue
            d.op("review_script", id=sid, approve=True)
            print(f"{sid} v{v}: approved")
        elif cmd == "refuse":
            d.op("review_script", id=sid, approve=False)
            print(f"{sid} v{v}: refused")
    left = [(k, m["version"], m.get("by")) for k, m in scripts(d).items() if m.get("pending")]
    print("pending:", left or "none")


if __name__ == "__main__":
    main()
