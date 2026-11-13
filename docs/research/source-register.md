# AZ-104 source register

Only first-party Microsoft sources are authoritative for the exam blueprint and technical lab claims. The current English study guide is the sole source used to count official objectives; supporting sources add role context, learning paths, and tool guidance.

## Blueprint and credential authorities

| Source ID | Source | Purpose | Verified | Notes |
|---|---|---|---|---|
| `SRC-EXAM-GUIDE` | [Study guide for Exam AZ-104: Microsoft Azure Administrator](https://learn.microsoft.com/en-us/credentials/certifications/resources/study-guides/az-104) | Canonical domain weights, skill groups, and objective text | 2026-11-07 | The blueprint baseline is the skills-measured version recorded as `blueprintEffectiveDate` in `curriculum/blueprint.yml`. At re-verification the live page had been republished and rendered only the superseded skills list and its older change log in every locale checked. No newer skills-measured version or future change log was published, so this is treated as a Microsoft publishing regression, not an exam update. The blueprint is unchanged; recheck the live page before the next release. |
| `SRC-EXAM-GUIDE-ARCHIVE` | [Internet Archive capture of the AZ-104 study guide](https://web.archive.org/web/20261012205028/https://learn.microsoft.com/en-us/credentials/certifications/resources/study-guides/az-104) | Archived evidence of the current skills-measured text used for bullet-by-bullet comparison | 2026-11-07 | Matches `curriculum/blueprint.yml` on all 82 objective bullets, 15 group headings, 5 domain names, and 5 weights. The preceding capture shows the same version, and the one before it shows the previous version. Evidence only; the live Microsoft page remains the authority once it is corrected. |
| `SRC-CERTIFICATION` | [Microsoft Certified: Azure Administrator Associate](https://learn.microsoft.com/en-us/credentials/certifications/azure-administrator/) | Audience, role, exam, renewal, and credential context | 2026-11-07 | Skills content on this page is rendered client-side, so the study guide remains the objective-count source. |
| `SRC-PRACTICE-ASSESSMENT` | [Microsoft practice assessment for AZ-104 on AI Skills Navigator](https://aka.ms/AZ104-PA) | Official learner-facing exam-readiness check referenced from the study plan and assessment guide | 2026-11-07 | Microsoft's study guide now directs learners to the AI Skills Navigator practice assessment and states that the legacy Microsoft Learn practice assessment (`https://aka.ms/AZ104-LearnPA`) is no longer being updated. Sign-in is required. Supporting source only: never used as a question source, and no wording from it may appear in this repository's banks. |
| `SRC-COURSE` | [Course AZ-104T00-A: Microsoft Azure Administrator](https://learn.microsoft.com/en-us/training/courses/az-104t00) | Instructor-led course context and related training | 2026-08-30 | Supporting source only; does not control objective counts |

## Microsoft Learn paths

| Source ID | Source | Curriculum use | Verified |
|---|---|---|---|
| `SRC-LP-PREREQ` | [AZ-104: Prerequisites for Azure administrators](https://learn.microsoft.com/en-us/training/paths/az-104-administrator-prerequisites/) | Lab 00 foundation and learner prerequisites | 2026-08-30 |
| `SRC-LP-IDENTITY` | [AZ-104: Manage identities and governance in Azure](https://learn.microsoft.com/en-us/training/paths/az-104-manage-identities-governance/) | Identity and governance domain | 2026-08-30 |
| `SRC-LP-STORAGE` | [AZ-104: Implement and manage storage in Azure](https://learn.microsoft.com/en-us/training/paths/az-104-manage-storage/) | Storage domain | 2026-08-30 |
| `SRC-LP-COMPUTE` | [AZ-104: Deploy and manage Azure compute resources](https://learn.microsoft.com/en-us/training/paths/az-104-manage-compute-resources/) | Compute domain | 2026-08-30 |
| `SRC-LP-NETWORK` | [AZ-104: Configure and manage virtual networks for Azure administrators](https://learn.microsoft.com/en-us/training/paths/az-104-manage-virtual-networks/) | Networking domain | 2026-08-30 |
| `SRC-LP-MONITOR` | [AZ-104: Monitor and back up Azure resources](https://learn.microsoft.com/en-us/training/paths/az-104-monitor-backup-resources/) | Monitoring and recovery domain | 2026-08-30 |

## Command and automation authorities

| Source ID | Source | Curriculum use | Verified |
|---|---|---|---|
| `SRC-AZ-CLI` | [Azure CLI documentation](https://learn.microsoft.com/en-us/cli/azure/) | Azure CLI command syntax and reference | 2026-08-30 |
| `SRC-AZ-REST` | [Azure CLI REST command](https://learn.microsoft.com/en-us/cli/azure/reference-index#az-rest) | Microsoft Graph and Azure REST operations not exposed by a dedicated command group | 2026-08-30 |
| `SRC-BICEP` | [Bicep documentation](https://learn.microsoft.com/en-us/azure/azure-resource-manager/bicep/) | Infrastructure-as-code interpretation, deployment, export, and decompilation | 2026-08-30 |
| `SRC-AZCOPY` | [Get started with AzCopy](https://learn.microsoft.com/en-us/azure/storage/common/storage-use-azcopy-v10) | Storage data movement exercises | 2026-08-30 |
| `SRC-KQL` | [Kusto Query Language overview](https://learn.microsoft.com/en-us/kusto/query/) | Azure Monitor log queries and troubleshooting | 2026-08-30 |
| `SRC-CLI-ENTRA-USERS` | [Azure CLI Microsoft Entra user commands](https://learn.microsoft.com/en-us/cli/azure/ad/user?view=azure-cli-latest) | Lab 01 user creation, reading, updating, and deletion | 2026-08-30 |
| `SRC-CLI-ENTRA-GROUPS` | [Azure CLI Microsoft Entra group commands](https://learn.microsoft.com/en-us/cli/azure/ad/group?view=azure-cli-latest) | Lab 01 security group, membership, and ownership operations | 2026-08-30 |
| `SRC-GRAPH-USERS` | [Microsoft Graph create user](https://learn.microsoft.com/en-us/graph/api/user-post-users?view=graph-rest-1.0) | Lab 01 required user properties and least-privileged API context | 2026-08-30 |
| `SRC-GRAPH-GROUPS` | [Microsoft Graph create group](https://learn.microsoft.com/en-us/graph/api/group-post-groups?view=graph-rest-1.0) | Lab 01 group type and property behavior | 2026-08-30 |
| `SRC-ENTRA-ROLES` | [Microsoft Entra built-in roles](https://learn.microsoft.com/en-us/entra/identity/role-based-access-control/permissions-reference) | Lab 01 directory-role boundary and least-privilege discussion | 2026-08-30 |

## Domain documentation hubs

| Source ID | Source | Curriculum use | Verified |
|---|---|---|---|
| `SRC-ENTRA` | [Microsoft Entra documentation](https://learn.microsoft.com/en-us/entra/) | Identity and tenant configuration | 2026-08-30 |
| `SRC-POLICY` | [Azure Policy documentation](https://learn.microsoft.com/en-us/azure/governance/policy/) | Governance, compliance, and remediation | 2026-08-30 |
| `SRC-STORAGE` | [Azure Storage documentation](https://learn.microsoft.com/en-us/azure/storage/) | Storage accounts, Blob Storage, and Azure Files | 2026-08-30 |
| `SRC-COMPUTE` | [Azure compute documentation](https://learn.microsoft.com/en-us/azure/?product=compute) | Virtual machines, containers, and App Service routing to service docs | 2026-08-30 |
| `SRC-NETWORK` | [Azure networking documentation](https://learn.microsoft.com/en-us/azure/networking/) | Virtual networks, security, DNS, load balancing, and diagnostics | 2026-08-30 |
| `SRC-MONITOR` | [Azure Monitor documentation](https://learn.microsoft.com/en-us/azure/azure-monitor/) | Metrics, logs, Insights, alerts, and diagnostic settings | 2026-08-30 |
| `SRC-BACKUP` | [Azure Backup documentation](https://learn.microsoft.com/en-us/azure/backup/) | Vaults, policies, backup, restore, reports, and alerts | 2026-08-30 |
| `SRC-ASR` | [Azure Site Recovery documentation](https://learn.microsoft.com/en-us/azure/site-recovery/) | Replication, test failover, failover, and cleanup | 2026-08-30 |

## Source policy

- Recheck `SRC-EXAM-GUIDE` before authoring a release; Microsoft updates exams periodically and updates English first.
- If the live study guide shows an older skills-measured version than the one recorded in `curriculum/blueprint.yml`, compare the page against the most recent Internet Archive capture, record the discrepancy in this register and in `docs/research/az-104-blueprint.md`, and keep the blueprint on the newest officially published version. Never downgrade the blueprint because of a page regression; only a newer skills list or change log counts as an exam update.
- Cite the most specific current Microsoft article in each lab and each answer explanation rather than citing only a documentation hub.
- Record a `lastVerified` date beside time-sensitive command or service behavior.
- Treat Microsoft Learn training as helpful sequencing, not as a replacement for the official objective list.
- Do not use exam dumps, leaked items, copied practice-assessment wording, or third-party question banks.
- When a source and a live tool disagree, pause the affected lab, record the discrepancy, and verify against the current service reference before changing instructions.
