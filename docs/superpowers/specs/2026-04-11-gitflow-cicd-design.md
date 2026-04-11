# Gitflow CI/CD Design

**Date:** 2026-04-11
**Repos:** `nathanfiorito/personal-finances-backend`, `nathanfiorito/personal-finances-frontend`
**Infra:** Coolify on VPS (backend), Vercel (frontend)

---

## Overview

Simplified Gitflow branching model with GitHub Actions CI for both repos. Coolify auto-deploys the backend from `develop` (staging) and `main` (production) via GitHub webhook. Vercel handles frontend deploys natively.

---

## Branching Model

```
main        ←── PR from develop only ──── production deploy (Coolify / Vercel)
develop     ←── PR from feature/*   ──── staging deploy (Coolify backend only)
feature/*   ←── created from develop, merged back via PR
```

- `feature/*` branches are created from `develop` and merged back via PR.
- `develop` → `main` is the only path to production.
- Hotfixes follow the same path: `feature/fix-*` → `develop` → fast-track PR to `main`.
- Direct pushes to `main` and `develop` are blocked via GitHub branch protection rules.

---

## CI Pipeline — GitHub Actions

Both repos get `.github/workflows/ci.yml`.

**Triggers:**
- Push to `feature/**`
- Pull request targeting `develop` or `main`

### Backend (`personal-finances-backend`)

Three parallel jobs:

| Job | Command | Notes |
|-----|---------|-------|
| `lint` | `ruff check src/` | Python 3.12 |
| `test` | `pytest tests/` | Installs `requirements.txt` |
| `docker-build` | `docker build .` | Verifies image builds cleanly |

All three must pass for the CI check to be green.

### Frontend (`personal-finances-frontend`)

Three parallel jobs:

| Job | Command | Notes |
|-----|---------|-------|
| `lint` | `npm run lint` | Node 20 |
| `test` | `npm run test` | Vitest |
| `build` | `npm run build` | Catches type errors + bundling failures |

All three must pass for the CI check to be green.

---

## Branch Protection Rules (both repos)

### `main`
- Require a pull request before merging
- Require CI status checks to pass (`ci` workflow)
- No direct pushes allowed

### `develop`
- Require a pull request before merging
- Require CI status checks to pass (`ci` workflow)
- No direct pushes allowed

---

## CD / Deploy

### Backend (Coolify on VPS)

Two separate Coolify applications pointing to `nathanfiorito/personal-finances-backend`:

| Coolify App | Branch | Environment |
|-------------|--------|-------------|
| `personal-finances-backend-staging` | `develop` | staging |
| `personal-finances-backend-prod` | `main` | production |

Coolify connects via GitHub webhook. Every push to the watched branch triggers an automatic deploy. GitHub Actions CI and Coolify CD are independent — CI validates code quality, branch protection ensures CI passes before merge, Coolify reacts to the merged commit.

### Frontend (Vercel)

Vercel's native Git integration handles everything without additional config:

- PR opened → Vercel preview deploy created automatically
- Merge to `main` → Vercel production deploy

The only addition is the GitHub Actions CI check, which branch protection enforces before any PR merge.

---

## End-to-End Flow

```
# Feature development
git checkout develop && git pull
git checkout -b feature/my-feature

# ... develop ...

git push origin feature/my-feature
# → GitHub Actions CI runs on push

# Open PR to develop
# → CI must pass before merge is allowed
# → Merge → Coolify staging deploys automatically

# Promote to production
# Open PR: develop → main
# → CI runs again on the PR
# → Merge → Coolify prod deploys automatically
#          → Vercel prod deploys automatically (frontend)
```

---

## Out of Scope

- Release branches (`release/*`) — excluded by design (simplified Gitflow)
- Hotfix branches (`hotfix/*`) — handled as regular `feature/fix-*` branches
- E2E tests in CI — Playwright tests exist but are not included in the CI pipeline (require running infra)
- Coolify rollback strategy — manual via Coolify dashboard
