# Assessment authoring and learner guide

Labs 01–25 each contain a 50-question knowledge check. Lab 00 and Capstones 26–27 remain hands-on exercises without separate question banks. The complete bank contains 1,250 four-option, single-answer questions and assesses all 82 official AZ-104 objectives.

## Learner workflow

1. Complete the guided tasks, validation, and break/fix exercise in the lab README.
2. Answer all 50 questions in `assessment/QUESTIONS.md` without opening the answer key.
3. Score one point for each correct response.
4. Use each missed question's remediation link in `assessment/ANSWERS.md` to repeat the mapped task and checkpoint.
5. Retry the assessment after reviewing the relevant Microsoft Learn sources.
6. Once every lab bank is in the mastery band, take [Microsoft's official practice assessment on AI Skills Navigator](https://aka.ms/AZ104-PA) as an independent readiness check. The repository banks are original, are not derived from any Microsoft practice assessment, and do not predict live exam items; see the [study plan](study-plan.md#exam-readiness) for how to use the two together.

Use these learning bands; they are not claims about Microsoft's exam scoring:

- **43–50 (85–100%): Mastery.** Continue and revisit missed topics during final review.
- **35–42 (70–84%): Targeted review.** Repeat every task linked from a missed question.
- **0–34 (below 70%): Rebuild.** Repeat the full lab, including validation and break/fix, before retrying.

## Locked per-lab contract

Every assessment-enabled lab contains:

- 15 foundational questions;
- 25 applied implementation or validation questions;
- 10 advanced troubleshooting or design questions;
- IDs contiguous from `LABxx-Q01` through `LABxx-Q50`;
- four distinct technical options with exactly one best answer;
- 12 or 13 correct answers in each A–D position, in a nonperiodic order;
- objective mappings from the lab's declared AZ-104 domain;
- checkpoint IDs and a matching `#task-1` through `#task-5` remediation anchor;
- a specific explanation for every option;
- named Microsoft Learn sources and an individual source-review date.

`assessment/questions.yml` is the authored source of truth. `QUESTIONS.md` deliberately omits answers, rationales, objective mappings, and source metadata. `ANSWERS.md` repeats each stem and option, marks every option correct or incorrect, explains the result, and links back to the relevant guided task.

## Question record

```yaml
- id: "LAB14-Q01"
  objectiveIds:
    - "CP-CONTAINERS-03"
  checkpointIds:
    - "LAB14-CP01"
  remediationAnchor: "#task-1"
  difficulty: "foundational"
  stem: "Which statement accurately describes an Azure Container Apps revision?"
  options:
    A: "A revision is an immutable snapshot of an app version."
    B: "A revision is the virtual network boundary for several apps."
    C: "A revision is a mutable alias for one container image tag."
    D: "A revision is the Log Analytics workspace used by an environment."
  correctOption: "A"
  optionExplanations:
    A: "Revision-scope changes create a new immutable revision rather than editing this one."
    B: "The managed environment, not a revision, provides the shared network boundary."
    C: "A revision captures versioned configuration and is not merely a mutable image alias."
    D: "The workspace is a logging destination and does not represent an application version."
  sources:
    - title: "Azure Container Apps revisions"
      url: "https://learn.microsoft.com/en-us/azure/container-apps/revisions"
  lastVerified: "2026-08-31"
```

## Authoring quality rules

- Write a new operational decision, validation need, failure, or design tradeoff for every item. Do not create variants by adding context prefixes, rotating options, or cloning another stem.
- Keep all four choices grammatically compatible with the stem and technically plausible within the lab topic. Do not use joke answers, overlapping choices, or an obvious outlier.
- Explain why each option is correct or incorrect in the context of that question. Avoid reusable rationale triads such as “too broad,” “not recommended,” or “does not satisfy the requirement” without technical reasoning.
- Map each item to the objective it actually assesses, not merely an objective from the same domain.
- Link remediation to the checkpoint that teaches and verifies the tested behavior. The checkpoint suffix and task-anchor number must agree.
- Prefer conceptual Microsoft Learn articles, Azure CLI references, and REST documentation. Do not use exam dumps, Portal walkthroughs, or Azure PowerShell procedural sources.
- Give every source a descriptive article title. Review the source's technical relevance and URL before updating `lastVerified`.
- Do not expose answer positions, rationales, or metadata in `QUESTIONS.md`.

## Rendering and validation

The historical renderer entrypoint remains compatible, but it no longer expands assessments or modifies question data:

```powershell
python tools/expand_assessments.py
python tools/expand_assessments.py --check
python tools/validate_assessments.py
```

The renderer refuses incomplete or invalid banks before updating Markdown. The assessment validator checks schema shape, counts, IDs, difficulty and answer balance, objective coverage, checkpoint mappings, distinct options, exact and near-duplicate stems, reused option sets and rationales, predictable answer periods, source titles and surfaces, review dates, and legacy generic rationales.

Source URLs are verified separately during editorial review so continuous integration remains deterministic and offline.
