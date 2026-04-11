# CI/CD Pipeline

## Overview

GitHub Actions CI runs automatically on every `feature/**` branch. When all checks pass on the first push, a PR to `develop` is opened automatically. Subsequent pushes re-run CI via the PR sync event.

Branch strategy: `feature/**` → `develop` → `main`

---

## Workflow

**File:** `.github/workflows/ci.yml`

### Triggers

| Event | Condition |
|---|---|
| `push` to `feature/**` | Runs only if no open PR exists for the branch |
| `push` to `develop` or `main` | Always runs — verifies the branch after a merge |
| `pull_request` targeting `develop` or `main` | Runs on every push once a PR is open |

The `preflight` job detects when a `push` fires on a `feature/**` branch that already has an open PR and sets `skip=true`, so CI always runs exactly once per feature commit — via `pull_request` once the PR exists, via `push` before it does. Pushes to `develop` and `main` are never skipped.

### Jobs

```
push feature (no PR)       → preflight → lint → test → docker-build → auto-pr (→ develop)
push feature (PR open)     → preflight [skip=true] → (all skipped)
push develop (no PR)       → preflight → lint → test → docker-build → auto-pr (→ main)
push develop (PR open)     → preflight [skip=true] → (all skipped)
push main                  → preflight → lint → test → docker-build
pull_request               → preflight → lint → test → docker-build
```

| Job | Trigger | Purpose |
|---|---|---|
| `preflight` | Always | Checks if push has an open PR for the branch; sets `skip` output |
| `lint` | When not skipped | `ruff check src/` |
| `test` | When not skipped | `pytest tests/ -v` |
| `docker-build` | When not skipped | `docker build .` — validates the image builds |
| `auto-pr` | Push on `feature/**` or `develop`, after CI passes | Opens PR to `develop` (feature) or `main` (develop) if one doesn't exist yet |

---

## Developer Workflow

1. Create and push a feature branch:
   ```bash
   git checkout -b feature/my-feature
   git push origin feature/my-feature
   ```

2. CI runs lint + test + docker-build. If all pass, a PR to `develop` is opened automatically with the title derived from the branch name (`feature/` prefix stripped).

3. Every subsequent push to the branch re-runs CI via the PR `synchronize` event. The `push` event is suppressed (preflight detects the existing PR).

4. Merge the PR when ready.

---

## Branch Protection

Import `docs/github-ruleset.json` into the repository to enforce:

- PR required before merging to `develop` and `main`
- `lint`, `test`, and `docker-build` checks must pass
- No force pushes
- No branch deletion

**How to import:**  
GitHub → Settings → Rules → Rulesets → New ruleset → Import ruleset → select `github-ruleset.json`

> **Note:** Branch protection rulesets require the repository to be **public** or the account to be on **GitHub Pro**. On a free private repo, the ruleset file can still serve as documentation of the intended policy.
