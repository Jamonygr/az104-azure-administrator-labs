# AZ-104 blueprint research baseline

Skills measured from: **2026-04-17**
Primary authority: [Microsoft's AZ-104 study guide](https://learn.microsoft.com/en-us/credentials/certifications/resources/study-guides/az-104)
Archived evidence: [Internet Archive capture of the study guide](https://web.archive.org/web/20261012205028/https://learn.microsoft.com/en-us/credentials/certifications/resources/study-guides/az-104)

## Research result

The current English-language study guide defines five weighted skill domains, 15 skill groups, and 82 objective bullets. `curriculum/blueprint.yml` is the machine-readable source of truth for this repository; `docs/objective-map.md` is its learner-readable lab mapping.

Microsoft notes that the bullets illustrate how each skill is assessed, related topics may also appear, and most questions cover generally available features. Preview features may appear when commonly used. The repository therefore treats these objectives as a minimum coverage boundary rather than a promise about the exact contents or distribution of exam questions.

## Verification notes

| Pass | Result | Notes |
|---|---|---|
| Baseline | Blueprint captured | The live study guide showed the skills-measured version recorded above, and its 82 objectives were recorded in `curriculum/blueprint.yml`. |
| Re-verification | Blueprint unchanged | The live page had been republished and rendered only the superseded skills list and its older change log in every locale checked. The current objective text was therefore compared bullet by bullet against the two most recent Internet Archive captures: all 82 objectives, 15 group headings, 5 domain names, and 5 weights match the blueprint exactly. No newer skills-measured version, future change log, or retirement notice was found, so the regression is recorded as a Microsoft publishing error rather than an exam update. |

Two non-objective changes were confirmed in the current version and are now reflected in the learner documentation:

- The audience profile lists experience with "Azure Resource Manager templates or Bicep files" (previously "Azure Resource Manager templates"); see `docs/prerequisites.md`.
- Microsoft directs learners to the practice assessment on AI Skills Navigator and states that the legacy Microsoft Learn practice assessment is no longer being updated; see `docs/study-plan.md` and `docs/assessment-guide.md`.

Neither change adds, removes, renames, or reorders an official objective, so objective IDs, lab mappings, and assessment mappings are unchanged.

## Skills at a glance

| Domain ID | Official skill domain | Weight | Groups | Objectives | Primary labs |
|---|---|---:|---:|---:|---|
| `IG` | Manage Azure identities and governance | 20–25% | 3 | 15 | 01–05, 26–27 |
| `ST` | Implement and manage storage | 15–20% | 3 | 17 | 06–09, 26 |
| `CP` | Deploy and manage Azure compute resources | 20–25% | 4 | 24 | 10–16, 26 |
| `NW` | Implement and manage virtual networking | 15–20% | 3 | 13 | 17–21, 26–27 |
| `MR` | Monitor and maintain Azure resources | 10–15% | 2 | 13 | 21–27 |
| **Total** |  |  | **15** | **82** | **28 labs including Lab 00** |

Weights are ranges published by Microsoft. They must not be converted into an assumed question count.

## Skill groups

| Group ID | Official skill group | Objectives | Core lab coverage |
|---|---|---:|---|
| `IG-USERS` | Manage Microsoft Entra users and groups | 5 | Labs 01–02 |
| `IG-ACCESS` | Manage access to Azure resources | 3 | Lab 03; Capstones 26–27 |
| `IG-GOVERN` | Manage Azure subscriptions and governance | 7 | Labs 00, 04–05; Capstones 26–27 |
| `ST-ACCESS` | Configure access to storage | 5 | Labs 06–07, 09, 19 |
| `ST-ACCOUNTS` | Configure and manage storage accounts | 5 | Labs 06, 08–09; Capstone 26 |
| `ST-DATA` | Configure Azure Files and Azure Blob Storage | 7 | Labs 08–09 |
| `CP-IAC` | Automate deployment of resources by using ARM templates or Bicep files | 5 | Lab 10; Capstone 26 |
| `CP-VM` | Create and configure virtual machines | 7 | Labs 11–12; Capstone 26 |
| `CP-CONTAINERS` | Provision and manage containers in the Azure portal | 4 | Labs 13–14 |
| `CP-APP` | Create and configure Azure App Service | 8 | Labs 15–16, 19 |
| `NW-VNET` | Configure and manage virtual networks in Azure | 5 | Labs 17–18, 21; Capstones 26–27 |
| `NW-SECURE` | Configure secure access to virtual networks | 5 | Labs 18–20; Capstones 26–27 |
| `NW-DNSLB` | Configure name resolution and load balancing | 3 | Labs 16, 20–21; Capstones 26–27 |
| `MR-MONITOR` | Monitor resources in Azure | 6 | Labs 21–23; Capstones 26–27 |
| `MR-RECOVERY` | Implement backup and recovery | 7 | Labs 24–25; Capstone 27 |

## Stable objective IDs

Microsoft publishes objective text but not repository-safe identifiers. This project assigns IDs in `DOMAIN-GROUP-NN` form:

- `IG`, `ST`, `CP`, `NW`, and `MR` identify the five official domains.
- The middle segment identifies the official skill group, such as `USERS`, `IAC`, or `SECURE`.
- The two-digit suffix follows the objective order in the 2026-04-17 English study guide.

These IDs remain stable within this blueprint version. If Microsoft changes an objective, a future research pass must record the change rather than silently reusing an ID for unrelated text.

Lab 00 also has five `FD-*` foundation outcomes for tools, Azure context, cost gating, safe state handling, and cleanup. They are deliberately stored outside `domains` and are **not** included in the official count of 82.

## Curriculum interpretation

- Azure CLI hosted in PowerShell is the canonical execution surface for each lab. Microsoft Graph is called with `az rest`; Bicep, AzCopy, and KQL are used where an objective requires them.
- The official containers group retains the words “in the Azure portal.” This curriculum implements and validates those objectives with Azure CLI hosted in PowerShell so the learner workflow remains reproducible and command-first.
- Some tenant-wide, licensed, paid, quota-sensitive, or long-running objectives need a gated or partial path. Their objective remains mapped even when live execution requires separate authorization.
- Capstone mappings reinforce earlier teaching; they do not replace the primary instructional lab for an objective.
- The objective map covers every official bullet at least once. Lab metadata and assessment questions will reference the same IDs so coverage can be tested automatically.

## Change-control procedure

Before a release or whenever Microsoft announces an exam update:

1. Reopen the English study guide and certification page.
2. Confirm the effective date, five weights, group headings, and every objective bullet.
3. If the live page shows an older skills-measured version than `curriculum/blueprint.yml` records, compare the page against the most recent Internet Archive capture, record the discrepancy in the verification notes and the source register, and keep the blueprint on the newest officially published version. Only a newer skills list or change log counts as an exam update.
4. Compare the new text against `curriculum/blueprint.yml`.
5. Update the source register.
6. Re-run exact counts, uniqueness checks, lab coverage checks, and assessment coverage checks.
7. Document additions, removals, renames, or reordered objectives in the release notes.

## Research boundaries

The blueprint is not an exam dump, prediction model, or substitute for Microsoft's current study guide. Lab scenarios and assessment questions must be original. Official documentation supports technical claims and answer rationales, while the study guide alone controls which bullets count as official AZ-104 objectives for this baseline.
