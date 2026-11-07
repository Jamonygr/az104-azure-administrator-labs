# Prerequisites

## Knowledge

- Azure fundamentals, networking, operating systems, servers, and virtualization.
- Basic command-line and source-control familiarity.

Microsoft's AZ-104 audience profile also expects experience with PowerShell, Azure CLI, the Azure portal, Azure Resource Manager templates or Bicep files, and Microsoft Entra ID. This curriculum builds the PowerShell, Azure CLI, Bicep, and Microsoft Entra ID experience directly; it does not contain portal procedures, so review the portal independently if you have never used it.

## Azure environment

- A disposable sandbox tenant and subscription that you are authorized to modify.
- `Reader` is sufficient for many preflight checks; labs declare additional Azure RBAC and Entra roles individually.
- A €10 live-test batch ceiling by default. Elevated labs require separate approval.
- `westeurope` and `northeurope` are defaults, not guarantees; preflight checks service and SKU availability.

Never use production or an employer tenant unless the owner has explicitly approved the exact lab changes.

## Tools

- Git
- Azure CLI 2.88 or later
- PowerShell 7.4 or later as the command host; Azure PowerShell modules are not used
- Bicep 0.46.1 or later through `az bicep`, AzCopy 10.32.8 or later, and the Container Apps extension 1.3.0b4 or later
- Python 3.12 and Node.js 22 for repository tooling and the local documentation site
- A secure location for temporary, redacted Azure CLI live-verification output

The dev container provides a reproducible starting point. Every lab still checks its own required Azure CLI extensions, providers, tools, and service prerequisites.

## Authentication

Use interactive or device authentication locally. Do not save access tokens in the repository. Future GitHub Actions that contact Azure must use OIDC and a protected environment; pull-request checks stay offline.
