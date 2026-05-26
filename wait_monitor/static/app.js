const airportGrid = document.getElementById("airportGrid");
const statusBanner = document.getElementById("statusBanner");
const refreshButton = document.getElementById("refreshButton");
const airportCardTemplate = document.getElementById("airportCardTemplate");
const entryTemplate = document.getElementById("entryTemplate");

function minutesText(value) {
  if (value === null || value === undefined) {
    return "n/a";
  }
  return `${value} min`;
}

function deltaText(entry) {
  if (entry.delta_avg_minutes === null || entry.delta_avg_minutes === undefined) {
    return "No previous value";
  }

  const amount = Math.abs(entry.delta_avg_minutes).toFixed(1);
  if (entry.delta_direction === "up") {
    return `▲ ${amount} min vs previous`;
  }
  if (entry.delta_direction === "down") {
    return `▼ ${amount} min vs previous`;
  }
  return "■ unchanged vs previous";
}

function deltaClass(entry) {
  if (entry.delta_direction === "up") return "delta-up";
  if (entry.delta_direction === "down") return "delta-down";
  return "delta-same";
}

function freshnessClass(seconds) {
  if (seconds === null || seconds === undefined) {
    return "";
  }
  if (seconds < 10 * 60) {
    return "freshness-green";
  }
  if (seconds < 30 * 60) {
    return "freshness-yellow";
  }
  return "freshness-red";
}

function renderEntry(entry, options = {}) {
  const node = entryTemplate.content.firstElementChild.cloneNode(true);
  node.querySelector(".entry-service").textContent = entry.service;
  node.querySelector(".entry-checkpoint").textContent = entry.checkpoint_label;
  node.querySelector(".entry-avg-value").textContent = minutesText(entry.current.avg_minutes);
  const updatedNode = node.querySelector(".entry-updated");
  updatedNode.textContent = `Updated ${entry.current.updated_ago}`;
  const entryFreshnessClass = freshnessClass(entry.current.updated_age_seconds);
  if (entryFreshnessClass) {
    updatedNode.classList.add(entryFreshnessClass);
  }
  if (options.nested) {
    node.classList.add("entry-nested");
  }

  const metrics = node.querySelector(".metrics");
  [
    ["Low", minutesText(entry.current.low_minutes)],
    ["Average", minutesText(entry.current.avg_minutes)],
    ["High", minutesText(entry.current.high_minutes)],
  ].forEach(([label, value]) => {
    const metric = document.createElement("div");
    metric.className = "metric";
    metric.innerHTML = `<div class="metric-label">${label}</div><div class="metric-value">${value}</div>`;
    metrics.appendChild(metric);
  });

  const previous = node.querySelector(".previous");
  if (entry.previous) {
    previous.innerHTML = `
      <div>Previous average: <strong>${minutesText(entry.previous.avg_minutes)}</strong> (${entry.previous.updated_ago})</div>
      <div class="${deltaClass(entry)}">${deltaText(entry)}</div>
      <div>Current snapshot recorded at ${entry.current.recorded_at}</div>
    `;
  } else {
    previous.innerHTML = `<div class="delta-same">No previous saved value yet.</div><div>Current snapshot recorded at ${entry.current.recorded_at}</div>`;
  }

  if (options.childEntries && options.childEntries.length > 0) {
    const childGroup = document.createElement("details");
    childGroup.className = "child-group";

    const childSummary = document.createElement("summary");
    const label = options.childEntries.length === 1 ? "checkpoint" : "checkpoints";
    childSummary.textContent = `${options.childEntries.length} additional ${label}`;
    childGroup.appendChild(childSummary);

    const childContainer = document.createElement("div");
    childContainer.className = "child-entry-list";
    options.childEntries.forEach((childEntry) => {
      childContainer.appendChild(renderEntry(childEntry, { nested: true }));
    });
    childGroup.appendChild(childContainer);
    node.querySelector(".entry-details").appendChild(childGroup);
  }

  return node;
}

function groupedServiceEntries(serviceGroup) {
  const entries = serviceGroup.entries.map((entry) => ({
    ...entry,
    service: serviceGroup.service,
  }));
  const allCheckpoints = entries.find((entry) => entry.checkpoint === "All Checkpoints");
  if (!allCheckpoints) {
    return entries.map((entry) => ({
      parent: entry,
      children: [],
    }));
  }
  return [
    {
      parent: allCheckpoints,
      children: entries.filter((entry) => entry !== allCheckpoints),
    },
  ];
}

function renderAirportCard(airport) {
  const node = airportCardTemplate.content.firstElementChild.cloneNode(true);
  node.querySelector(".airport-code").textContent = airport.airport_code;
  node.querySelector(".airport-name").textContent = airport.airport_name ?? "Airport";

  const updatedText = airport.last_updated_ago
    ? `Updated ${airport.last_updated_ago}`
    : airport.used_cached_current
      ? "Using saved values"
      : "No current data";
  const updatedPill = node.querySelector(".updated-pill");
  updatedPill.textContent = updatedText;
  const airportFreshnessClass = freshnessClass(airport.last_updated_age_seconds);
  if (airportFreshnessClass) {
    updatedPill.classList.add(airportFreshnessClass);
  }

  const entriesContainer = node.querySelector(".entries");
  if (!airport.found) {
    const missing = document.createElement("div");
    missing.textContent = "Airport Not Found";
    entriesContainer.appendChild(missing);
    return node;
  }

  airport.services.forEach((serviceGroup) => {
    groupedServiceEntries(serviceGroup).forEach(({ parent, children }) => {
      entriesContainer.appendChild(
        renderEntry(parent, {
          childEntries: children,
        }),
      );
    });
  });

  if (airport.warnings && airport.warnings.length > 0) {
    const warningBlock = document.createElement("div");
    warningBlock.innerHTML = `<strong>Warnings</strong>`;
    const list = document.createElement("ul");
    list.className = "warning-list";
    airport.warnings.forEach((warning) => {
      const item = document.createElement("li");
      item.textContent = warning;
      list.appendChild(item);
    });
    warningBlock.appendChild(list);
    entriesContainer.appendChild(warningBlock);
  }

  return node;
}

async function loadAirports() {
  refreshButton.disabled = true;
  statusBanner.textContent = "Refreshing airport data...";
  airportGrid.innerHTML = "";

  try {
    const response = await fetch("/api/waits/all", { cache: "no-store" });
    const payload = await response.json();
    payload.airports.forEach((airport) => {
      airportGrid.appendChild(renderAirportCard(airport));
    });
    statusBanner.textContent = `Last dashboard refresh: ${payload.generated_at}`;
  } catch (error) {
    statusBanner.textContent = `Refresh failed: ${error}`;
  } finally {
    refreshButton.disabled = false;
  }
}

refreshButton.addEventListener("click", () => {
  loadAirports();
});

loadAirports();
