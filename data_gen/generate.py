"""
Generate synthetic product data for "Voxly", a made-up AI voice app.

Why synthetic? Real product event data is never public. Generating it
ourselves lets us PLANT known effects (e.g. "the new onboarding lifts
activation by 4 points") and then check that our analysis finds them.
That is the best way to prove an analysis method works.

Outputs three CSV files in data/raw/:
  users.csv        one row per user (who they are, how they arrived)
  assignments.csv  which experiment variant each user saw
  events.csv       everything users did in the product (the event log)

Run:  python data_gen/generate.py
"""

from pathlib import Path

import numpy as np
import pandas as pd

SEED = 42  # fixed seed = the same data every run (reproducible)
N_USERS = 20_000
START = pd.Timestamp("2026-09-01")
SIGNUP_DAYS = 56  # users sign up over 8 weeks
OBSERVE_DAYS = 84  # we observe behaviour for 12 weeks in total

# Experiment: new guided onboarding, shown to users who sign up in weeks 3-8
EXP_ID = "onboarding_v2"
EXP_START = START + pd.Timedelta(days=14)
EXP_END = START + pd.Timedelta(days=56)

# ---- The "truth" we plant (the analysis should recover these) ----
BASE_ACTIVATION_LOGIT = -0.55  # ~37% of control users activate
TREATMENT_ACTIVATION_LIFT = 0.20  # in logit units, ~ +4 percentage points
TREATMENT_USAGE_LIFT = 0.05  # +5% characters generated, for active users
# Paid conversion is NOT affected by the treatment (a guardrail metric)

CHANNELS = ["organic", "paid_social", "referral", "partner"]
CHANNEL_P = [0.45, 0.30, 0.15, 0.10]
CHANNEL_EFFECT = {"organic": 0.0, "paid_social": -0.35, "referral": 0.40, "partner": 0.15}
COUNTRIES = ["US", "GB", "DE", "PL", "IN", "BR", "FR", "ES"]
COUNTRY_P = [0.30, 0.10, 0.10, 0.08, 0.17, 0.10, 0.08, 0.07]
DEVICES = ["desktop", "mobile"]
DEVICE_P = [0.62, 0.38]


def sigmoid(x):
    return 1 / (1 + np.exp(-x))


def make_users(rng):
    """Who the users are. Each has a hidden 'engagement' trait we never export."""
    n = N_USERS
    signup_ts = START + pd.to_timedelta(rng.uniform(0, SIGNUP_DAYS, n), unit="D")
    channel = rng.choice(CHANNELS, n, p=CHANNEL_P)
    device = rng.choice(DEVICES, n, p=DEVICE_P)

    # Hidden trait: how engaged this person will be. Drives everything below.
    engagement = rng.normal(0, 1, n) + np.vectorize(CHANNEL_EFFECT.get)(channel)
    engagement += np.where(device == "desktop", 0.25, -0.25)

    # Visits to the marketing site BEFORE sign-up. It is measured before the
    # experiment starts and correlates with engagement, which makes it a
    # good covariate for CUPED variance reduction later.
    pre_signup_sessions = rng.poisson(np.exp(0.6 + 0.45 * engagement))

    users = pd.DataFrame(
        {
            "user_id": [f"u{i:05d}" for i in range(n)],
            "signup_ts": signup_ts.round("s"),
            "country": rng.choice(COUNTRIES, n, p=COUNTRY_P),
            "channel": channel,
            "device": device,
            "pre_signup_sessions": pre_signup_sessions,
        }
    )
    return users, engagement


def make_assignments(rng, users):
    """Random 50/50 split for users who signed up during the experiment."""
    in_exp = (users.signup_ts >= EXP_START) & (users.signup_ts < EXP_END)
    exp_users = users.loc[in_exp, ["user_id", "signup_ts"]].copy()
    exp_users["experiment_id"] = EXP_ID
    exp_users["variant"] = rng.choice(["control", "treatment"], len(exp_users))
    exp_users = exp_users.rename(columns={"signup_ts": "assigned_ts"})
    return exp_users[["user_id", "experiment_id", "variant", "assigned_ts"]]


