(() => {
  "use strict";
  // cspell:ignore labelledby resourceid subscriptionid tenantid

  const storageKey = "az104LearnerProgress.v1";
  const schemaVersion = "1.0.0";
  const forbiddenKeys = new Set([
    "tenantid",
    "subscriptionid",
    "userid",
    "username",
    "resourceid",
    "token"
  ]);
  const validStatuses = new Set(["not-started", "in-progress", "complete"]);
  const allowedTopLevel = new Set(["schemaVersion", "exportedAt", "labs"]);
  const allowedEntry = new Set([
    "status",
    "validationPassed",
    "cleanupPassed",
    "assessmentScore",
    "updatedAt"
  ]);
  const labIdPattern = /^LAB-(?:0[0-9]|1[0-9]|2[0-7])$/;
  const isoTimestampPattern = /^\d{4}-\d{2}-\d{2}[Tt]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:[Zz]|[+-]\d{2}:\d{2})$/;
  const maximumImportBytes = 256 * 1024;
  let readWarning = "";

  const isIsoTimestamp = (value) =>
    typeof value === "string" && isoTimestampPattern.test(value) && !Number.isNaN(Date.parse(value));

  const emptyRecord = () => {
    const timestamp = new Date().toISOString();
    const labs = {};
    for (let number = 0; number < 28; number += 1) {
      labs[`LAB-${String(number).padStart(2, "0")}`] = {
        status: "not-started",
        validationPassed: false,
        cleanupPassed: false,
        assessmentScore: null,
        updatedAt: timestamp
      };
    }
    return { schemaVersion, exportedAt: timestamp, labs };
  };

  function hasForbiddenKey(value) {
    if (!value || typeof value !== "object") return false;
    return Object.entries(value).some(([key, nested]) =>
      forbiddenKeys.has(key.toLowerCase()) || hasForbiddenKey(nested)
    );
  }

  function validateRecord(record) {
    if (!record || typeof record !== "object" || Array.isArray(record)) {
      throw new Error("Progress must be a JSON object.");
    }
    if (record.schemaVersion !== schemaVersion || !record.labs || typeof record.labs !== "object") {
      throw new Error(`Progress must use schemaVersion ${schemaVersion}.`);
    }
    const unexpectedTopLevel = Object.keys(record).filter((key) => !allowedTopLevel.has(key));
    if (unexpectedTopLevel.length) {
      throw new Error(`Unexpected progress field: ${unexpectedTopLevel.join(", ")}.`);
    }
    if (!isIsoTimestamp(record.exportedAt)) {
      throw new Error("Progress exportedAt must be an ISO 8601 timestamp.");
    }
    if (hasForbiddenKey(record)) {
      throw new Error("Progress contains an identity, tenant, subscription, resource, or token field.");
    }
    if (Object.keys(record.labs).length !== 28) {
      throw new Error("Progress must contain LAB-00 through LAB-27.");
    }
    for (const [labId, entry] of Object.entries(record.labs)) {
      if (!labIdPattern.test(labId) || !entry || typeof entry !== "object") {
        throw new Error(`Invalid lab progress entry: ${labId}.`);
      }
      const unexpectedEntry = Object.keys(entry).filter((key) => !allowedEntry.has(key));
      if (unexpectedEntry.length || Object.keys(entry).length !== allowedEntry.size) {
        throw new Error(`${labId} has missing or unexpected fields.`);
      }
      if (!validStatuses.has(entry.status)) {
        throw new Error(`Invalid status for ${labId}.`);
      }
      if (typeof entry.validationPassed !== "boolean" || typeof entry.cleanupPassed !== "boolean") {
        throw new Error(`${labId} must include Boolean validationPassed and cleanupPassed values.`);
      }
      if (entry.status === "complete" && (!entry.validationPassed || !entry.cleanupPassed)) {
        throw new Error(`${labId} cannot be complete until validation and cleanup pass.`);
      }
      if (entry.assessmentScore !== null &&
          (!Number.isInteger(entry.assessmentScore) || entry.assessmentScore < 0 || entry.assessmentScore > 100)) {
        throw new Error(`${labId} has an invalid assessmentScore.`);
      }
      if (["LAB-00", "LAB-26", "LAB-27"].includes(labId) && entry.assessmentScore !== null) {
        throw new Error(`${labId} is hands-on only and cannot contain an assessmentScore.`);
      }
      if (!isIsoTimestamp(entry.updatedAt)) {
        throw new Error(`${labId} has an invalid updatedAt value.`);
      }
    }
    return record;
  }

  function readRecord(rejectInvalid = false) {
    readWarning = "";
    try {
      const raw = window.localStorage.getItem(storageKey);
      if (!raw) return emptyRecord();
      return validateRecord(JSON.parse(raw));
    } catch (error) {
      console.warn("Ignoring invalid AZ-104 progress:", error);
      readWarning = "Stored browser progress is unavailable or invalid. Import a valid backup or clear local progress.";
      if (rejectInvalid) {
        throw new Error(readWarning);
      }
      return emptyRecord();
    }
  }

  function writeRecord(record) {
    record.exportedAt = new Date().toISOString();
    validateRecord(record);
    window.localStorage.setItem(storageKey, JSON.stringify(record));
  }

  // The quiz updates a fresh, validated record rather than a page's cached
  // snapshot. Assessment results never imply deployment or cleanup success.
  function saveAssessmentScore(labId, score) {
    if (!/^LAB-(?:0[1-9]|1[0-9]|2[0-5])$/.test(labId)) {
      throw new Error("Only LAB-01 through LAB-25 have an assessment score.");
    }
    if (!Number.isInteger(score) || score < 0 || score > 100) {
      throw new Error("Assessment scores must be whole numbers from 0 through 100.");
    }
    const record = readRecord(true);
    record.labs[labId].assessmentScore = score;
    record.labs[labId].updatedAt = new Date().toISOString();
    writeRecord(record);
    return score;
  }

  window.az104Progress = Object.freeze({ saveAssessmentScore });

  function errorText(error) {
    return error instanceof Error ? error.message : String(error);
  }

  function persistLabChange(labId, statusElement, change, successMessage) {
    try {
      const record = readRecord(true);
      const entry = record.labs[labId];
      change(entry);
      entry.updatedAt = new Date().toISOString();
      writeRecord(record);
      statusElement.textContent = successMessage(entry);
      return true;
    } catch (error) {
      statusElement.textContent = `Progress could not be saved in this browser: ${errorText(error)}`;
      return false;
    }
  }

  function currentLabId() {
    const match = window.location.pathname.match(/\/labs\/((?:0[0-9]|1[0-9]|2[0-7]))-[^/]+\/?(?:index\.html)?$/);
    return match ? `LAB-${match[1]}` : null;
  }

  function masteryText(entry) {
    if (entry.assessmentScore === null) return "Assessment not recorded";
    if (entry.assessmentScore >= 85) return "Mastery";
    if (entry.assessmentScore >= 70) return "Targeted review";
    return "Repeat mapped tasks";
  }

  function makeButton(label, action) {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = label;
    button.addEventListener("click", action);
    return button;
  }

  function renderLabControl(main, labId) {
    if (main.querySelector("[data-az104-lab-progress]")) return;
    const record = readRecord();
    const entry = record.labs[labId];
    const card = document.createElement("section");
    card.className = "az104-progress-card";
    card.dataset.az104LabProgress = labId;
    card.setAttribute("aria-labelledby", "az104-lab-progress-title");
    const title = document.createElement("h2");
    title.id = "az104-lab-progress-title";
    title.textContent = "Record this lab";
    const summary = document.createElement("p");
    summary.textContent = readWarning || `Status: ${entry.status}; ${masteryText(entry)}.`;
    const actions = document.createElement("div");
    actions.className = "az104-progress-actions";

    actions.append(makeButton("Mark in progress", () => {
      persistLabChange(labId, summary, (current) => {
        current.status = "in-progress";
      }, (current) => `Status: ${current.status}; ${masteryText(current)}.`);
    }));
    actions.append(makeButton("Record validation pass", () => {
      persistLabChange(labId, summary, (current) => {
        current.validationPassed = true;
        current.status = current.cleanupPassed ? "complete" : "in-progress";
      }, (current) => `Status: ${current.status}; deployment validation passed.`);
    }));
    actions.append(makeButton("Record cleanup pass", () => {
      persistLabChange(labId, summary, (current) => {
        current.cleanupPassed = true;
        current.status = current.validationPassed ? "complete" : "in-progress";
      }, (current) => `Status: ${current.status}; cleanup validation passed.`);
    }));

    const labNumber = Number.parseInt(labId.slice(4), 10);
    if (labNumber >= 1 && labNumber <= 25) {
      const scoreLabel = document.createElement("label");
      scoreLabel.className = "az104-score-label";
      scoreLabel.setAttribute("for", "az104-assessment-score");
      scoreLabel.textContent = "Assessment score (0–100): ";
      const scoreInput = document.createElement("input");
      scoreInput.id = "az104-assessment-score";
      scoreInput.type = "number";
      scoreInput.min = "0";
      scoreInput.max = "100";
      scoreInput.step = "1";
      if (entry.assessmentScore !== null) scoreInput.value = String(entry.assessmentScore);
      scoreLabel.append(scoreInput);
      actions.append(scoreLabel);
      actions.append(makeButton("Save score", () => {
        const score = Number(scoreInput.value);
        if (!scoreInput.value.trim() || !Number.isInteger(score) || score < 0 || score > 100) {
          summary.textContent = "Enter a whole-number assessment score from 0 through 100.";
          scoreInput.focus();
          return;
        }
        try {
          saveAssessmentScore(labId, score);
          const savedEntry = readRecord(true).labs[labId];
          Object.assign(entry, savedEntry);
          summary.textContent = `Status: ${savedEntry.status}; ${masteryText(savedEntry)}.`;
        } catch (error) {
          summary.textContent = `Progress could not be saved in this browser: ${errorText(error)}`;
        }
      }));
    }

    card.append(title, summary, actions);
    const firstHeading = main.querySelector("h1");
    if (firstHeading && firstHeading.nextSibling) {
      firstHeading.parentNode.insertBefore(card, firstHeading.nextSibling);
    } else {
      main.prepend(card);
    }
  }

  function renderDashboard(main) {
    if (main.querySelector("[data-az104-progress-dashboard]")) return;
    const record = readRecord();
    const complete = Object.values(record.labs).filter((entry) => entry.status === "complete").length;
    const card = document.createElement("section");
    card.className = "az104-progress-card";
    card.dataset.az104ProgressDashboard = "true";
    card.setAttribute("aria-labelledby", "az104-progress-dashboard-title");
    card.innerHTML = `
      <h2 id="az104-progress-dashboard-title">Local dashboard</h2>
      <p><strong>${complete} of 28 labs complete</strong></p>
      <progress class="az104-progress-meter" max="28" value="${complete}" aria-label="${complete} of 28 labs complete"></progress>
      <p class="az104-progress-message" role="status" aria-live="polite"></p>
    `;
    const actions = document.createElement("div");
    actions.className = "az104-progress-actions";
    const message = card.querySelector(".az104-progress-message");
    message.textContent = readWarning;

    actions.append(makeButton("Export JSON", () => {
      try {
        const exported = validateRecord(readRecord(true));
        exported.exportedAt = new Date().toISOString();
        const blob = new Blob([JSON.stringify(exported, null, 2)], { type: "application/json" });
        const link = document.createElement("a");
        const objectUrl = URL.createObjectURL(blob);
        link.href = objectUrl;
        link.download = "az104-progress.json";
        document.body.append(link);
        link.click();
        link.remove();
        window.setTimeout(() => URL.revokeObjectURL(objectUrl), 0);
        message.textContent = "Progress exported. The file contains no identity or Azure environment fields.";
      } catch (error) {
        message.textContent = `Export failed: ${errorText(error)}`;
      }
    }));

    const importLabel = document.createElement("label");
    importLabel.className = "az104-file-button";
    importLabel.textContent = "Import JSON";
    const file = document.createElement("input");
    file.type = "file";
    file.accept = "application/json,.json";
    file.setAttribute("aria-label", "Import AZ-104 progress JSON");
    file.addEventListener("change", async () => {
      if (!file.files.length) return;
      try {
        const selectedFile = file.files[0];
        if (selectedFile.size > maximumImportBytes) {
          throw new Error("Progress imports must be 256 KiB or smaller.");
        }
        const imported = validateRecord(JSON.parse(await selectedFile.text()));
        writeRecord(imported);
        message.textContent = "Progress imported successfully. Reloading dashboard.";
        window.location.reload();
      } catch (error) {
        message.textContent = `Import rejected: ${errorText(error)}`;
      } finally {
        file.value = "";
      }
    });
    importLabel.append(file);
    actions.append(importLabel);
    actions.append(makeButton("Clear local progress", () => {
      if (window.confirm("Clear all AZ-104 progress stored in this browser?")) {
        try {
          window.localStorage.removeItem(storageKey);
          message.textContent = "Local progress cleared. Reloading dashboard.";
          window.location.reload();
        } catch (error) {
          message.textContent = `Local progress could not be cleared: ${errorText(error)}`;
        }
      }
    }));
    card.append(actions);

    const grid = document.createElement("div");
    grid.className = "az104-progress-grid";
    for (let number = 0; number < 28; number += 1) {
      const labId = `LAB-${String(number).padStart(2, "0")}`;
      const entry = record.labs[labId] || { status: "not-started", assessmentScore: null };
      const item = document.createElement("div");
      item.className = "az104-progress-item";
      item.dataset.status = entry.status;
      item.innerHTML = `<strong>${labId}</strong><br>${entry.status}<br>${masteryText(entry)}`;
      grid.append(item);
    }
    card.append(grid);
    main.append(card);
  }

  function renderDomainDashboard(container) {
    if (container.dataset.az104Rendered === "true") return;
    const labIds = (container.dataset.az104DomainLabs || "")
      .split(",")
      .filter((labId) => labIdPattern.test(labId));
    const record = readRecord();
    const complete = labIds.filter((labId) => record.labs[labId]?.status === "complete").length;
    const heading = document.createElement("h2");
    heading.textContent = "Domain progress";
    const summary = document.createElement("p");
    summary.innerHTML = `<strong>${complete} of ${labIds.length} labs complete</strong>`;
    const meter = document.createElement("progress");
    meter.className = "az104-progress-meter";
    meter.max = labIds.length;
    meter.value = complete;
    meter.setAttribute("aria-label", `${complete} of ${labIds.length} domain labs complete`);
    container.append(heading, summary, meter);
    if (readWarning) {
      const warning = document.createElement("p");
      warning.setAttribute("role", "status");
      warning.textContent = readWarning;
      container.append(warning);
    }
    container.dataset.az104Rendered = "true";
  }

  function render() {
    const main = document.querySelector("main .md-content__inner") || document.querySelector("main");
    if (!main) return;
    const labId = currentLabId();
    if (labId) renderLabControl(main, labId);
    if (/\/learner-progress\/?(?:index\.html)?$/.test(window.location.pathname)) {
      renderDashboard(main);
    }
    main.querySelectorAll("[data-az104-domain-labs]").forEach(renderDomainDashboard);
  }

  if (typeof document$ !== "undefined") {
    document$.subscribe(render);
  } else if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", render);
  } else {
    render();
  }
})();
