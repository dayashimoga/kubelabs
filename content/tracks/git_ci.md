# Git Version Control, GitHub Actions & CI/CD Curriculum

## 1. What
Git is a distributed content-addressable version control system. CI/CD (Continuous Integration and Continuous Deployment) automates building, linting, testing, security scanning, containerizing, and publishing code.

## 2. Why
Modern SRE requires rapid, verified releases. Failed merge conflicts, exposed API credentials in git history, flaky end-to-end tests, broken dependency caches, and release rollbacks directly impact velocity and site reliability.

## 3. Architecture
```
Developer Branch ---> Pull Request ---> GitHub Actions Runner
                                              |
      +-------------------+-------------------+-------------------+
      |                   |                   |                   |
      v                   v                   v                   v
[Lint & Types]     [Unit/Int Tests]    [Security Scans]    [Docker Build]
(eslint/ruff)      (pytest/jest)       (Trivy/Gitleaks)    (BuildKit OCI)
                                                                  |
                                                                  v
                                                           [Container Registry]
```

## 4. Internals
- **Git Object Model**: Blobs (file contents), Trees (directories and filenames), Commits (pointer to root tree, parent commit, author, message), and Annotated Tags. All objects are SHA-1/SHA-256 content-addressable hashes stored in `.git/objects/`.
- **Merge vs Rebase vs Squash**:
  - `git merge`: Creates a merge commit preserving full branch history.
  - `git rebase`: Replays commits onto target base, creating a linear history.
  - `squash`: Compresses multiple commits into a single commit upon merge.
- **GitHub Actions Runner Architecture**: Ephemeral runner instances receive workflow job events via WebSocket/long-poll from GitHub API. Step failures stop subsequent steps unless guarded with `if: always()`.
- **Matrix Builds**: Parallelizes jobs across dimensions (e.g. `python: [3.10, 3.11, 3.12]`, `os: [ubuntu-latest, windows-latest]`).

## 5. Commands
- Git diagnostic and surgery commands:
  - `git log --graph --oneline --decorate --all -n 20`
  - `git reflog` (the safety net: lists previous HEAD positions for recovering lost commits)
  - `git reset --hard HEAD~1` vs `git reset --soft HEAD~1`
  - `git cherry-pick <commit-hash>`
  - `git bisect start` / `git bisect bad` / `git bisect good <commit>` (binary search for bug introduction)
  - `git filter-repo` / `git-filter-branch` (scrub exposed API keys from entire git history)

## 6. Configuration
- Production GitHub Actions Workflow (`.github/workflows/ci.yml`):
  ```yaml
  name: Production CI Pipeline
  on:
    pull_request:
      branches: [main]
    push:
      branches: [main]
  jobs:
    test:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v4
          with:
            fetch-depth: 0
        - name: Secret Scanning
          uses: gitleaks/gitleaks-action@v2
        - name: Set up Python
          uses: actions/setup-python@v5
          with:
            python-version: '3.11'
            cache: 'pip'
        - name: Run Tests with Coverage
          run: |
            pip install -r requirements.txt
            pytest --cov=src --cov-fail-under=90
  ```

## 7. Hands-on Lab
- **Lab 1: Recovering Deleted Commits via Git Reflog**: Simulate accidental `git reset --hard` destroying unpushed work; locate commit hash in `git reflog`; recover branch pointer.
- **Lab 2: Scrubbing Committed Secrets from History**: Locate committed AWS secret key; scrub from entire commit graph using `git filter-repo`; force-push clean history.
- **Lab 3: Resolving Complex 3-Way Merge Conflicts**: Resolve conflicting migrations in Git working tree and commit clean merge resolution.

## 8. Common Errors
- `error: failed to push some refs to ... (Updates were rejected because the remote contains work)`: Fast-forward rejected; requires `git pull --rebase`.
- `fatal: refusing to merge unrelated histories`: Two repositories with separate root commits merged without `--allow-unrelated-histories`.
- Flaky tests failing in CI due to unmocked external network calls or race conditions in parallel test workers.

## 9. Troubleshooting
1. Use `git status` to identify conflicting files (`both modified:`).
2. Inspect `git reflog` when commits disappear.
3. Review CI runner step logs and raw execution output.

## 10. Production Design
- Mandate branch protection rules: Require PR reviews, passing status checks, and linear git history on `main`.
- Automate Semantic Versioning (`semver`) and changelog generation using Release Drafter / Semantic Release.

## 11. Security
- Enforce secret detection tools (Gitleaks, Trufflehog) in pre-commit hooks and CI gates.
- Sign git commits using GPG or SSH keys.
- Restrict GitHub Actions token permissions (`permissions: contents: read`).

## 12. Performance
- Utilize dependency caching (`actions/cache`) for npm packages, pip wheels, and Go build caches.
- Enable Docker BuildKit layer caching with GitHub Actions cache backend (`cache-from: type=gha`).

## 13. Interview Scenarios
- **Scenario**: A junior engineer accidentally commits an AWS access key and secret to a public GitHub repo, pushes it, and then commits a second change deleting the file. Is the secret safe? How do you remediate?
  - **Answer**: No, the secret is completely compromised. Git retains the file blob in the previous commit object, visible in git log and API history. Remediation:
    1. Immediately rotate and revoke the credential in AWS IAM.
    2. Scrub the commit history using `git filter-repo --invert-paths --path secrets.env` and force-push.
    3. Audit AWS CloudTrail logs for unauthorized API calls during the exposure window.
