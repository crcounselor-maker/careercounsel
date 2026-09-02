#!/usr/bin/env python3
"""Fetch entry-level Business Admin / IS job postings from Adzuna and write site/data/jobs.json."""

import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

ADZUNA_APP_ID = os.environ.get("ADZUNA_APP_ID")
ADZUNA_APP_KEY = os.environ.get("ADZUNA_APP_KEY")
COUNTRY = os.environ.get("ADZUNA_COUNTRY", "us")
LOCATION = os.environ.get("LOCATION", "Salt Lake City, UT")
MAX_DAYS_OLD = int(os.environ.get("MAX_DAYS_OLD", "30"))
RESULTS_PER_PAGE = 50

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = REPO_ROOT / "docs" / "data" / "jobs.json"

KEYWORDS = [
    "entry level",
    "business administration",
    "associate",
    "coordinator",
    "analyst",
    "operations",
]

# Adzuna job categories relevant to Business Admin / IS students. Restricting to
# these (instead of an unfiltered keyword search) is what keeps results on-topic —
# an unrestricted search on words like "coordinator" or "analyst" pulls in
# healthcare, retail, and trucking postings that happen to use the same words.
CATEGORIES = ["admin-jobs", "it-jobs", "accounting-finance-jobs", "graduate-jobs"]

EXCLUDE_PATTERN = re.compile(
    r"\b(senior|sr\.?|manager|mgr\.?|director|dir\.?|\bvp\b|vice president|\d+\+\s*years?)\b",
    re.IGNORECASE,
)

API_URL = "https://api.adzuna.com/v1/api/jobs/{country}/search/1"


def fetch_page(category, what=None, what_or=None, where=None):
    if not ADZUNA_APP_ID or not ADZUNA_APP_KEY:
        print("ERROR: ADZUNA_APP_ID / ADZUNA_APP_KEY environment variables are required.", file=sys.stderr)
        sys.exit(1)

    params = {
        "app_id": ADZUNA_APP_ID,
        "app_key": ADZUNA_APP_KEY,
        "results_per_page": RESULTS_PER_PAGE,
        "category": category,
        "max_days_old": MAX_DAYS_OLD,
        "sort_by": "date",
        "content-type": "application/json",
    }
    if what:
        params["what"] = what
    if what_or:
        params["what_or"] = what_or
    if where:
        params["where"] = where

    resp = requests.get(API_URL.format(country=COUNTRY), params=params, timeout=30)
    resp.raise_for_status()
    return resp.json().get("results", [])


def is_excluded(title):
    return bool(EXCLUDE_PATTERN.search(title or ""))


def normalize(raw):
    return {
        "id": str(raw.get("id")),
        "title": raw.get("title", "").strip(),
        "company": (raw.get("company") or {}).get("display_name", "Unknown"),
        "location": (raw.get("location") or {}).get("display_name", ""),
        "url": raw.get("redirect_url", ""),
        "date_posted": raw.get("created", ""),
        "description_snippet": (raw.get("description") or "")[:280].strip(),
        "source": "Adzuna",
    }


WHAT_OR = " ".join(KEYWORDS)


def collect_results():
    results = {}

    for category in CATEGORIES:
        # Location-specific sweep (e.g. Salt Lake City, UT): any keyword, in-category.
        if LOCATION:
            for raw in fetch_page(category=category, what_or=WHAT_OR, where=LOCATION):
                job = normalize(raw)
                if job["id"] and not is_excluded(job["title"]):
                    results[job["id"]] = job

        # Remote sweep: nationwide, "remote" AND each keyword, in-category.
        for keyword in KEYWORDS:
            for raw in fetch_page(category=category, what=f"remote {keyword}"):
                job = normalize(raw)
                if job["id"] and not is_excluded(job["title"]):
                    results[job["id"]] = job

    return list(results.values())


def load_existing():
    if OUTPUT_PATH.exists():
        try:
            return json.loads(OUTPUT_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
    return []


def parse_date(value):
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def merge_and_prune(existing, fresh):
    by_key = {}

    for job in existing + fresh:
        key = job.get("url") or job.get("id")
        if not key:
            continue
        by_key[key] = job

    cutoff = datetime.now(timezone.utc) - timedelta(days=MAX_DAYS_OLD)
    merged = []
    for job in by_key.values():
        posted = parse_date(job.get("date_posted"))
        if posted is not None and posted < cutoff:
            continue
        merged.append(job)

    merged.sort(key=lambda j: j.get("date_posted", ""), reverse=True)
    return merged


def main():
    existing = load_existing()
    fresh = collect_results()
    merged = merge_and_prune(existing, fresh)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(merged, indent=2), encoding="utf-8")
    print(f"Wrote {len(merged)} jobs to {OUTPUT_PATH} ({len(fresh)} fetched this run).")


if __name__ == "__main__":
    main()
