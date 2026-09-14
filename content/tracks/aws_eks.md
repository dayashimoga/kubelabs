# AWS Infrastructure, IAM, Networking & EKS Platform Curriculum

## 1. What
Amazon Web Services (AWS) is the leading cloud hyperscaler. Elastic Kubernetes Service (EKS) provides managed Kubernetes control planes tightly integrated with AWS VPC networking, IAM security, and Elastic Load Balancing.

## 2. Why
Running production Kubernetes on AWS requires understanding complex cloud interactions: VPC subnet CIDR sizing, CNI ENI allocation, IAM Roles for Service Accounts (IRSA), Security Group rules, NAT Gateway bottlenecks, and Application Load Balancer (ALB) ingress controllers.

## 3. Architecture
```
AWS Cloud:
   VPC (10.0.0.0/16)
      |
      +-- Public Subnets (NAT Gateways, Internet Gateway, ALB)
      |
      +-- Private Subnets (EKS Managed Node Groups, Pods, RDS)
             |
             v
   [EKS Control Plane] (AWS Managed, ENI cross-account attachment)
             |
             +---> AWS VPC CNI Plugin (daemonset: aws-node)
             |        (attaches secondary IPs from private subnet to pods)
             |
             +---> IRSA (OIDC Provider + IAM Roles for Service Accounts)
```

## 4. Internals
- **AWS VPC CNI & IP Allocation**: In AWS EKS, every Kubernetes Pod receives a real, routable IP address directly from the VPC subnet. Each EC2 instance type has a physical limit on the number of Elastic Network Interfaces (ENIs) and secondary IP addresses it can attach (e.g. `m5.large` supports 3 ENIs with 10 IPs each = 30 IPs max). The `aws-node` daemonset maintains a "warm pool" of pre-allocated IPs (`WARM_IP_TARGET`). If a subnet runs out of IP addresses, pods are stuck in `Pending` with `FailedCreatePodSandBox`.
- **IAM Roles for Service Accounts (IRSA)**: Integrates Kubernetes ServiceAccounts with AWS IAM using an OpenID Connect (OIDC) identity provider. Kubelet projects a signed JWT token into the pod (`/var/run/secrets/eks.amazonaws.com/serviceaccount/token`). The AWS SDK exchanges this JWT via `sts:AssumeRoleWithWebIdentity` for temporary AWS credentials without hardcoded access keys.
- **AWS Load Balancer Controller**: Provisions and manages AWS ALBs (Layer 7) and NLBs (Layer 4). Uses TargetGroupBinding to route traffic directly from the ALB to pod IP addresses (IP mode) without traversing NodePort iptables.

## 5. Commands
- AWS CLI diagnostics:
  - `aws eks describe-cluster --name <cluster_name>`
  - `aws ec2 describe-subnets --subnet-ids <id> --query 'Subnets[*].AvailableIpAddressCount'`
  - `aws ec2 describe-security-groups --group-ids <sg_id>`
  - `aws sts get-caller-identity` (verify assumed role)
  - `aws logs tail /aws/eks/<cluster_name>/cluster --follow` (control plane audit logs)

## 6. Configuration
- Production IAM Role Trust Policy for IRSA:
  ```json
  {
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Principal": {
          "Federated": "arn:aws:iam::123456789012:oidc-provider/oidc.eks.us-east-1.amazonaws.com/id/EXAMPLED52D13DEE11EDFB74E"
        },
        "Action": "sts:AssumeRoleWithWebIdentity",
        "Condition": {
          "StringEquals": {
            "oidc.eks.us-east-1.amazonaws.com/id/EXAMPLED52D13DEE11EDFB74E:sub": "system:serviceaccount:prod:order-service-sa",
            "oidc.eks.us-east-1.amazonaws.com/id/EXAMPLED52D13DEE11EDFB74E:aud": "sts.amazonaws.com"
          }
        }
      }
    ]
  }
  ```

## 7. Hands-on Lab
- **Lab 1: AWS EKS VPC CNI Subnet IP Exhaustion**: Diagnose pending pods caused by depleted /24 subnet; tune `WARM_IP_TARGET=2` on `aws-node` daemonset to reclaim unassigned IPs.
- **Lab 2: IRSA AccessDeniedException Remediation**: Fix mismatched OIDC issuer condition in IAM trust policy blocking S3 read access from backend pod.
- **Lab 3: ALB Ingress 502 Bad Gateway**: Fix TargetGroup health check path mismatch where ALB probed `/` (which returned 404) while application only responded to `/healthz`.

## 8. Common Errors
- `FailedCreatePodSandBox: failed to assign an IP address to container`: VPC Subnet has 0 available IP addresses.
- `AccessDeniedException: User: arn:aws:sts:... is not authorized to perform: s3:GetObject`: Missing IAM policy or incorrect IRSA trust policy.
- `EKS cluster authentication failure (You must be logged in to the server)`: AWS IAM identity not mapped in `aws-auth` ConfigMap or EKS Access Entries.

## 9. Troubleshooting
1. Check VPC subnet free IP addresses: `aws ec2 describe-subnets`.
2. Inspect `aws-node` daemonset logs: `kubectl logs -n kube-system -l k8s-app=aws-node`.
3. Check pod environment variables: verify `AWS_ROLE_ARN` and `AWS_WEB_IDENTITY_TOKEN_FILE` are injected.

## 10. Production Design
- Enable VPC CNI Custom Networking with secondary non-routable CIDR (e.g. `100.64.0.0/16`) to eliminate pod IP exhaustion in production VPCs.
- Deploy worker nodes across a minimum of 3 Availability Zones with managed node groups.

## 11. Security
- Keep EKS control plane API endpoint private or restricted to corporate CIDRs.
- Replace legacy `aws-auth` ConfigMap with EKS Access Entries and API-based access management.
- Enforce IMDSv2 (`HttpTokens=required`) on all EC2 worker instances to block SSRF token theft.

## 12. Performance
- Use Graviton (ARM64) instances (e.g. `c7g`, `m7g`) for 20-40% better price-performance.
- Enable Karpenter for just-in-time, sub-minute node autoscaling instead of legacy Cluster Autoscaler.

## 13. Interview Scenarios
- **Scenario**: Why does an `m5.large` instance on EKS max out at 29 pods, and how can you run 100+ pods on that same instance?
  - **Answer**: Standard AWS VPC CNI attaches one secondary IP per pod from the instance ENIs. An `m5.large` has 3 ENIs, each supporting 10 IP addresses ($3 \times 10 - 1 \text{ host IP} = 29 \text{ pods}$). To run more pods, enable **AWS VPC CNI Prefix Delegation** (`ENABLE_PREFIX_DELEGATION=true`). This assigns `/28` IPv4 subnets (16 IPs per slot) to each ENI slot instead of individual IPs, boosting pod density to 110 pods per instance.
