# 🏃 Vamshi's Running Dashboard

A free, auto-updating running dashboard powered by Strava API + GitHub Actions + GitHub Pages.

**Live URL:** `https://<your-github-username>.github.io/strava-dashboard/`

Auto-syncs every 2 hours via GitHub Actions — no server needed.

---

## Setup (one-time, ~15 minutes)

### Step 1 — Create this repo on GitHub

1. Go to [github.com](https://github.com) → **New repository**
2. Name it `strava-dashboard`
3. Set to **Public** (required for free GitHub Pages)
4. Do **not** add a README (you'll push these files)

Upload all these files (or `git push`):
```
index.html
data/runs.json
scripts/sync.py
.github/workflows/sync.yml
README.md
```

### Step 2 — Enable GitHub Pages

1. Go to your repo → **Settings** → **Pages**
2. Source: **Deploy from a branch**
3. Branch: `main` / folder: `/ (root)`
4. Click **Save**

Your dashboard will be live at:
`https://<your-username>.github.io/strava-dashboard/`

### Step 3 — Create a Strava API app

1. Go to [strava.com/settings/api](https://www.strava.com/settings/api)
2. Create an app (name/description can be anything)
3. Set **Authorization Callback Domain** to `localhost`
4. Note your **Client ID** and **Client Secret**

### Step 4 — Get your Strava Refresh Token

Run this in your browser (replace `YOUR_CLIENT_ID`):

```
https://www.strava.com/oauth/authorize?client_id=YOUR_CLIENT_ID&response_type=code&redirect_uri=http://localhost&approval_prompt=force&scope=activity:read_all
```

1. Authorize the app → you'll be redirected to `http://localhost/?code=XXXX`
2. Copy the `code=XXXX` value
3. Run this in your terminal (replace the values):

```bash
curl -X POST https://www.strava.com/oauth/token \
  -d client_id=YOUR_CLIENT_ID \
  -d client_secret=YOUR_CLIENT_SECRET \
  -d code=YOUR_CODE \
  -d grant_type=authorization_code
```

4. From the response, copy the `refresh_token` value

### Step 5 — Add secrets to GitHub

Go to your repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

Add these three secrets:

| Name | Value |
|------|-------|
| `STRAVA_CLIENT_ID` | Your Strava app Client ID |
| `STRAVA_CLIENT_SECRET` | Your Strava app Client Secret |
| `STRAVA_REFRESH_TOKEN` | The refresh token from Step 4 |

### Step 6 — Trigger first sync

Go to your repo → **Actions** → **Sync Strava data** → **Run workflow**

Wait ~30 seconds → your dashboard will populate with all your runs!

---

## How it works

```
Every 2 hours:
  GitHub Actions → scripts/sync.py
    → Strava API (fetch activities)
    → data/runs.json (write)
    → git commit & push
  
  GitHub Pages serves index.html
    → fetch data/runs.json
    → render charts & coaching
```

## Sharing

Just share your GitHub Pages URL:
`https://<your-username>.github.io/strava-dashboard/`

It's public and readable by anyone — no login needed.
