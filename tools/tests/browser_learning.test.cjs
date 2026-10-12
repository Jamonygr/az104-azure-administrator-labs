"use strict";

// Exercise the shipped scripts together with browser storage, fetch, and DOM
// boundaries. No Azure calls, third-party test packages, or production data.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const test = require("node:test");
const root = path.resolve(__dirname, "../..");
const progressScript = fs.readFileSync(path.join(root, "docs/site-assets/progress.js"), "utf8");
const quizScript = fs.readFileSync(path.join(root, "docs/site-assets/quiz.js"), "utf8");
const key = "az104LearnerProgress.v1";
const base = "https://example.test/az104-azure-administrator-labs/";

class Element {
  constructor(tag, document) {
    this.tagName = tag.toLowerCase();
    this.document = document;
    this.children = [];
    this.dataset = {};
    this.attributes = {};
    this.listeners = {};
    this.className = "";
    this.value = "";
    this._text = "";
    this.classList = { add: (name) => { this.className += ` ${name}`; } };
  }
  get isConnected() { return this === this.document.body || Boolean(this.parentNode?.isConnected); }
  set textContent(value) { this._text = String(value); this.replaceChildren(); }
  get textContent() { return this._text + this.children.map((child) => child.textContent).join(""); }
  set innerHTML(value) {
    this.replaceChildren();
    const stack = [this];
    for (const token of value.match(/<[^>]+>|[^<]+/g) || []) {
      if (token.startsWith("</")) { stack.pop(); continue; }
      if (!token.startsWith("<")) { stack.at(-1)._text += token; continue; }
      const name = token.match(/^<([a-z0-9-]+)/i)?.[1];
      if (!name) continue;
      const element = this.document.createElement(name);
      for (const attribute of token.matchAll(/([a-z-]+)="([^"]*)"/g)) element.setAttribute(attribute[1], attribute[2]);
      stack.at(-1).append(element);
      if (!/^(input|br|img|meta)$/.test(name) && !token.endsWith("/>")) stack.push(element);
    }
  }
  append(...elements) {
    for (const element of elements) { element.parentNode = this; this.children.push(element); }
  }
  prepend(element) { element.parentNode = this; this.children.unshift(element); }
  replaceChildren(...elements) {
    for (const child of this.children) child.parentNode = null;
    this.children = [];
    this.append(...elements);
  }
  remove() {
    if (this.parentNode) this.parentNode.children = this.parentNode.children.filter((child) => child !== this);
    this.parentNode = null;
  }
  setAttribute(name, value) {
    this.attributes[name] = String(value);
    if (name === "id") this.id = String(value);
    if (name === "class") this.className = String(value);
    if (name.startsWith("data-")) this.dataset[name.slice(5).replace(/-([a-z])/g, (_, letter) => letter.toUpperCase())] = String(value);
  }
  matches(selector) {
    const tag = selector.match(/^[a-z]+/i)?.[0];
    if (tag && tag !== this.tagName) return false;
    const id = selector.match(/#([a-z0-9-]+)/i)?.[1];
    if (id && id !== this.id) return false;
    const className = selector.match(/\.([a-z0-9-]+)/i)?.[1];
    if (className && !this.className.split(/\s+/).includes(className)) return false;
    const attribute = selector.match(/\[([a-z0-9-]+)(?:=['"]?([^'"\]]+)['"]?)?\]/i);
    if (attribute) {
      const name = attribute[1];
      const actual = name.startsWith("data-") ? this.dataset[name.slice(5).replace(/-([a-z])/g, (_, letter) => letter.toUpperCase())] : this[name] ?? this.attributes[name];
      if (actual === undefined || (attribute[2] !== undefined && actual !== attribute[2])) return false;
    }
    return !selector.endsWith(":checked") || this.checked === true;
  }
  querySelectorAll(selector) {
    const tokens = selector.split(/\s+/);
    const last = tokens.at(-1);
    const matches = [];
    const visit = (element) => {
      for (const child of element.children) {
        if (child.matches(last) && (tokens.length === 1 || child.parentNode.matches(tokens[0]))) matches.push(child);
        visit(child);
      }
    };
    visit(this);
    return matches;
  }
  querySelector(selector) { return this.querySelectorAll(selector)[0] || null; }
  addEventListener(name, callback) { (this.listeners[name] ||= []).push(callback); }
  async emit(name) { for (const callback of this.listeners[name] || []) await callback({ target: this }); }
  click() { return this.emit("click"); }
  focus() { this.document.activeElement = this; }
}

function record() {
  const timestamp = "2026-01-01T00:00:00.000Z";
  return {
    schemaVersion: "1.0.0", exportedAt: timestamp,
    labs: Object.fromEntries(Array.from({ length: 28 }, (_, number) => [
      `LAB-${String(number).padStart(2, "0")}`,
      { status: "not-started", validationPassed: false, cleanupPassed: false, assessmentScore: null, updatedAt: timestamp }
    ]))
  };
}

function fixtures() {
  const labs = Array.from({ length: 25 }, (_, number) => {
    const labId = `LAB-${String(number + 1).padStart(2, "0")}`;
    return { labId, title: `Assessment ${number + 1}`, questionCount: 50, bankUrl: `${labId}.json`, pathUrl: `labs/${labId.slice(4)}-example/` };
  });
  const banks = Object.fromEntries(labs.map((lab) => [lab.labId, {
    schemaVersion: "1.0.0", labId: lab.labId, title: lab.title, pathUrl: lab.pathUrl,
    questions: Array.from({ length: 50 }, (_, number) => ({
      id: `${lab.labId}-Q${number + 1}`, stem: `Question ${number + 1} <script>alert(1)</script>`,
      options: { A: "Correct choice", B: "Wrong choice", C: "Third choice", D: "Fourth choice" },
      correctOption: "A", optionExplanations: { A: "Correct because of the mapped task.", B: "This is wrong.", C: "This is incomplete.", D: "This is unrelated." },
      objectiveIds: ["EXAMPLE-01"], reviewUrl: `${lab.pathUrl}#task-1`,
      sources: [{ title: "Official learning reference", url: "https://learn.microsoft.com/en-us/azure/" }]
    }))
  }]));
  return { index: { schemaVersion: "1.0.0", labs }, banks };
}

function browser({ initial = record(), fetcher, page = "practice/", storageFailure = false } = {}) {
  const document = { readyState: "complete", currentScript: { src: `${base}assets/quiz.js` }, activeElement: null, addEventListener() {} };
  document.createElement = (tag) => new Element(tag, document);
  document.body = document.createElement("body");
  document.querySelector = (selector) => document.body.querySelector(selector);
  const main = document.createElement("main");
  const content = document.createElement("article");
  content.className = "md-content__inner";
  main.append(content);
  document.body.append(main);
  if (page.startsWith("practice")) {
    const container = document.createElement("div");
    container.dataset.az104Quiz = "";
    for (const [tag, id] of [["select", "az104-quiz-lab"], ["button", "az104-quiz-load"], ["button", "az104-quiz-grade"], ["p", "az104-quiz-status"], ["p", "az104-quiz-count"], ["div", "az104-quiz-questions"], ["div", "az104-quiz-results"]]) {
      const element = document.createElement(tag);
      element.id = id;
      container.append(element);
    }
    content.append(container);
  }
  const storage = new Map(initial === null ? [] : [[key, JSON.stringify(initial)]]);
  const downloads = [];
  class BrowserURL extends URL {
    static createObjectURL(blob) { downloads.push(blob); return "blob:example"; }
    static revokeObjectURL() {}
  }
  const requests = [];
  const data = fixtures();
  const context = vm.createContext({
    document, URL: BrowserURL, AbortController, Blob,
    console: { warn() {} },
    fetch: async (url, options) => {
      requests.push(String(url));
      if (fetcher) return fetcher(String(url), options, data);
      const value = String(url).endsWith("index.json") ? data.index : data.banks[path.basename(String(url), ".json")];
      return { ok: true, json: async () => value };
    },
    window: {
      location: { href: base + page, pathname: new URL(base + page).pathname, reload() { context.reloads += 1; } },
      localStorage: {
        getItem: (name) => storage.get(name) ?? null,
        setItem: (name, value) => { if (storageFailure) throw new Error("Storage is full"); storage.set(name, value); },
        removeItem: (name) => storage.delete(name)
      },
      confirm: () => true, setTimeout: (callback) => callback()
    }, reloads: 0
  });
  vm.runInContext(progressScript, context);
  if (page.startsWith("practice")) vm.runInContext(quizScript, context);
  return { context, document, storage, data, requests, downloads,
    get: (id) => document.querySelector(`#${id}`), saved: () => JSON.parse(storage.get(key)) };
}

async function settle() { for (let index = 0; index < 8; index += 1) await new Promise((resolve) => setImmediate(resolve)); }
function answerAll(env, correct = 50) {
  const cards = env.get("az104-quiz-questions").querySelectorAll("fieldset");
  cards.forEach((card, index) => { card.querySelectorAll("input")[index < correct ? 0 : 1].checked = true; });
}

test("lazy bank loading renders 50 single-answer questions as plain text", async () => {
  const env = browser();
  await settle();
  assert.equal(env.requests.length, 2);
  assert.equal(env.get("az104-quiz-lab").children.length, 25);
  assert.equal(env.get("az104-quiz-questions").querySelectorAll("fieldset").length, 50);
  assert.equal(env.get("az104-quiz-questions").querySelectorAll("input").length, 200);
  assert.equal(env.get("az104-quiz-questions").querySelectorAll("script").length, 0);
  assert.match(env.get("az104-quiz-questions").textContent, /<script>alert\(1\)<\/script>/);
  assert.equal(env.get("az104-quiz-grade").disabled, false);
});

test("unanswered grading focuses the first missing answer and never writes progress", async () => {
  const env = browser();
  await settle();
  const before = env.storage.get(key);
  await env.get("az104-quiz-grade").click();
  assert.equal(env.storage.get(key), before);
  assert.match(env.get("az104-quiz-status").textContent, /50 remaining; question 1/);
  assert.equal(env.document.activeElement, env.get("az104-quiz-questions").querySelector("input"));
});

test("100% grading preserves imported completion and validation while showing all explanations", async () => {
  const initial = record();
  initial.labs["LAB-01"] = { ...initial.labs["LAB-01"], status: "complete", validationPassed: true, cleanupPassed: true, assessmentScore: 64 };
  const env = browser({ initial });
  await settle();
  answerAll(env);
  await env.get("az104-quiz-grade").click();
  const saved = env.saved();
  assert.equal(saved.labs["LAB-01"].assessmentScore, 100);
  for (const field of ["status", "validationPassed", "cleanupPassed"]) assert.equal(saved.labs["LAB-01"][field], initial.labs["LAB-01"][field]);
  assert.deepEqual(saved.labs["LAB-02"], initial.labs["LAB-02"]);
  assert.equal(saved.schemaVersion, "1.0.0");
  assert.equal(Object.keys(saved.labs).length, 28);
  assert.equal(env.get("az104-quiz-questions").querySelectorAll("dd").length, 200);
  assert.equal(env.get("az104-quiz-questions").querySelectorAll("a").length, 100);
  assert.equal(env.get("az104-quiz-questions").querySelector("a").href, `${base}labs/01-example/#task-1`);
  assert.equal(env.document.activeElement.tagName, "h2");
  assert.equal(env.get("az104-quiz-grade").disabled, true);
});

test("wrong answers produce percentage score, reload persistence, and no inferred completion", async () => {
  const env = browser();
  await settle();
  answerAll(env, 37);
  await env.get("az104-quiz-grade").click();
  assert.equal(env.saved().labs["LAB-01"].assessmentScore, 74);
  assert.equal(env.saved().labs["LAB-01"].status, "not-started");
  const restored = browser({ initial: env.saved(), page: "learner-progress/" });
  assert.equal(restored.saved().labs["LAB-01"].assessmentScore, 74);
  assert.match(restored.document.body.textContent, /Targeted review/);
});

test("save helper reads current storage instead of overwriting newer records", async () => {
  const env = browser();
  await settle();
  const newer = record();
  newer.labs["LAB-01"].validationPassed = true;
  newer.labs["LAB-01"].status = "in-progress";
  newer.labs["LAB-02"].assessmentScore = 88;
  env.storage.set(key, JSON.stringify(newer));
  answerAll(env, 0);
  await env.get("az104-quiz-grade").click();
  assert.equal(env.saved().labs["LAB-01"].assessmentScore, 0);
  assert.equal(env.saved().labs["LAB-01"].validationPassed, true);
  assert.equal(env.saved().labs["LAB-01"].status, "in-progress");
  assert.equal(env.saved().labs["LAB-02"].assessmentScore, 88);
});

test("manual lesson score entry remains compatible with later validation controls", async () => {
  const env = browser({ page: "labs/01-example/" });
  const input = env.get("az104-assessment-score");
  const buttons = env.document.body.querySelectorAll("button");
  const save = buttons.find((element) => element.textContent === "Save score");
  input.value = "";
  await save.click();
  assert.equal(env.saved().labs["LAB-01"].assessmentScore, null);
  input.value = "86";
  await save.click();
  await buttons.find((element) => element.textContent === "Record validation pass").click();
  assert.equal(env.saved().labs["LAB-01"].assessmentScore, 86);
  assert.equal(env.saved().labs["LAB-01"].validationPassed, true);
  assert.equal(env.saved().labs["LAB-01"].status, "in-progress");
});

test("every lesson action preserves quiz scores and newer records from another tab", async () => {
  for (const action of ["Mark in progress", "Record validation pass", "Record cleanup pass"]) {
    const env = browser({ page: "labs/01-example/" });
    env.context.window.az104Progress.saveAssessmentScore("LAB-01", 90);
    const newer = env.saved();
    newer.labs["LAB-01"].status = "in-progress";
    newer.labs["LAB-01"].validationPassed = action === "Record cleanup pass";
    newer.labs["LAB-01"].cleanupPassed = action === "Record validation pass";
    newer.labs["LAB-02"].assessmentScore = 88;
    env.storage.set(key, JSON.stringify(newer));
    await env.document.body.querySelectorAll("button").find((element) => element.textContent === action).click();
    const saved = env.saved();
    assert.equal(saved.labs["LAB-01"].assessmentScore, 90);
    assert.deepEqual(saved.labs["LAB-02"], newer.labs["LAB-02"]);
    assert.equal(saved.labs["LAB-01"].status, action === "Mark in progress" ? "in-progress" : "complete");
    if (action !== "Mark in progress") {
      assert.equal(saved.labs["LAB-01"].validationPassed, true);
      assert.equal(saved.labs["LAB-01"].cleanupPassed, true);
    }
  }
});

test("lesson actions refuse corrupt stored progress instead of replacing it", async () => {
  const env = browser({ page: "labs/01-example/" });
  env.storage.set(key, JSON.stringify({ ...record(), token: "forbidden" }));
  const before = env.storage.get(key);
  for (const action of ["Mark in progress", "Record validation pass", "Record cleanup pass"]) {
    await env.document.body.querySelectorAll("button").find((element) => element.textContent === action).click();
    assert.equal(env.storage.get(key), before);
  }
  assert.match(env.document.body.textContent, /Progress could not be saved/);
});

test("hands-on labs, invalid scores, and corrupt records are refused without replacement", () => {
  const env = browser({ page: "unrelated/" });
  const save = env.context.window.az104Progress.saveAssessmentScore;
  for (const labId of ["LAB-00", "LAB-26", "LAB-27", "LAB-28"]) assert.throws(() => save(labId, 80), /Only LAB-01/);
  for (const score of [-1, 101, 99.5, "80", null]) assert.throws(() => save("LAB-01", score), /whole numbers/);
  const corrupt = { ...record(), subscriptionId: "not-allowed" };
  env.storage.set(key, JSON.stringify(corrupt));
  const before = env.storage.get(key);
  assert.throws(() => save("LAB-01", 80), /unavailable or invalid/);
  assert.equal(env.storage.get(key), before);
});

test("a failed bank download and invalid links leave saved progress untouched", async () => {
  for (const invalidLink of [false, true]) {
    const env = browser({ fetcher: async (url, _options, data) => {
      if (url.endsWith("index.json")) return { ok: true, json: async () => data.index };
      if (!invalidLink) return { ok: false, status: 503 };
      data.banks["LAB-01"].questions[0].reviewUrl = "javascript:alert(1)";
      return { ok: true, json: async () => data.banks["LAB-01"] };
    } });
    const before = env.storage.get(key);
    await settle();
    assert.equal(env.storage.get(key), before);
    assert.equal(env.get("az104-quiz-grade").disabled, true);
    assert.match(env.get("az104-quiz-status").textContent, /could not be loaded/);
  }
});

test("unavailable storage keeps visible results without claiming the score was saved", async () => {
  const env = browser({ storageFailure: true });
  const before = env.storage.get(key);
  await settle();
  answerAll(env);
  await env.get("az104-quiz-grade").click();
  assert.equal(env.storage.get(key), before);
  assert.match(env.get("az104-quiz-results").textContent, /100%/);
  assert.match(env.get("az104-quiz-status").textContent, /could not be saved: Storage is full/);
});

test("a late response from a previously selected lab cannot replace the active bank", async () => {
  let releaseFirst;
  const env = browser({ fetcher: async (url, _options, data) => {
    if (url.endsWith("index.json")) return { ok: true, json: async () => data.index };
    if (url.endsWith("LAB-01.json")) return new Promise((resolve) => { releaseFirst = () => resolve({ ok: true, json: async () => data.banks["LAB-01"] }); });
    return { ok: true, json: async () => data.banks["LAB-02"] };
  } });
  await settle();
  env.get("az104-quiz-lab").value = "LAB-02";
  await env.get("az104-quiz-lab").emit("change");
  releaseFirst();
  await settle();
  assert.match(env.get("az104-quiz-status").textContent, /LAB-02: Assessment 2/);
  answerAll(env);
  await env.get("az104-quiz-grade").click();
  assert.equal(env.saved().labs["LAB-02"].assessmentScore, 100);
  assert.equal(env.saved().labs["LAB-01"].assessmentScore, null);
});

test("valid version 1 imports and exports remain compatible with scored records", async () => {
  const env = browser({ page: "learner-progress/" });
  const imported = record();
  imported.labs["LAB-25"].assessmentScore = 92;
  imported.labs["LAB-25"].status = "in-progress";
  const file = env.document.querySelector("input[type='file']");
  file.files = [{ size: 8000, text: async () => JSON.stringify(imported) }];
  await file.emit("change");
  assert.equal(env.saved().labs["LAB-25"].assessmentScore, 92);
  assert.equal(env.context.reloads, 1);
  const exportButton = env.document.body.querySelectorAll("button").find((element) => element.textContent === "Export JSON");
  await exportButton.click();
  const exported = JSON.parse(await env.downloads[0].text());
  assert.equal(exported.schemaVersion, "1.0.0");
  assert.deepEqual(exported.labs, env.saved().labs);
  assert.deepEqual(Object.keys(exported).sort(), ["exportedAt", "labs", "schemaVersion"]);
});

test("oversized and privacy-violating imports are rejected before storage changes", async () => {
  for (const oversized of [true, false]) {
    const env = browser({ page: "learner-progress/" });
    const before = env.storage.get(key);
    const file = env.document.querySelector("input[type='file']");
    let readFile = false;
    file.files = [{ size: oversized ? 256 * 1024 + 1 : 8000, text: async () => {
      readFile = true;
      return JSON.stringify({ ...record(), token: "forbidden" });
    } }];
    await file.emit("change");
    assert.equal(env.storage.get(key), before);
    assert.equal(env.context.reloads, 0);
    assert.equal(readFile, !oversized);
    assert.match(env.document.body.textContent, /Import rejected:/);
  }
});
