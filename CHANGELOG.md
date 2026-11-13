# Changelog

All notable changes to this curriculum are documented here.

## 2026-10-12 — More illustrated lesson guides

### Added

- Thirty-six original teaching visuals: 28 checkpoint roadmaps, five setup illustrations, and three safety, troubleshooting, and cleanup guides.
- Contextual illustrations within every lab, with captions and full-size links.
- A visual gallery linking each guide to its lesson, plus deterministic SVG and curriculum-alignment checks.

## 2026-10-12 — Illustrated learning website

### Added

- An original cloud cover and five domain illustrations with a black default theme and light-mode toggle.
- A responsive homepage with all 28 lab cards, curriculum statistics, and learning pathways.
- Interactive 50-question assessments for Labs 01–25, explanations, official references, and task remediation links.
- Automatic percentage scores integrated with the existing private learner-progress format.
- Accessible service icons and refreshed SVG architecture diagrams, generated from the unchanged Mermaid sources.

### Fixed

- The quality workflow dependency-cache path and checksum-verified tool installation.
- Documentation publishing now depends on the reusable repository quality checks.
- Search tokenization and lab result titles.
- Lesson progress actions preserve quiz scores saved in other tabs.

## Unreleased

### Added

- Current AZ-104 blueprint baseline dated April 17, 2026.
- Blueprint re-verification: all 82 official objectives, 15 skill groups, five domains, and five weights were compared bullet by bullet against archived Internet Archive captures of Microsoft's study guide and found identical, so objective IDs, lab mappings, and assessment mappings are unchanged. The verification notes are recorded in `docs/research/az-104-blueprint.md`.
- `SRC-EXAM-GUIDE-ARCHIVE` and `SRC-PRACTICE-ASSESSMENT` entries in the source register, plus `archivedSourceUrl` metadata in `curriculum/blueprint.yml`.
- Exam-readiness guidance in the study plan and assessment guide pointing to Microsoft's official AZ-104 practice assessment on AI Skills Navigator, which replaces the legacy Microsoft Learn practice assessment that Microsoft no longer updates.
- Twenty-eight self-contained learning environments with Azure CLI commands hosted in PowerShell, lifecycle contracts, diagrams, and solution notes.
- Preview-first `Preflight.ps1`, `Setup.ps1`, `Validate.ps1`, and `Cleanup.ps1` interfaces, including cost and tenant-change gates.
- Strict schemas for lab metadata, the lab catalog, run state, deployment validation, cleanup results, assessments, and private learner progress.
- A marked-section, data-driven lab renderer with drift checking.
- Full assessment coverage for all 82 official objectives in the April 17, 2026 AZ-104 blueprint.
- Exactly 50 questions in every assessment-enabled lab, with separate learner and answer files in Labs 01–25.
- A searchable Material for MkDocs site, private browser-local progress, JSON import/export, learning pathways, and generated domain dashboards.
- A cross-platform initializer, blocking readiness report, pinned development container, VS Code tasks, and GitHub Pages workflow.
- Deterministic accessible SVG rendering from each lab's Mermaid architecture source.

### Changed

- Prerequisites now restate Microsoft's current audience profile, which lists experience with Azure Resource Manager templates or Bicep files alongside PowerShell, Azure CLI, the Azure portal, and Microsoft Entra ID.
- The source policy and change-control procedure now require comparing the live study guide against its most recent archive capture when the live page shows an older skills-measured version, and forbid downgrading the blueprint because of a page regression. This was triggered by Microsoft's live study guide being republished with only a superseded skills list; no newer exam update was announced, and the blueprint is unchanged.
- Every core checkpoint now includes the direct learner command, expected state, positive and negative checks, retained evidence, retry guidance, and cleanup dependency.
- Architecture Mermaid/SVG files are the only instructional visuals.
- Learner evidence is redacted command output and structured lifecycle results; no browser procedure or screenshot evidence is required.
- Complete lifecycle script implementations are synchronized into every lab README after the guided tasks.
- The assessment expander now renders authored records and refuses incomplete or duplicated banks.
- The master question index is a compact per-lab and objective-coverage dashboard.

### Fixed

- Setup persists every returned managed-object ID immediately so cleanup can recover after a partial failure.
- Cleanup verifies run ownership before mutation, follows declared dependencies, is idempotent, and reports expected retained or soft-deleted objects explicitly.
- Validation reports `pass` only when every required checkpoint passes and uses `partial` when an optional gate is skipped.
- Generated lab READMEs render each checkpoint as a distinct learner-first section.
