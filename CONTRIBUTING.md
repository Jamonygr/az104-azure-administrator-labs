# Contributing

Contributions should preserve objective traceability, safe Azure behavior, learner clarity, and lab portability.

## Before opening a change

- Use current official Microsoft documentation.
- Do not copy exam dumps or proprietary practice questions.
- Do not commit tenant IDs, subscription IDs, personal email addresses, secrets, SAS tokens, keys, or credentials.
- Keep every lab self-contained; no runtime import from another lab.
- Make validation read-only and cleanup idempotent.
- Update `lastVerified` metadata for changed technical instructions.

## Validation

Run:

```powershell
python tools/validate_repository.py --release
python tools/generate_labs.py --check
python tools/render_diagrams.py --check
python tools/generate_indexes.py --check
python tools/validate_assessments.py
python tools/expand_assessments.py --check
python tools/build_docs_site.py --check
node --check docs/site-assets/quiz.js
node --test tools/tests/browser_learning.test.cjs
$pester = Invoke-Pester -Path labs -Output Detailed -PassThru
if ($pester.FailedCount -gt 0) { throw "$($pester.FailedCount) Pester test(s) failed." }
python tools/build_docs_site.py
python -m mkdocs build --strict
python tools/build_docs_site.py --check-built-site site
```

Run the relevant Markdown, PowerShell, Bicep, diagram, site, and assessment checks for the files changed. Live Azure testing requires a dedicated sandbox and explicit authorization.

## Architecture diagrams

Treat each `diagrams/architecture.mmd` file as the editable source. The repository renderer supports the curriculum's documented Mermaid `flowchart LR` subset and produces a byte-stable SVG with a title, description, and source hash without using a browser or network dependency.

```powershell
python tools/render_diagrams.py
python tools/render_diagrams.py --check
```

Commit the generated `architecture.svg` beside its source. CI fails when the source and SVG differ or when a diagram uses unsupported syntax.

## Website and artwork

Edit the homepage in `docs/site/index.md`; its curriculum cards and quiz data are staged from the validated catalog and question banks. Keep lesson paths, task anchors, and the version 1.0.0 progress export compatible.

Store original artwork in `docs/site-assets/illustrations`, document generated cover prompts in [artwork notes](ASSET_NOTES.md), and provide descriptive alternative text, captions, and full-size links. Review the black and light themes at desktop, tablet, and phone widths, including keyboard focus and reduced motion.

## Assessment contributions

Labs 01–25 each have exactly 50 original four-option, single-answer questions with a 15 foundational / 25 applied / 10 advanced mix. Map every question to objective and checkpoint IDs plus a valid task anchor, explain the concrete consequence of every option, cite named Microsoft Learn sources, record an individual review date, and avoid cloned stems, generic rationales, reused option sets, or predictable answer patterns. Lab 00 and Capstones 26–27 remain hands-on only.
