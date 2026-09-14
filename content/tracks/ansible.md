# Ansible Configuration Automation & Idempotency Curriculum

## 1. What
Ansible is an agentless automation engine that configures systems, deploys software, and orchestrates operational workflows over SSH and WinRM using YAML playbooks.

## 2. Why
Fleet configuration drift, broken SSH authentication, non-idempotent tasks that trigger unnecessary service restarts, unencrypted plain-text secrets, and unhandled handler notifications lead to production outages.

## 3. Architecture
```
Control Node (Ansible Engine)
   |
   |-- SSH (Port 22, Key-based Auth)
   |
   +---> Target Host 1 (Linux Server)
   +---> Target Host 2 (Database Node)
   +---> Target Host 3 (Edge Gateway)
```

## 4. Internals
- **Agentless Execution**: Ansible generates temporary standalone Python scripts for each task on the control node, SFTP/SCPs them to the remote target's `/tmp/.ansible/`, executes the script, parses JSON output from stdout, and deletes the script.
- **Idempotency**: Running a playbook once brings the system to the desired state (`changed: true`). Running it again without underlying system changes makes zero modifications (`changed: false`, `ok: true`). Tasks using the `command` or `shell` modules violate idempotency unless guarded with `creates` or `removes`.
- **Handlers**: Triggered only when a task reports `changed: true`. Handlers execute once at the end of the play regardless of how many tasks notified them.
- **Ansible Vault**: Encrypts sensitive YAML files or variables using AES-256 cipher.

## 5. Commands
- Syntax and execution:
  - `ansible-playbook -i inventory.ini site.yml --syntax-check`
  - `ansible-playbook -i inventory.ini site.yml --check --diff` (Dry-run mode!)
  - `ansible-playbook -i inventory.ini site.yml --limit webservers --step`
  - `ansible-inventory -i inventory.ini --graph`
- Vault management:
  - `ansible-vault encrypt vars/secrets.yml`
  - `ansible-vault edit vars/secrets.yml`
  - `ansible-playbook site.yml --vault-password-file .vault_pass`

## 6. Configuration
- Production Playbook with Idempotent System Tuning:
  ```yaml
  ---
  - name: Configure Production Kubernetes Worker Nodes
    hosts: k8s_workers
    become: true
    vars_files:
      - vars/sysctl_params.yml
    tasks:
      - name: Ensure kernel modules are loaded
        community.general.modprobe:
          name: "{{ item }}"
          state: present
        loop:
          - overlay
          - br_netfilter

      - name: Apply sysctl network bridge parameters
        ansible.posix.sysctl:
          name: "{{ item.key }}"
          value: "{{ item.val }}"
          state: present
          reload: true
        loop:
          - { key: "net.bridge.bridge-nf-call-iptables", val: "1" }
          - { key: "net.ipv4.ip_forward", val: "1" }
        notify: Restart containerd

    handlers:
      - name: Restart containerd
        ansible.builtin.systemd:
          name: containerd
          state: restarted
  ```

## 7. Hands-on Lab
- **Lab 1: Non-Idempotent Shell Task Remediation**: Replace raw `shell: curl ... >> /etc/hosts` with idempotent `ansible.builtin.lineinfile` or `template` module to ensure `changed: false` on rerun.
- **Lab 2: Unhandled Handler Failure**: Diagnose playbook where task failure prevented downstream handler notification, leaving service in inconsistent state; fix using `meta: flush_handlers` or `force_handlers: true`.
- **Lab 3: Ansible Vault Decryption in CI**: Configure automated vault decryption in CI runner using environment variable `ANSIBLE_VAULT_PASSWORD`.

## 8. Common Errors
- `UNREACHABLE! => {"msg": "Permission denied (publickey)"}`: Missing SSH private key, incorrect remote user, or HostKeyChecking failure.
- `FAILED! => {"msg": "Missing sudo password"}`: Task required `become: true` without sudo permissions or passwordless sudo configured in `/etc/sudoers`.
- `fatal: [host]: FAILED! => {"msg": "The conditional check 'var is defined' failed"}`: Undefined variable reference.

## 9. Troubleshooting
1. Run with increased verbosity: `ansible-playbook -vvvv`.
2. Inspect dry run diffs: `ansible-playbook --check --diff`.
3. Test connectivity with ad-hoc ping: `ansible all -m ping -i inventory.ini`.

## 10. Production Design
- Structure projects using Ansible Roles or Collections with clear `tasks/`, `handlers/`, `defaults/`, `vars/`, and `templates/`.
- Enforce `ansible-lint` in CI pipeline.

## 11. Security
- Never commit unencrypted Vault passwords or API tokens to version control.
- Restrict remote SSH root access (`PermitRootLogin no`) and use dedicated service accounts with constrained sudo privileges.

## 12. Performance
- Enable SSH Pipelining (`pipelining = True` in `ansible.cfg`) to eliminate SFTP overhead.
- Configure `forks = 50` for parallel execution across large fleets.

## 13. Interview Scenarios
- **Scenario**: A task uses `command: service nginx restart` instead of the `service` module. Why is this considered an anti-pattern in Ansible?
  - **Answer**: `command` is never idempotent—it executes on every run and always reports `changed: true`, which triggers downstream handlers and causes unnecessary service disruptions. Using the `ansible.builtin.service` module allows Ansible to inspect the daemon's current state and only restart if configuration files have changed.
