const state = {
  jobs: [],
  search: "",
  location: "",
  sort: "newest",
};

const jobListEl = document.getElementById("job-list");
const statusLineEl = document.getElementById("status-line");
const searchInputEl = document.getElementById("search-input");
const locationSelectEl = document.getElementById("location-select");
const sortSelectEl = document.getElementById("sort-select");

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str ?? "";
  return div.innerHTML;
}

function formatDate(iso) {
  if (!iso) return "Date unknown";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "Date unknown";
  return date.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

function populateLocationOptions(jobs) {
  const locations = [...new Set(jobs.map((j) => j.location).filter(Boolean))].sort();
  for (const loc of locations) {
    const opt = document.createElement("option");
    opt.value = loc;
    opt.textContent = loc;
    locationSelectEl.appendChild(opt);
  }
}

function getFilteredJobs() {
  const query = state.search.trim().toLowerCase();

  let filtered = state.jobs.filter((job) => {
    const matchesSearch =
      !query ||
      job.title?.toLowerCase().includes(query) ||
      job.company?.toLowerCase().includes(query) ||
      job.description_snippet?.toLowerCase().includes(query);
    const matchesLocation = !state.location || job.location === state.location;
    return matchesSearch && matchesLocation;
  });

  filtered.sort((a, b) => {
    const dateA = new Date(a.date_posted).getTime() || 0;
    const dateB = new Date(b.date_posted).getTime() || 0;
    return state.sort === "newest" ? dateB - dateA : dateA - dateB;
  });

  return filtered;
}

function render() {
  const jobs = getFilteredJobs();

  if (jobs.length === 0) {
    jobListEl.innerHTML = "";
    statusLineEl.textContent = `0 jobs match your filters (${state.jobs.length} total).`;
    const empty = document.createElement("li");
    empty.className = "empty-state";
    empty.textContent = "No jobs match your filters. Try clearing the search or location.";
    jobListEl.appendChild(empty);
    return;
  }

  statusLineEl.textContent = `${jobs.length} of ${state.jobs.length} jobs shown.`;

  jobListEl.innerHTML = jobs
    .map(
      (job) => `
      <li class="job-card">
        <h2 class="job-title"><a href="${escapeHtml(job.url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(job.title)}</a></h2>
        <div class="job-meta">
          <span>${escapeHtml(job.company)}</span>
          <span>${escapeHtml(job.location)}</span>
          <span>${formatDate(job.date_posted)}</span>
          <span>${escapeHtml(job.source)}</span>
        </div>
        <p class="job-snippet">${escapeHtml(job.description_snippet)}${job.description_snippet ? "…" : ""}</p>
      </li>`
    )
    .join("");
}

async function init() {
  try {
    const res = await fetch("data/jobs.json", { cache: "no-store" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    state.jobs = await res.json();
  } catch (err) {
    statusLineEl.textContent = "Couldn't load job listings. Please try again later.";
    console.error("Failed to load jobs.json", err);
    return;
  }

  populateLocationOptions(state.jobs);
  render();
}

searchInputEl.addEventListener("input", (e) => {
  state.search = e.target.value;
  render();
});

locationSelectEl.addEventListener("change", (e) => {
  state.location = e.target.value;
  render();
});

sortSelectEl.addEventListener("change", (e) => {
  state.sort = e.target.value;
  render();
});

init();
