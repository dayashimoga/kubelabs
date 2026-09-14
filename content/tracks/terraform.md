# Terraform Infrastructure as Code & State Management Curriculum

## 1. What
Terraform is an open-source declarative Infrastructure as Code (IaC) tool that manages cloud and on-premises resources using HashiCorp Configuration Language (HCL).

## 2. Why
Cloud infrastructure is too complex to manage manually. IaC guarantees auditability, reproducibility, and automated lifecycle management. However, state file corruption, unmanaged drift, locking deadlocks, dependency cycle errors, and destructive plans are common production disasters.

## 3. Architecture
```
HCL Code (*.tf) + Provider Plugins (AWS, Azure, K8s)
                 |
                 v
        [Terraform Core Engine]
                 |
      +----------+----------+
      |                     |
      v                     v
[Remote State Backend]   [Cloud APIs (Target Resources)]
(S3 + DynamoDB Lock)     (VPC, EC2, RDS, IAM, EKS)
```

## 4. Internals
- **State File (`terraform.tfstate`)**: A JSON document mapping declared HCL resources (`aws_instance.web`) to real-world cloud IDs (`i-0a1b2c3d4e`). State contains resource metadata, dependency graphs, and sensitive outputs.
- **State Locking**: Distributed locking (e.g. DynamoDB table with `LockID` string attribute) prevents concurrent runs from corrupting the state file.
- **Refresh and Drift**: `terraform refresh` queries cloud APIs to update the state with actual real-world values. `terraform plan` computes the directed acyclic graph (DAG) diff between desired HCL and refreshed state.
- **Destroy & Recreate**: Certain resource attribute changes (e.g. changing an EC2 instance AMI or subnet CIDR) force replacement (`-/+`). Careless applies cause unplanned outages.

## 5. Commands
- Workflow commands:
  - `terraform init -backend-config=...`
  - `terraform validate`
  - `terraform plan -out=tfplan`
  - `terraform apply tfplan`
- State manipulation and recovery:
  - `terraform state list`
  - `terraform state show <resource_address>`
  - `terraform state rm <resource_address>` (detach from Terraform management without destroying cloud resource)
  - `terraform import <resource_address> <cloud_id>` (bring unmanaged resource into Terraform)
  - `terraform force-unlock <lock-id>` (clear stuck lock when a worker dies mid-run)

## 6. Configuration
- Production Remote Backend Configuration:
  ```hcl
  terraform {
    required_version = ">= 1.6.0"
    required_providers {
      aws = {
        source  = "hashicorp/aws"
        version = "~> 5.40"
      }
    }
    backend "s3" {
      bucket         = "corp-terraform-state-prod"
      key            = "platform/eks/terraform.tfstate"
      region         = "us-east-1"
      dynamodb_table = "terraform-locks"
      encrypt        = true
    }
  }
  ```

## 7. Hands-on Lab
- **Lab 1: Stuck State Lock Resolution**: Release a stuck DynamoDB lock ID left by a crashed CI runner using `terraform force-unlock`.
- **Lab 2: State Drift Remediation via Import**: Reconcile unmanaged security group rule added via AWS Console using `terraform import` without recreating the security group.
- **Lab 3: Refactoring with Moved Blocks**: Rename module resources safely using `moved {}` blocks without triggering resource destruction.

## 8. Common Errors
- `Error: Error acquiring the state lock: ConditionalCheckFailedException`: State is locked by another process.
- `Cycle: resource A -> resource B -> resource A`: Circular dependency in resource references.
- `Provider produced inconsistent result after apply`: Cloud API returned different attributes than anticipated by the provider.

## 9. Troubleshooting
1. Inspect plan carefully for `-/+` (replacement) warnings.
2. Check `terraform state list` to confirm resource tracking.
3. Enable debug logging: `TF_LOG=DEBUG terraform apply`.

## 10. Production Design
- Separate state files by environment and blast radius (`networking`, `database`, `compute`).
- Enforce CI/CD pipeline automation (Atlantis, Spacelift, GitHub Actions) and disable local terminal applies.

## 11. Security
- Encrypt state bucket with KMS Customer Managed Keys (CMK) and enable S3 bucket versioning.
- Block public S3 access and mandate TLS 1.2 on S3 endpoint.
- Run `tfsec` / `trivy config` / `checkov` in CI to detect insecure infrastructure definitions.

## 12. Performance
- Use `-target` sparingly during emergency incident triage.
- Leverage `-parallelism=20` for large states.

## 13. Interview Scenarios
- **Scenario**: A critical production database was accidentally deleted from the Terraform code. `terraform plan` indicates the database will be destroyed. How do you prevent it from being destroyed?
  - **Answer**: 
    1. Add `lifecycle { prevent_destroy = true }` in the resource block.
    2. Remove the resource from the state file using `terraform state rm aws_db_instance.primary` so Terraform ceases to manage its lifecycle without issuing a cloud API deletion call.
