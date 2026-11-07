# AZ-104 objective-to-lab map

Blueprint effective date: **2026-04-17**
Verification status: see the [verification notes](research/az-104-blueprint.md#verification-notes)
Source of objective text: [Microsoft's official AZ-104 study guide](https://learn.microsoft.com/en-us/credentials/certifications/resources/study-guides/az-104)

This map assigns every official objective to at least one of the 28 lab folders. The first listed lab is normally the primary teaching lab; capstones and cross-domain labs reinforce or validate the same skill. Live verification is tracked separately from this objective-to-lab teaching map.

## Coverage summary

| Domain | Weight | Groups | Objectives | Core lab range |
|---|---:|---:|---:|---|
| Manage Azure identities and governance | 20–25% | 3 | 15 | 01–05 |
| Implement and manage storage | 15–20% | 3 | 17 | 06–09 |
| Deploy and manage Azure compute resources | 20–25% | 4 | 24 | 10–16 |
| Implement and manage virtual networking | 15–20% | 3 | 13 | 17–21 |
| Monitor and maintain Azure resources | 10–15% | 2 | 13 | 22–25 |
| **Official total** |  | **15** | **82** | Capstones 26–27 reinforce all domains |

## Non-exam foundation outcomes

These five outcomes belong to Lab 00 and do not count toward the 82 official objectives.

| ID | Foundation outcome | Lab |
|---|---|---|
| `FD-TOOLS-01` | Verify the required Azure CLI and PowerShell toolchain | `00-safe-bootstrap` |
| `FD-CONTEXT-01` | Confirm the intended Azure tenant and subscription context before changes | `00-safe-bootstrap` |
| `FD-COST-01` | Review service, quota, region, and cost gates before deployment | `00-safe-bootstrap` |
| `FD-SAFETY-01` | Use deterministic names, tags, run IDs, and state records | `00-safe-bootstrap` |
| `FD-CLEANUP-01` | Preview, perform, and verify scoped and idempotent cleanup | `00-safe-bootstrap` |

## Manage Azure identities and governance (20–25%)

### Manage Microsoft Entra users and groups

| ID | Official objective | Lab mapping |
|---|---|---|
| `IG-USERS-01` | Create users and groups | `01-entra-users-groups` |
| `IG-USERS-02` | Manage user and group properties | `01-entra-users-groups` |
| `IG-USERS-03` | Manage licenses in Microsoft Entra ID | `02-entra-licenses-guests-sspr` |
| `IG-USERS-04` | Manage external users | `02-entra-licenses-guests-sspr` |
| `IG-USERS-05` | Configure self-service password reset (SSPR) | `02-entra-licenses-guests-sspr` |

### Manage access to Azure resources

| ID | Official objective | Lab mapping |
|---|---|---|
| `IG-ACCESS-01` | Manage built-in Azure roles | `03-azure-rbac-scopes`; `26-capstone-build` |
| `IG-ACCESS-02` | Assign roles at different scopes | `03-azure-rbac-scopes`; `26-capstone-build` |
| `IG-ACCESS-03` | Interpret access assignments | `03-azure-rbac-scopes`; `27-capstone-operate-recover` |

### Manage Azure subscriptions and governance

| ID | Official objective | Lab mapping |
|---|---|---|
| `IG-GOVERN-01` | Implement and manage Azure Policy | `05-policy-costs-advisor`; `26-capstone-build`; `27-capstone-operate-recover` |
| `IG-GOVERN-02` | Configure resource locks | `04-resource-hierarchy-tags-locks`; `27-capstone-operate-recover` |
| `IG-GOVERN-03` | Apply and manage tags on resources | `00-safe-bootstrap`; `04-resource-hierarchy-tags-locks`; `26-capstone-build` |
| `IG-GOVERN-04` | Manage resource groups | `00-safe-bootstrap`; `04-resource-hierarchy-tags-locks`; `26-capstone-build`; `27-capstone-operate-recover` |
| `IG-GOVERN-05` | Manage subscriptions | `00-safe-bootstrap`; `04-resource-hierarchy-tags-locks` |
| `IG-GOVERN-06` | Manage costs by using alerts, budgets, and Azure Advisor recommendations | `05-policy-costs-advisor`; `27-capstone-operate-recover` |
| `IG-GOVERN-07` | Configure management groups | `04-resource-hierarchy-tags-locks`; `05-policy-costs-advisor` |

## Implement and manage storage (15–20%)

### Configure access to storage

| ID | Official objective | Lab mapping |
|---|---|---|
| `ST-ACCESS-01` | Configure Azure Storage firewalls and virtual networks | `07-storage-network-sas`; `19-service-private-endpoints` |
| `ST-ACCESS-02` | Create and use shared access signature (SAS) tokens | `07-storage-network-sas` |
| `ST-ACCESS-03` | Configure stored access policies | `07-storage-network-sas` |
| `ST-ACCESS-04` | Manage access keys | `06-storage-accounts-security`; `07-storage-network-sas` |
| `ST-ACCESS-05` | Configure identity-based access for Azure Files | `09-azure-files-identity` |

### Configure and manage storage accounts

| ID | Official objective | Lab mapping |
|---|---|---|
| `ST-ACCOUNTS-01` | Create and configure storage accounts | `06-storage-accounts-security`; `26-capstone-build` |
| `ST-ACCOUNTS-02` | Configure Azure Storage redundancy | `06-storage-accounts-security` |
| `ST-ACCOUNTS-03` | Configure object replication | `08-blob-lifecycle-replication` |
| `ST-ACCOUNTS-04` | Configure storage account encryption | `06-storage-accounts-security` |
| `ST-ACCOUNTS-05` | Manage data by using Azure Storage Explorer and AzCopy | `08-blob-lifecycle-replication`; `09-azure-files-identity` |

### Configure Azure Files and Azure Blob Storage

| ID | Official objective | Lab mapping |
|---|---|---|
| `ST-DATA-01` | Create and configure a file share in Azure Files | `09-azure-files-identity` |
| `ST-DATA-02` | Create and configure a container in Azure Blob Storage | `08-blob-lifecycle-replication` |
| `ST-DATA-03` | Configure storage tiers | `08-blob-lifecycle-replication` |
| `ST-DATA-04` | Configure soft delete for blobs and containers | `08-blob-lifecycle-replication` |
| `ST-DATA-05` | Configure snapshots and soft delete for Azure Files | `09-azure-files-identity` |
| `ST-DATA-06` | Configure blob lifecycle management | `08-blob-lifecycle-replication` |
| `ST-DATA-07` | Configure blob versioning | `08-blob-lifecycle-replication` |

## Deploy and manage Azure compute resources (20–25%)

### Automate deployment of resources by using Azure Resource Manager (ARM) templates or Bicep files

| ID | Official objective | Lab mapping |
|---|---|---|
| `CP-IAC-01` | Interpret an Azure Resource Manager template or a Bicep file | `10-arm-bicep-lifecycle` |
| `CP-IAC-02` | Modify an existing Azure Resource Manager template | `10-arm-bicep-lifecycle` |
| `CP-IAC-03` | Modify an existing Bicep file | `10-arm-bicep-lifecycle` |
| `CP-IAC-04` | Deploy resources by using an Azure Resource Manager template or a Bicep file | `10-arm-bicep-lifecycle`; `26-capstone-build` |
| `CP-IAC-05` | Export a deployment as an Azure Resource Manager template or convert an Azure Resource Manager template to a Bicep file | `10-arm-bicep-lifecycle` |

### Create and configure virtual machines

| ID | Official objective | Lab mapping |
|---|---|---|
| `CP-VM-01` | Create a virtual machine | `11-vm-lifecycle-disks-encryption`; `26-capstone-build` |
| `CP-VM-02` | Configure encryption at host for Azure virtual machines | `11-vm-lifecycle-disks-encryption` |
| `CP-VM-03` | Move a virtual machine to another resource group, subscription, or region | `12-vm-resilience-scale-mobility` |
| `CP-VM-04` | Manage virtual machine sizes | `11-vm-lifecycle-disks-encryption`; `12-vm-resilience-scale-mobility` |
| `CP-VM-05` | Manage virtual machine disks | `11-vm-lifecycle-disks-encryption` |
| `CP-VM-06` | Deploy virtual machines to availability zones and availability sets | `12-vm-resilience-scale-mobility`; `26-capstone-build` |
| `CP-VM-07` | Deploy and configure an Azure Virtual Machine Scale Sets | `12-vm-resilience-scale-mobility`; `26-capstone-build` |

### Provision and manage containers in the Azure portal

| ID | Official objective | Lab mapping |
|---|---|---|
| `CP-CONTAINERS-01` | Create and manage an Azure Container Registry | `13-acr-aci` |
| `CP-CONTAINERS-02` | Provision a container by using Azure Container Instances | `13-acr-aci` |
| `CP-CONTAINERS-03` | Provision a container by using Azure Container Apps | `14-container-apps` |
| `CP-CONTAINERS-04` | Manage sizing and scaling for containers, including Azure Container Instances and Azure Container Apps | `13-acr-aci`; `14-container-apps` |

### Create and configure Azure App Service

| ID | Official objective | Lab mapping |
|---|---|---|
| `CP-APP-01` | Provision an App Service plan | `15-app-service-scale-slots` |
| `CP-APP-02` | Configure scaling for an App Service plan | `15-app-service-scale-slots` |
| `CP-APP-03` | Create an App Service | `15-app-service-scale-slots` |
| `CP-APP-04` | Configure certificates and Transport Layer Security (TLS) for an App Service | `16-app-service-tls-dns-backup-network` |
| `CP-APP-05` | Map an existing custom DNS name to an App Service | `16-app-service-tls-dns-backup-network` |
| `CP-APP-06` | Configure backup for an App Service | `16-app-service-tls-dns-backup-network` |
| `CP-APP-07` | Configure networking settings for an App Service | `16-app-service-tls-dns-backup-network`; `19-service-private-endpoints` |
| `CP-APP-08` | Configure deployment slots for an App Service | `15-app-service-scale-slots` |

## Implement and manage virtual networking (15–20%)

### Configure and manage virtual networks in Azure

| ID | Official objective | Lab mapping |
|---|---|---|
| `NW-VNET-01` | Create and configure virtual networks and subnets | `17-vnet-subnets-peering-public-ip`; `26-capstone-build` |
| `NW-VNET-02` | Create and configure virtual network peering | `17-vnet-subnets-peering-public-ip` |
| `NW-VNET-03` | Configure public IP addresses | `17-vnet-subnets-peering-public-ip` |
| `NW-VNET-04` | Configure user-defined routes | `18-routing-nsg-asg` |
| `NW-VNET-05` | Troubleshoot network connectivity | `18-routing-nsg-asg`; `21-load-balancer-network-watcher`; `27-capstone-operate-recover` |

### Configure secure access to virtual networks

| ID | Official objective | Lab mapping |
|---|---|---|
| `NW-SECURE-01` | Create and configure network security groups (NSGs) and application security groups | `18-routing-nsg-asg`; `26-capstone-build` |
| `NW-SECURE-02` | Evaluate effective security rules in NSGs | `18-routing-nsg-asg`; `27-capstone-operate-recover` |
| `NW-SECURE-03` | Implement Azure Bastion | `20-azure-dns-bastion` |
| `NW-SECURE-04` | Configure service endpoints for Azure platform as a service (PaaS) | `19-service-private-endpoints` |
| `NW-SECURE-05` | Configure private endpoints for Azure PaaS | `19-service-private-endpoints`; `26-capstone-build` |

### Configure name resolution and load balancing

| ID | Official objective | Lab mapping |
|---|---|---|
| `NW-DNSLB-01` | Configure Azure DNS | `20-azure-dns-bastion`; `16-app-service-tls-dns-backup-network` |
| `NW-DNSLB-02` | Configure an internal or public load balancer | `21-load-balancer-network-watcher`; `26-capstone-build` |
| `NW-DNSLB-03` | Troubleshoot load balancing | `21-load-balancer-network-watcher`; `27-capstone-operate-recover` |

## Monitor and maintain Azure resources (10–15%)

### Monitor resources in Azure

| ID | Official objective | Lab mapping |
|---|---|---|
| `MR-MONITOR-01` | Interpret metrics in Azure Monitor | `22-azure-monitor-logs-insights` |
| `MR-MONITOR-02` | Configure log settings in Azure Monitor | `22-azure-monitor-logs-insights`; `26-capstone-build` |
| `MR-MONITOR-03` | Query and analyze logs in Azure Monitor | `22-azure-monitor-logs-insights`; `27-capstone-operate-recover` |
| `MR-MONITOR-04` | Set up alert rules, action groups, and alert processing rules in Azure Monitor | `23-monitor-alerts-actions`; `26-capstone-build`; `27-capstone-operate-recover` |
| `MR-MONITOR-05` | Configure and interpret monitoring of virtual machines, storage accounts, and networks by using Azure Monitor Insights | `22-azure-monitor-logs-insights`; `27-capstone-operate-recover` |
| `MR-MONITOR-06` | Use Azure Network Watcher and Connection monitor | `21-load-balancer-network-watcher`; `22-azure-monitor-logs-insights`; `27-capstone-operate-recover` |

### Implement backup and recovery

| ID | Official objective | Lab mapping |
|---|---|---|
| `MR-RECOVERY-01` | Create a Recovery Services vault | `24-azure-backup-restore` |
| `MR-RECOVERY-02` | Create an Azure Backup vault | `24-azure-backup-restore` |
| `MR-RECOVERY-03` | Create and configure a backup policy | `24-azure-backup-restore` |
| `MR-RECOVERY-04` | Perform backup and restore operations by using Azure Backup | `24-azure-backup-restore`; `27-capstone-operate-recover` |
| `MR-RECOVERY-05` | Configure Azure Site Recovery for Azure resources | `25-site-recovery-failover` |
| `MR-RECOVERY-06` | Perform a failover to a secondary region by using Site Recovery | `25-site-recovery-failover`; `27-capstone-operate-recover` |
| `MR-RECOVERY-07` | Configure and interpret reports and alerts for backups | `24-azure-backup-restore`; `27-capstone-operate-recover` |

## Coverage invariants

- Official objective IDs are unique and match `DOMAIN-GROUP-NN`.
- Exactly 82 official objectives appear in the five domain sections.
- Exactly five non-exam `FD-*` outcomes appear only in the foundation section.
- Every official objective has at least one lab mapping.
- Every lab from `00-safe-bootstrap` through `27-capstone-operate-recover` appears in at least one mapping.
- A lab's eventual `lab.yml` and assessment metadata must use these IDs verbatim.
