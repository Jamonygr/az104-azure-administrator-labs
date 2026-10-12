(() => {
  "use strict";

  const script = document.currentScript;
  if (!script?.src) return;
  const scriptUrl = new URL(script.src);
  const siteRoot = new URL("../", scriptUrl);
  const indexUrl = new URL("quiz/index.json", scriptUrl);
  const answerKeys = ["A", "B", "C", "D"];
  const labPattern = /^LAB-(?:0[1-9]|1[0-9]|2[0-5])$/;

  const textElement = (tag, text, className) => {
    const element = document.createElement(tag);
    element.textContent = text;
    if (className) element.className = className;
    return element;
  };

  function requiredText(value) {
    return typeof value === "string" && value.trim().length > 0;
  }

  function validateIndex(index) {
    if (index?.schemaVersion !== "1.0.0" || !Array.isArray(index.labs) || index.labs.length !== 25) {
      throw new Error("The assessment catalog is unavailable or invalid.");
    }
    const ids = new Set();
    for (const lab of index.labs) {
      const number = lab?.labId?.slice(4);
      if (!labPattern.test(lab?.labId) || ids.has(lab.labId) || !requiredText(lab.title) ||
          lab.questionCount !== 50 || lab.bankUrl !== `${lab.labId}.json` ||
          !new RegExp(`^labs/${number}-[a-z0-9-]+/$`).test(lab.pathUrl)) {
        throw new Error("The assessment catalog contains an invalid lab.");
      }
      ids.add(lab.labId);
    }
    return index.labs;
  }

  function localReviewUrl(value, lab) {
    if (!requiredText(value) || !value.startsWith(lab.pathUrl)) {
      throw new Error("An assessment has an invalid lesson reference.");
    }
    const url = new URL(value, siteRoot);
    const lesson = new URL(lab.pathUrl, siteRoot);
    if (url.origin !== siteRoot.origin || url.pathname !== lesson.pathname || !/^#[a-z0-9-]+$/.test(url.hash)) {
      throw new Error("An assessment has an invalid lesson reference.");
    }
    return url.href;
  }

  function officialSourceUrl(value) {
    const url = new URL(value);
    if (url.protocol !== "https:" || url.hostname !== "learn.microsoft.com" || url.username || url.password) {
      throw new Error("An assessment has an invalid official reference.");
    }
    return url.href;
  }

  function validateBank(bank, lab) {
    if (bank?.schemaVersion !== "1.0.0" || bank.labId !== lab.labId || bank.pathUrl !== lab.pathUrl ||
        !Array.isArray(bank.questions) || bank.questions.length !== 50) {
      throw new Error("This lab's assessment is unavailable or invalid.");
    }
    const ids = new Set();
    for (const question of bank.questions) {
      if (!requiredText(question.id) || ids.has(question.id) || !requiredText(question.stem) ||
          !answerKeys.includes(question.correctOption) || !question.options ||
          Object.keys(question.options).length !== 4 || !question.optionExplanations ||
          Object.keys(question.optionExplanations).length !== 4 ||
          !answerKeys.every((key) => requiredText(question.options[key]) && requiredText(question.optionExplanations[key])) ||
          !Array.isArray(question.sources) || question.sources.length === 0) {
        throw new Error("This lab's assessment contains an invalid question.");
      }
      localReviewUrl(question.reviewUrl, lab);
      for (const source of question.sources) {
        if (!requiredText(source.title) || !requiredText(source.url)) {
          throw new Error("An assessment has an invalid official reference.");
        }
        officialSourceUrl(source.url);
      }
      ids.add(question.id);
    }
    return bank;
  }

  async function fetchJson(url, signal) {
    const response = await fetch(url, { credentials: "omit", signal });
    if (!response.ok) throw new Error(`The assessment download returned HTTP ${response.status}.`);
    return response.json();
  }

  function render() {
    const container = document.querySelector("[data-az104-quiz]");
    if (!container || container.dataset.az104QuizReady === "true") return;
    container.dataset.az104QuizReady = "true";
    const select = container.querySelector("#az104-quiz-lab");
    const loadButton = container.querySelector("#az104-quiz-load");
    const gradeButton = container.querySelector("#az104-quiz-grade");
    const status = container.querySelector("#az104-quiz-status");
    const count = container.querySelector("#az104-quiz-count");
    const questions = container.querySelector("#az104-quiz-questions");
    const results = container.querySelector("#az104-quiz-results");
    if (![select, loadButton, gradeButton, status, count, questions, results].every(Boolean)) return;
    let labs = [];
    let activeBank = null;
    let activeLab = null;
    let requestId = 0;
    let controller = null;
    let graded = false;
    const questionCards = [];

    const selectedAnswers = () => questionCards.map((card) =>
      card.querySelector("input[type='radio']:checked")?.value || null
    );

    function updateCount() {
      const answered = selectedAnswers().filter(Boolean).length;
      count.textContent = `${answered} of 50 questions answered.`;
      return answered;
    }

    function displayQuestions(bank) {
      questions.replaceChildren();
      questionCards.length = 0;
      bank.questions.forEach((question, index) => {
        const card = document.createElement("fieldset");
        card.className = "az104-quiz-question";
        const legend = textElement("legend", `${index + 1}. ${question.stem}`);
        card.append(legend);
        if (Array.isArray(question.objectiveIds)) {
          card.append(textElement("p", `Objectives: ${question.objectiveIds.join(", ")}`, "az104-quiz-meta"));
        }
        const options = document.createElement("div");
        options.className = "az104-quiz-options";
        for (const key of answerKeys) {
          const label = document.createElement("label");
          label.className = "az104-quiz-option";
          const input = document.createElement("input");
          input.type = "radio";
          input.name = `az104-${bank.labId}-question-${index}`;
          input.value = key;
          input.required = true;
          input.addEventListener("change", updateCount);
          label.append(input, textElement("span", `${key}. ${question.options[key]}`));
          options.append(label);
        }
        card.append(options);
        questions.append(card);
        questionCards.push(card);
      });
      updateCount();
    }

    async function loadBank() {
      const currentRequest = ++requestId;
      controller?.abort();
      controller = new AbortController();
      activeBank = null;
      activeLab = null;
      graded = false;
      gradeButton.disabled = true;
      loadButton.disabled = true;
      loadButton.textContent = "Load selected lab";
      questions.replaceChildren();
      questionCards.length = 0;
      results.replaceChildren();
      results.hidden = true;
      count.textContent = "";
      const lab = labs.find((item) => item.labId === select.value);
      if (!lab) {
        status.textContent = "Choose a lab with a practice assessment.";
        loadButton.disabled = false;
        return;
      }
      status.textContent = `Loading ${lab.labId}'s 50 questions…`;
      try {
        const bank = validateBank(await fetchJson(new URL(lab.bankUrl, indexUrl), controller.signal), lab);
        if (currentRequest !== requestId || !container.isConnected || select.value !== lab.labId) return;
        activeBank = bank;
        activeLab = lab;
        displayQuestions(bank);
        gradeButton.disabled = false;
        status.textContent = `${lab.labId}: ${lab.title}. Answer all 50 questions before grading.`;
      } catch (error) {
        if (currentRequest !== requestId || !container.isConnected) return;
        status.textContent = `Questions could not be loaded. ${error.message} Select the lab again or use Load selected lab to retry. Your saved progress has not changed.`;
      } finally {
        if (currentRequest === requestId && container.isConnected) loadButton.disabled = false;
      }
    }

    function grade() {
      if (!activeBank || !activeLab || graded) return;
      const answers = selectedAnswers();
      const missing = answers.findIndex((answer) => answer === null);
      if (missing !== -1) {
        const answered = updateCount();
        status.textContent = `Answer all 50 questions before grading. ${50 - answered} remaining; question ${missing + 1} needs an answer.`;
        questionCards[missing].querySelector("input[type='radio']")?.focus();
        return;
      }
      const correct = activeBank.questions.reduce((total, question, index) =>
        total + (answers[index] === question.correctOption ? 1 : 0), 0
      );
      const score = Math.round(correct / 50 * 100);
      results.replaceChildren();
      const heading = textElement("h2", `${correct} of 50 correct — ${score}%`);
      heading.tabIndex = -1;
      results.append(heading);
      results.append(textElement("p", score >= 85 ? "Mastery: continue your learning path." :
        score >= 70 ? "Targeted review: revisit the mapped lesson tasks." : "Repeat the mapped lesson tasks, then try again."));
      let saveMessage;
      try {
        if (!window.az104Progress?.saveAssessmentScore) throw new Error("Browser progress is unavailable.");
        window.az104Progress.saveAssessmentScore(activeLab.labId, score);
        saveMessage = "Score saved in this browser. Lab status, deployment validation, and cleanup results are unchanged.";
      } catch (error) {
        saveMessage = `Your result is shown below, but the score could not be saved: ${error.message}`;
      }
      results.append(textElement("p", saveMessage));
      activeBank.questions.forEach((question, index) => {
        const correctAnswer = answers[index] === question.correctOption;
        const card = questionCards[index];
        card.classList.add(correctAnswer ? "az104-quiz-correct" : "az104-quiz-incorrect");
        card.querySelectorAll("input[type='radio']").forEach((input) => { input.disabled = true; });
        const feedback = document.createElement("div");
        feedback.className = "az104-quiz-feedback";
        feedback.append(textElement("p", `${correctAnswer ? "Correct" : "Review needed"}. Your answer: ${answers[index]}; correct answer: ${question.correctOption}.`));
        const explanations = document.createElement("dl");
        for (const key of answerKeys) {
          explanations.append(textElement("dt", `${key}${key === question.correctOption ? " — correct answer" : ""}`),
            textElement("dd", question.optionExplanations[key]));
        }
        feedback.append(explanations);
        const remediation = textElement("a", "Review the mapped lesson task");
        remediation.href = localReviewUrl(question.reviewUrl, activeLab);
        feedback.append(remediation);
        const sourceList = document.createElement("ul");
        for (const source of question.sources) {
          const item = document.createElement("li");
          const link = textElement("a", source.title);
          link.href = officialSourceUrl(source.url);
          item.append(link);
          sourceList.append(item);
        }
        feedback.append(textElement("p", "Official references:"), sourceList);
        card.append(feedback);
      });
      results.hidden = false;
      graded = true;
      gradeButton.disabled = true;
      loadButton.textContent = "Try this lab again";
      status.textContent = `Assessment graded: ${correct} of 50 correct, ${score}%. ${saveMessage}`;
      heading.focus();
    }

    select.disabled = true;
    loadButton.disabled = true;
    gradeButton.disabled = true;
    select.addEventListener("change", loadBank);
    loadButton.addEventListener("click", loadBank);
    gradeButton.addEventListener("click", grade);
    status.textContent = "Loading the practice assessment catalog…";
    fetchJson(indexUrl).then((index) => {
      if (!container.isConnected) return;
      labs = validateIndex(index);
      select.replaceChildren();
      for (const lab of labs) {
        const option = textElement("option", `${lab.labId} — ${lab.title}`);
        option.value = lab.labId;
        select.append(option);
      }
      const requested = new URL(window.location.href).searchParams.get("lab");
      select.value = labs.some((lab) => lab.labId === requested) ? requested : labs[0].labId;
      select.disabled = false;
      loadButton.disabled = false;
      return loadBank();
    }).catch((error) => {
      if (!container.isConnected) return;
      status.textContent = `The assessment catalog could not be loaded. ${error.message} Reload this page to retry. Your saved progress has not changed.`;
    });
  }

  if (typeof document$ !== "undefined") {
    document$.subscribe(render);
  } else if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", render);
  } else {
    render();
  }
})();
