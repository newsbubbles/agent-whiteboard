"""The owner's hands on a hosted Whiteboard, over its HTTP door (POST <base>/op/<tool>, Bearer). The owner's paste
lives in a file that git ignores (default .run/hosted-owner.txt); its token is read from there and never printed.

    uv run python tools/door.py check                      who the owner grant is, the world, the clock
    uv run python tools/door.py invite <label> [--role R]  a Bay, a body, the roster line and a grant; the paste
                                                           goes to .run/invites/<label>.txt, never to the screen

Labels are neutral (guest-1, guest-2): a guest's label is its principal, and the host's hands read principals.
Who a label is stays with Nate.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import wb  # noqa: E402

RUN = wb.REPO / ".run"
OWNER = RUN / "hosted-owner.txt"


class Door:
    def __init__(self, paste: str):
        tok = re.search(r"Bearer ([A-Za-z0-9_-]{20,})", paste)
        url = re.search(r"(https?://[^\s\"'<>]+?)/mcp", paste)
        if not (tok and url):
            raise SystemExit("the owner file needs the server's /mcp address and its Bearer token")
        self.base, self.token = url.group(1), tok.group(1)

    def op(self, tool: str, **kw):
        req = urllib.request.Request(f"{self.base}/op/{tool}", data=json.dumps(kw).encode(), method="POST",
                                     headers={"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                out = json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            out = json.loads(e.read().decode() or "{}")
        if isinstance(out, dict) and out.get("ok") is False:
            raise SystemExit(f"{tool} refused: {out.get('reason')} ({out.get('hint')})")
        return out.get("result", out) if isinstance(out, dict) else out


def resolve(paste: str) -> str:
    """An invite paste carries a link (/i/<code>) whose page holds the token; read the page and keep the server's
    /mcp address with the token, the form Door takes. A paste already in that form is returned as it is."""
    if re.search(r"Bearer [A-Za-z0-9_-]{20,}", paste):
        return paste
    m = re.search(r"(https?://[^\s\"'<>]+?)/i/[A-Za-z0-9_-]+", paste)
    if not m:
        raise SystemExit("no invite link in the owner file")
    page = urllib.request.urlopen(m.group(0), timeout=30).read().decode()
    tok = re.search(r"Bearer ([A-Za-z0-9_-]{20,})", page)
    if not tok:
        raise SystemExit("the invite page carries no token (spent, or more than a day old): ask for a fresh one")
    return f"{m.group(1)}/mcp Bearer {tok.group(1)}\n"


def open_door(path: Path = OWNER) -> Door:
    raw = path.read_text(encoding="utf-8")
    keys = resolve(raw)
    if keys != raw:
        path.write_text(keys, encoding="utf-8")  # the link lasts a day; the grant does not expire
    d = Door(keys)
    d.op("use", world_id=wb.WORLD_ID)
    return d


def invite(d: Door, label: str, role: str = wb.ROLE) -> dict:
    """The same two ops as wb.invite_participant: the Roll's seat verb (world code, never in changes.jsonl), then the
    grant, limited to the Bay the verb made."""
    seat = d.op("act_as", entity="The Host", verb="seat", target="The Roll")
    seat = seat.get("result", seat)
    inv = d.op("invite", role=role, entity=seat["body"], label=label, brief=wb.BRIEF,
               limits=wb.limits(seat["bay"], seat["k"]))
    return {**inv, "body": seat["body"], "bay": seat["bay"]}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["check", "invite"])
    ap.add_argument("label", nargs="?")
    ap.add_argument("--role", default=wb.ROLE)
    ap.add_argument("--owner", default=str(OWNER))
    a = ap.parse_args()
    d = open_door(Path(a.owner))
    if a.cmd == "check":
        s = d.op("summary")
        print(f"door {d.base}: world {s.get('world') or wb.WORLD_ID}, root {s.get('root')}, clock {d.op('clock')}")
        return
    if not a.label or not re.fullmatch(r"[a-z0-9-]{3,30}", a.label):
        raise SystemExit("a neutral label: guest-1, guest-2 (lowercase, digits, dashes)")
    inv = invite(d, a.label, a.role)
    out = RUN / "invites" / f"{a.label}.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(inv["paste"] + "\n", encoding="utf-8")
    print(f"{a.role} invite for {a.label}: body {inv['body']}, bay {inv['bay']}; paste in {out}")


if __name__ == "__main__":
    main()
