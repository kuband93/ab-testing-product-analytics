"""
First look at the generated data. Saves charts to figures/.

Run:  python data_gen/explore.py   (after generate.py)
"""

from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
IMG = ROOT / "figures"
IMG.mkdir(parents=True, exist_ok=True)

BLUE, GREY, ORANGE = "#2b6cb0", "#a0aec0", "#dd6b20"
plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False, "font.size": 10})

users = pd.read_csv(RAW / "users.csv", parse_dates=["signup_ts"])
assign = pd.read_csv(RAW / "assignments.csv", parse_dates=["assigned_ts"])
events = pd.read_csv(RAW / "events.csv", parse_dates=["event_ts"])

# ---- Chart 1: sign-ups per day, experiment window shaded ----
daily = users.set_index("signup_ts").resample("D").size()
fig, ax = plt.subplots(figsize=(8, 3.2))
ax.bar(daily.index, daily.values, color=GREY, width=0.8)
ax.axvspan(assign.assigned_ts.min(), assign.assigned_ts.max(), color=BLUE, alpha=0.12)
ax.text(assign.assigned_ts.min(), daily.max() * 1.02, "  experiment running (50/50 split)", color=BLUE, va="bottom")
ax.set_title("New sign-ups per day", loc="left", fontweight="bold")
ax.set_ylim(0, daily.max() * 1.15)
ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=mdates.TU))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
fig.tight_layout()
fig.savefig(IMG / "signups.png", dpi=150)

# ---- Chart 2: the user funnel (how many users ever reached each step) ----
steps = ["signup", "project_created", "voice_generated", "subscription_started"]
labels = ["Signed up", "Created a project", "Generated a voice", "Started paying"]
reached = [events.loc[events.event_name == s, "user_id"].nunique() for s in steps]
fig, ax = plt.subplots(figsize=(8, 3.2))
bars = ax.barh(labels[::-1], reached[::-1], color=[ORANGE, BLUE, BLUE, GREY])
for b, v in zip(bars, reached[::-1]):
    ax.text(v, b.get_y() + b.get_height() / 2, f"  {v:,} ({v / reached[0]:.0%})", va="center")
ax.set_xlim(0, reached[0] * 1.25)
ax.set_xticks([])
ax.spines["bottom"].set_visible(False)
ax.set_title("User funnel: how many users ever reached each step", loc="left", fontweight="bold")
fig.tight_layout()
fig.savefig(IMG / "funnel.png", dpi=150)

print("Saved charts to", IMG)
