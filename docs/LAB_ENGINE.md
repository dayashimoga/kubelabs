# KubeLabs Declarative Lab Engine Specification

## 1. Overview
The KubeLabs Lab Engine is responsible for loading, validating, provisioning, executing, and evaluating hands-on engineering labs.

## 2. Lab Lifecycle State Machine
```
[Uninitialized]
       |
       v (GET /api/v1/labs/{id})
[Loaded in Registry]
       |
       v (POST /session)
[Sandbox Provisioning] ---> (Podman Run / Simulator Init)
       |
       v
[Active Session] <---> (WebSocket Terminal & Monaco Editor)
       |
       +---> [Ask Advisor] ---> (Layered Hints & Guided Q&A)
       |
       v (POST /validate)
[State Evaluation] ---> (14 Validators Check Actual State)
       |
       +---> PASS / PARTIAL / FAIL
       |
       v (DELETE /session OR TTL Expiry)
[Tear Down & Cleanup] ---> (Container rm, network prune, file purge)
```

## 3. Validator Types & Execution Rules

| Validator Type | Checked Resource | Target Spec | Success Criteria |
| :--- | :--- | :--- | :--- |
| `command` | Subprocess execution | Shell command string | `exit_code == expected`, optional `output_regex` or `output_contains` |
| `file` | Filesystem entry | File path | File exists, matches octal permissions, content substring |
| `yaml` | YAML document | Manifest path | JMESPath / dot-notation key values match assertions |
| `json` | JSON document | File path | JSON structure matches expected schema/values |
| `http` | HTTP endpoint | URL | HTTP status code matches, response body contains substring |
| `tcp` | TCP Socket | Host + Port | Socket opens successfully within timeout |
| `dns` | DNS Name | Hostname | Resolves to IP or matches expected IP |
| `container` | Podman/Docker container | Container Name | `State.Status == 'running'` |
| `kubernetes` | Kubernetes API | Resource name | Pod Phase is Running, Endpoints > 0 |
| `git` | Git Repository | Workdir | Clean working tree, on specified branch |
| `prometheus` | Prometheus Vector | PromQL Query | Evaluated value satisfies comparison operator |
| `opentelemetry` | Trace Pipeline | Span Name | Span exists with status `OK` and matching tags |

## 4. Layered Hint Engine
Hints are disclosed progressively to prevent giving away answers prematurely:
1. **Tier 1 (Conceptual Direction)**: Explains the underlying protocol or system mechanism. (-5 pts)
2. **Tier 2 (Inspection Target)**: Points learner to the specific file, socket, or API object. (-10 pts)
3. **Tier 3 (Diagnostic Command)**: Gives exact shell command to reveal authoritative evidence. (-15 pts)
4. **Tier 4 (Strong Clue)**: Explicitly identifies the root-cause mismatch. (-20 pts)
5. **Tier 5 (Full Solution)**: Provides full copy-paste solution and prevention advice. (-35 pts)