def make_events(rng, users, engagement, assignments):
    """Simulate what each user does, day by day, as an event log."""
    treated = users.user_id.isin(assignments.loc[assignments.variant == "treatment", "user_id"]).to_numpy()
    end_ts = START + pd.Timedelta(days=OBSERVE_DAYS)

    # 1) Activation = generating a first voice within 7 days of sign-up
    act_logit = BASE_ACTIVATION_LOGIT + 0.9 * engagement + TREATMENT_ACTIVATION_LIFT * treated
    activated = rng.random(len(users)) < sigmoid(act_logit)

    rows = []
    for i, u in enumerate(users.itertuples(index=False)):
        t0 = u.signup_ts
        rows.append((u.user_id, t0, "signup", 0))
        # Most users start a session right after signing up
        rows.append((u.user_id, t0 + pd.Timedelta(seconds=5), "session_start", 0))
        if rng.random() < sigmoid(0.3 + 0.8 * engagement[i]):
            rows.append((u.user_id, t0 + pd.Timedelta(minutes=rng.uniform(1, 30)), "project_created", 0))
        if not activated[i]:
            continue

        # First voice: within 7 days, usually on day 0-1
        first = t0 + pd.Timedelta(hours=float(min(rng.exponential(18), 167)))
        usage_mult = 1 + TREATMENT_USAGE_LIFT * treated[i]
        rows.append((u.user_id, first, "voice_generated", int(rng.lognormal(6.5, 0.8) * usage_mult)))

        # 2) Retention: active in later weeks with decaying probability
        n_weeks = int((end_ts - t0).days // 7)
        for w in range(1, n_weeks + 1):
            p_active = sigmoid(0.4 + 1.0 * engagement[i] - 0.9 * np.log(w + 1))
            if rng.random() > p_active:
                continue
            for _ in range(rng.poisson(1 + max(engagement[i], 0) * 1.5) + 1):
                ts = t0 + pd.Timedelta(days=7 * w + rng.uniform(0, 7))
                if ts >= end_ts:
                    continue
                rows.append((u.user_id, ts, "session_start", 0))
                for _ in range(rng.poisson(2.0)):
                    chars = int(rng.lognormal(6.5 + 0.2 * engagement[i], 0.8) * usage_mult)
                    rows.append((u.user_id, ts + pd.Timedelta(minutes=rng.uniform(1, 40)), "voice_generated", chars))

        # 3) Paid conversion: only activated users, NOT affected by treatment
        if rng.random() < sigmoid(-2.6 + 0.8 * engagement[i]):
            ts = first + pd.Timedelta(days=rng.exponential(10))
            if ts < end_ts:
                rows.append((u.user_id, ts, "subscription_started", 0))

    events = pd.DataFrame(rows, columns=["user_id", "event_ts", "event_name", "characters"])
    events = events[events.event_ts < end_ts].sort_values("event_ts").reset_index(drop=True)
    events["event_ts"] = events.event_ts.dt.round("s")
    events.insert(0, "event_id", [f"e{i:07d}" for i in range(len(events))])
    return events


def main():
    rng = np.random.default_rng(SEED)
    out = Path(__file__).resolve().parents[1] / "data" / "raw"
    out.mkdir(parents=True, exist_ok=True)

    users, engagement = make_users(rng)
    assignments = make_assignments(rng, users)
    events = make_events(rng, users, engagement, assignments)

    users.to_csv(out / "users.csv", index=False)
    assignments.to_csv(out / "assignments.csv", index=False)
    events.to_csv(out / "events.csv", index=False)
    print(f"users={len(users):,}  assignments={len(assignments):,}  events={len(events):,}")


if __name__ == "__main__":
    main()
