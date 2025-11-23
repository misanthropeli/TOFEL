import json
from datetime import datetime

def make_progress_bar(percent):
    total_blocks = 20
    filled = int(percent / 5)
    return "[" + ("#" * filled) + ("-" * (total_blocks - filled)) + f"] {percent}%"

# Load progress data
with open("progress.json", "r", encoding="utf-8") as f:
    data = json.load(f)

target_date = datetime.strptime(data["target_date"], "%Y-%m-%d")
today = datetime.now()
days_left = (target_date - today).days

progress_bar = make_progress_bar(data["progress"])

# Daily tasks
daily = data["daily"]
def checkbox(done): return "[x]" if done else "[ ]"

# Generate README
readme = f"""
<div align="center">

<h2 style="font-family: monospace; color: #0052CC;">{progress_bar}</h2>

<h1 style="font-size: 80px; color: #333; margin: 10px 0;">{days_left} Days</h1>

<img src="https://capsule-render.vercel.app/api?type=waving&color=0:0052CC,100:009688&height=180&section=header&text=PhD%20Candidate%202027&fontSize=50&fontColor=ffffff" width="100%" alt="Header" />

<p>
<img src="https://img.shields.io/badge/TARGET-TOEFL_100%2B-0052CC?style=for-the-badge&logo=target&logoColor=white" />
<img src="https://img.shields.io/badge/MAJOR-CHEMICAL_ENG-009688?style=for-the-badge&logo=atom&logoColor=white" />
<img src="https://img.shields.io/badge/STATUS-HIGH_PRESSURE-FF5722?style=for-the-badge&logo=fire&logoColor=white" />
</p>

</div>

---

# 📅 {today.strftime("%Y-%m-%d")} (Today)

- {checkbox(daily["vocab"])} **Vocab**: 100 new + 150 review
- {checkbox(daily["listening"])} **Listening**: 3× SSS
- {checkbox(daily["reading"])} **Reading**: 5 long sentences
- {checkbox(daily["speaking"])} **Speaking**: Task 1 (3 takes)

---

# 🗺️ Strategic Master Plan

| Phase | Timeline | Core Mission | Status |
|-------|----------|--------------|--------|
| **Phase 1: Input** | Now - 12.20 | Vocab + SSS | 🟢 Active |
| **Phase 2: Attack** | 12.21 - 01.31 | TPO 50-70 + Speaking | ⚪ Pending |
| **Phase 3: Sprint** | 02.01 - 02.19 | Full Mock Exams | ⚪ Pending |

<br/>

<div align="center">
<sub>Auto-updated by <b>Supervisor Bot</b> 🤖</sub>
</div>
"""

with open("README.md", "w", encoding="utf-8") as f:
    f.write(readme)

print("README updated!")
