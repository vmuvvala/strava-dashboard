#!/usr/bin/env python3
"""
Strava sync script — fetches activities and writes data/runs.json
Runs via GitHub Actions every 2 hours.
"""

import os, json, time, requests
from datetime import datetime, timezone

CLIENT_ID     = os.environ["STRAVA_CLIENT_ID"]
CLIENT_SECRET = os.environ["STRAVA_CLIENT_SECRET"]
REFRESH_TOKEN = os.environ["STRAVA_REFRESH_TOKEN"]

def get_access_token():
    r = requests.post("https://www.strava.com/oauth/token", data={
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": REFRESH_TOKEN,
        "grant_type": "refresh_token",
    })
    r.raise_for_status()
    return r.json()["access_token"]

def get_activities(token):
    headers = {"Authorization": f"Bearer {token}"}
    activities = []
    page = 1
    # fetch from Jan 1 2026
    after = int(datetime(2026, 1, 1, tzinfo=timezone.utc).timestamp())
    while True:
        r = requests.get(
            "https://www.strava.com/api/v3/athlete/activities",
            headers=headers,
            params={"after": after, "per_page": 100, "page": page}
        )
        r.raise_for_status()
        batch = r.json()
        if not batch:
            break
        activities.extend(batch)
        page += 1
        time.sleep(0.5)
    return activities

def classify_run(name, distance_m, elapsed_sec):
    name_lower = name.lower()
    if any(w in name_lower for w in ["track", "interval", "repeat", "400", "600", "800", "1000", "1200"]):
        return "interval"
    if any(w in name_lower for w in ["hill", "hills"]):
        return "hill"
    if any(w in name_lower for w in ["long", "8 mile", "9 mile", "10 mile", "saturday", "weekend"]):
        return "long"
    if any(w in name_lower for w in ["recovery", "easy", "cool", "warm"]):
        return "recovery"
    if any(w in name_lower for w in ["tempo", "threshold"]):
        return "tempo"
    if distance_m >= 10000:
        return "long"
    if elapsed_sec and distance_m / elapsed_sec > 3.2:
        return "interval"
    return "easy"

def sec_to_pace(dist_m, time_sec):
    if not dist_m or not time_sec:
        return "--"
    pace_sec = time_sec / (dist_m / 1000)
    m, s = divmod(int(pace_sec), 60)
    return f"{m}:{s:02d}"

def process(activities):
    runs = []
    for a in activities:
        if a.get("type") not in ("Run",) and a.get("sport_type") not in ("Run",):
            continue
        dist = a.get("distance", 0)
        if dist < 500:
            continue
        moving = a.get("moving_time", 0)
        elapsed = a.get("elapsed_time", 0)
        name = a.get("name", "Run")
        date = a.get("start_date_local", "")[:10]
        runs.append({
            "id": str(a["id"]),
            "name": name,
            "date": date,
            "distance_km": round(dist / 1000, 2),
            "moving_time_sec": moving,
            "elapsed_time_sec": elapsed,
            "pace": sec_to_pace(dist, moving),
            "elevation_gain": round(a.get("total_elevation_gain", 0), 1),
            "pr_count": a.get("pr_count", 0),
            "achievement_count": a.get("achievement_count", 0),
            "kudos_count": a.get("kudos_count", 0),
            "avg_hr": a.get("average_heartrate"),
            "max_hr": a.get("max_heartrate"),
            "calories": a.get("calories", 0),
            "run_type": classify_run(name, dist, moving),
        })
    runs.sort(key=lambda r: r["date"], reverse=True)
    return runs

def compute_stats(runs):
    if not runs:
        return {}
    total_dist = sum(r["distance_km"] for r in runs)
    total_prs  = sum(r["pr_count"] for r in runs)
    longest    = max(r["distance_km"] for r in runs)

    # weekly volumes
    weeks = {}
    for r in runs:
        d = datetime.fromisoformat(r["date"])
        # Monday of that week
        mon = d - __import__("timedelta", fromlist=["timedelta"])
        from datetime import timedelta
        mon = (d - timedelta(days=d.weekday())).strftime("%Y-%m-%d")
        weeks[mon] = round(weeks.get(mon, 0) + r["distance_km"], 2)
    sorted_weeks = sorted(weeks.items())
    peak_week_km = max(weeks.values()) if weeks else 0

    # long run progression (runs >= 6km, sorted oldest first)
    long_runs = sorted([r for r in runs if r["distance_km"] >= 6], key=lambda r: r["date"])

    # best 5K estimate from runs >= 5km
    best_5k_sec = None
    for r in runs:
        if r["distance_km"] >= 5 and r["moving_time_sec"]:
            est = (r["moving_time_sec"] / r["distance_km"]) * 5
            if best_5k_sec is None or est < best_5k_sec:
                best_5k_sec = est
    best_5k = None
    if best_5k_sec:
        m, s = divmod(int(best_5k_sec), 60)
        best_5k = f"{m}:{s:02d}"

    return {
        "total_runs": len(runs),
        "total_km": round(total_dist, 1),
        "total_miles": round(total_dist * 0.621371, 1),
        "total_prs": total_prs,
        "longest_km": longest,
        "peak_week_km": round(peak_week_km, 1),
        "best_5k_est": best_5k,
        "weekly_volumes": [{"week": w, "km": k} for w, k in sorted_weeks],
        "long_run_progression": [{"date": r["date"], "km": r["distance_km"]} for r in long_runs],
    }

def main():
    print("🔑  Getting Strava access token...")
    token = get_access_token()

    print("📡  Fetching activities...")
    raw = get_activities(token)
    print(f"    → {len(raw)} total activities fetched")

    runs = process(raw)
    print(f"    → {len(runs)} runs processed")

    stats = compute_stats(runs)

    output = {
        "synced_at": datetime.now(timezone.utc).isoformat(),
        "stats": stats,
        "runs": runs,
    }

    os.makedirs("data", exist_ok=True)
    with open("data/runs.json", "w") as f:
        json.dump(output, f, indent=2)
    print(f"✅  data/runs.json written ({len(runs)} runs)")

if __name__ == "__main__":
    main()
