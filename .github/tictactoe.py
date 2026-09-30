#!/usr/bin/env python3
"""Tic-tac-toe for JanikDhadwar's profile README. Triggered by issues titled 'tictactoe|...'."""
import json, os, subprocess, urllib.parse

REPO = os.environ["REPO"]
ISSUE_NUMBER = os.environ["ISSUE_NUMBER"]
ISSUE_TITLE = os.environ["ISSUE_TITLE"]
TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN", "")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
STATE_PATH = os.path.join(ROOT, "tictactoe-state.json")
README_PATH = os.path.join(ROOT, "README.md")
START = "<!--TICTACTOE:START-->"
END = "<!--TICTACTOE:END-->"

WINS = [(0,1,2),(3,4,5),(6,7,8),(0,3,6),(1,4,7),(2,5,8),(0,4,8),(2,4,6)]

def blank_state(x=0, o=0, d=0):
    return {"board": [""]*9, "over": False, "winner": None,
            "x_wins": x, "o_wins": o, "draws": d}

def load_state():
    try:
        with open(STATE_PATH) as f:
            s = json.load(f)
        st = blank_state()
        if isinstance(s.get("board"), list) and len(s["board"]) == 9:
            st["board"] = [c if c in ("X","O") else "" for c in s["board"]]
        st["over"] = bool(s.get("over"))
        st["winner"] = s.get("winner") if s.get("winner") in ("X","O","draw") else None
        for k in ("x_wins","o_wins","draws"):
            if isinstance(s.get(k), int) and s[k] >= 0:
                st[k] = s[k]
        return st
    except (FileNotFoundError, json.JSONDecodeError, AttributeError):
        return blank_state()

def check_winner(b):
    for a,c,d in WINS:
        if b[a] and b[a] == b[c] == b[d]:
            return b[a]
    return None

def full(b):
    return all(b)

def computer_move(b):
    empty = [i for i,v in enumerate(b) if not v]
    for i in empty:
        t = b.copy(); t[i] = "O"
        if check_winner(t) == "O":
            return i
    for i in empty:
        t = b.copy(); t[i] = "X"
        if check_winner(t) == "X":
            return i
    if 4 in empty:
        return 4
    for i in (0,2,6,8):
        if i in empty:
            return i
    return empty[0]

def finish(state, result):
    state["over"] = True
    state["winner"] = result
    if result == "X":
        state["x_wins"] += 1
    elif result == "O":
        state["o_wins"] += 1
    else:
        state["draws"] += 1

def issue_url(title):
    return "https://github.com/" + REPO + "/issues/new?title=" + urllib.parse.quote(title, safe="")

def render(state):
    b = state["board"]
    tds = []
    for i,v in enumerate(b):
        if v == "X":
            inner = "❌"
        elif v == "O":
            inner = "⭕"
        elif state["over"]:
            inner = "⬜"
        else:
            inner = '<a href="%s">⬜</a>' % issue_url("tictactoe|move %d" % i)
        tds.append('<td align="center" width="70" height="70">%s</td>' % inner)
    rows = "".join("<tr>%s</tr>\n" % "".join(tds[r*3:r*3+3]) for r in range(3))
    table = "<table>\n%s</table>" % rows
    if state["over"]:
        w = state["winner"]
        status = {"X": "🏆 **You win!** Nicely played.",
                  "O": "🤖 **I win!** Better luck next time.",
                  "draw": "🤝 **Draw!**"}[w]
        status += ' <a href="%s"><b>↻ Play again</b></a>' % issue_url("tictactoe|new")
    elif not any(b):
        status = "You're ❌ and I'm ⭕ — **click a square to start!**"
    else:
        status = "Your move — you're ❌. **Click a square!**"
    stats = "<sub>📊 All-time — You: %d · Me: %d · Draws: %d</sub>" % (state["x_wins"], state["o_wins"], state["draws"])
    return "%s\n\n%s\n\n%s" % (status, table, stats)

def update_readme(html):
    with open(README_PATH) as f:
        content = f.read()
    if START not in content or END not in content:
        return False
    before, rest = content.split(START, 1)
    _, after = rest.split(END, 1)
    with open(README_PATH, "w") as f:
        f.write(before + START + "\n" + html + "\n" + END + after)
    return True

def main():
    cmd = ISSUE_TITLE[len("tictactoe|"):].strip().lower() if ISSUE_TITLE.startswith("tictactoe|") else ""
    state = load_state()
    note = "Move recorded."
    if cmd == "new":
        state = blank_state(state["x_wins"], state["o_wins"], state["draws"])
        note = "New game started — you're ❌."
    elif cmd.startswith("move"):
        try:
            cell = int(cmd.split()[1])
        except (IndexError, ValueError):
            cell = -1
        if state["over"]:
            note = "That game's over — hit ↻ Play again for a fresh board."
        elif not 0 <= cell <= 8 or state["board"][cell]:
            note = "Illegal move — that square is taken."
        else:
            state["board"][cell] = "X"
            if check_winner(state["board"]) == "X":
                finish(state, "X"); note = "You won! 🏆"
            elif full(state["board"]):
                finish(state, "draw"); note = "It's a draw! 🤝"
            else:
                state["board"][computer_move(state["board"])] = "O"
                if check_winner(state["board"]) == "O":
                    finish(state, "O"); note = "I win! 🤖"
                elif full(state["board"]):
                    finish(state, "draw"); note = "It's a draw! 🤝"
                else:
                    note = "Move played — your turn."
    else:
        note = "Unknown command."

    with open(STATE_PATH, "w") as f:
        json.dump(state, f)
    ok = update_readme(render(state))
    subprocess.run(["git","config","user.name","github-actions[bot]"], cwd=ROOT, check=False)
    subprocess.run(["git","config","user.email","github-actions[bot]@users.noreply.github.com"], cwd=ROOT, check=False)
    subprocess.run(["git","add","tictactoe-state.json","README.md"], cwd=ROOT, check=False)
    if subprocess.run(["git","diff","--cached","--quiet"], cwd=ROOT).returncode != 0:
        subprocess.run(["git","commit","-m","Tic-tac-toe: " + note], cwd=ROOT, check=False)
        subprocess.run(["git","push"], cwd=ROOT, check=False)
    env = dict(os.environ)
    if TOKEN:
        env["GH_TOKEN"] = TOKEN
    subprocess.run(["gh","issue","close",ISSUE_NUMBER,"--repo",REPO,
                    "--comment", note + (" The board is updated ✓" if ok else "")],
                   env=env, check=False, capture_output=True)

if __name__ == "__main__":
    main()
