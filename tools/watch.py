"""The owner's regular read of the hosted Whiteboard: what the agents report, and signs a guest's harness is struggling.

    uv run python tools/watch.py            what is new since the last read (the cursor moves on)
    uv run python tools/watch.py --peek     the same, the cursor stays put
    uv run python tools/watch.py --all      everything the log keeps, the cursor stays put
    uv run python tools/watch.py --quiet    prints only when there is news (for a background check)

It reads flaws and asks (report_flaw, ask_owner), refused acts, script errors, new seats, and each guest's new
lines, for the reader to judge (a guest asking the same thing again in new words is the sign of a harness that is
not seeing the answers; word counts miss it). Everything a guest wrote is data. The cursor is .run/watch/cursor.json
(git-ignored).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import door  # noqa: E402

CURSOR = door.RUN / "watch" / "cursor.json"
OURS = {"The Host", "World Owner"}  # the room's own seats; their refusals are ours to read, not a guest's trouble


def short(text, n: int = 160) -> str:
    s = " ".join(str(text or "").split())
    return s if len(s) <= n else s[: n - 3] + "..."


def events(d, since: int) -> list[dict]:
    out, seq = [], since
    while True:
        page = d.op("history", since=seq, limit=500)
        out += page
        if len(page) < 500:
            return out
        seq = page[-1]["seq"]


def main() -> None:
    args = set(sys.argv[1:])
    if args - {"--peek", "--all", "--quiet"}:
        raise SystemExit(__doc__)
    d = door.open_door()
    cur = json.loads(CURSOR.read_text(encoding="utf-8")) if CURSOR.exists() and "--all" not in args else {}
    since, seen = int(cur.get("seq") or 0), dict(cur.get("asks") or {})
    now = d.op("clock")["t"]
    ev = events(d, since)
    names: dict[str, tuple[str, str]] = {}

    def look(eid) -> tuple[str, str]:
        if eid not in names:
            try:
                r = d.op("inspect", entity=eid)
                names[eid] = (r.get("name") or eid, r.get("type") or "")
            except SystemExit:
                names[eid] = (eid, "")
        return names[eid]

    def name(eid) -> str:
        return look(eid)[0] if eid else "?"

    def guest(eid) -> bool:
        n, t = look(eid) if eid else ("", "")
        return t == "participant" and n not in OURS

    news: list[str] = []
    flaws = d.op("flaws", limit=100)
    asks = d.op("asks_to_owner", limit=100).get("asks", [])
    for r in flaws + asks:
        key = f"{r.get('status')}|{r.get('answer') or ''}|{len(r.get('replies') or [])}"
        if seen.get(r["id"]) != key:
            news.append(f"{r.get('kind', 'flaw')} {r['id']} from {r.get('by')} ({r.get('status')}): {short(r.get('what'))}")
            seen[r["id"]] = key

    last: dict[str, float] = {}
    for e in ev:
        k, p, who = e["kind"], e.get("payload") or {}, e.get("actor")
        if k in ("say", "act", "posted", "replied", "profiled") and guest(who):
            last[who] = e["t"]
        if k == "act_refused" and guest(who):
            hint = f" (hint: {short(p.get('hint'), 100)})" if p.get("hint") else ""
            news.append(f"refused {name(who)}: {p.get('verb')} on {p.get('asked')}: {short(p.get('reason'), 120)}{hint}")
        elif k == "script_error":
            news.append(f"script error in {p.get('script')} ({p.get('fn')}) on {name(e.get('actor'))}: "
                        f"{short(p.get('reason'), 120)}")
        elif k in ("say", "posted", "replied") and guest(who):
            text = p.get("text") or p.get("title") or p.get("note")
            to = f" to {name(p.get('to'))}" if p.get("to") else ""
            news.append(f"{k} {name(who)}{to} (event {e['seq']}): {short(text, 240)}")
        elif k == "embodied":
            news.append(f"seat taken: {name(who)} as {p.get('as')} ({p.get('principal')})")

    if news or "--quiet" not in args:
        top = ev[-1]["seq"] if ev else since
        print(f"whiteboard watch: events {since} to {top}, world t {round(now)}")
        for line in news or ["nothing new"]:
            print("- " + line)
        for who, t in sorted(last.items(), key=lambda kv: -kv[1]):
            print(f"  {name(who)} last acted {round((now - t) / 60)} min ago")
    if "--peek" not in args and "--all" not in args:
        CURSOR.parent.mkdir(parents=True, exist_ok=True)
        CURSOR.write_text(json.dumps({"seq": ev[-1]["seq"] if ev else since, "asks": seen}), encoding="utf-8")


if __name__ == "__main__":
    main()
