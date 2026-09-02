# Entry-Level Business Admin Jobs Board

Auto-refreshing board of entry-level Business Administration / Information Systems
job postings, sourced from the [Adzuna API](https://developer.adzuna.com/).

## How it works

- `scripts/fetch_jobs.py` queries Adzuna for a set of entry-level keywords, both in
  a specific metro area and nationwide-remote, excludes senior/manager-level titles,
  dedupes against the existing dataset, drops postings older than 30 days, and
  writes the result to `site/data/jobs.json`.
- `.github/workflows/update-jobs.yml` runs that script on a 6-hour cron schedule and
  commits `site/data/jobs.json` if it changed.
- `site/` is a static frontend (no build step) that fetches `data/jobs.json` and
  renders a searchable, filterable, sortable list.

Note: `jobs.json` lives at `site/data/jobs.json` (not a top-level `/data` folder) so
that it's included when GitHub Pages serves the `/site` directory.

## Local setup

1. Copy `.env.example` to `.env` and fill in your Adzuna `app_id` / `app_key`
   (already done for you in this checkout — `.env` is gitignored and never committed).
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the fetch script:
   ```bash
   set -a; source .env; set +a  # or manually export the vars on Windows
   python scripts/fetch_jobs.py
   ```
4. Preview the site locally:
   ```bash
   cd site
   python -m http.server 8000
   ```
   Then open http://localhost:8000

## Deploying

1. Create an empty GitHub repository and push this project to it.
2. In the repo, go to **Settings → Secrets and variables → Actions** and add:
   - Secret `ADZUNA_APP_ID`
   - Secret `ADZUNA_APP_KEY`
   - (Optional) Variable `LOCATION` — defaults to `Salt Lake City, UT` if unset
3. Go to **Settings → Actions → General → Workflow permissions** and select
   **Read and write permissions** so the workflow can commit `jobs.json` updates.
4. Go to **Settings → Pages** and set the source to deploy from the `/site` folder
   on your default branch (or use a `docs/` folder / Vercel if you prefer — see notes
   below).
5. Trigger the workflow once manually (Actions tab → "Update job listings" →
   Run workflow) to populate `site/data/jobs.json` before your first deploy.

### Alternative: Vercel

Point a Vercel project at this repo with `site` as the output/root directory; no
build command is needed since it's static HTML/JS.

## Customizing

- **Keywords / exclusions**: edit `KEYWORDS` and `EXCLUDE_PATTERN` in
  `scripts/fetch_jobs.py`.
- **Location**: set the `LOCATION` env var (repo variable in Actions, or your local
  `.env`). The script always additionally runs a nationwide "remote" sweep per
  keyword.
- **Max posting age**: `MAX_DAYS_OLD` env var (default 30).
- **Styling**: colors are defined as CSS custom properties at the top of
  `site/style.css` (currently University of Utah crimson/white).
