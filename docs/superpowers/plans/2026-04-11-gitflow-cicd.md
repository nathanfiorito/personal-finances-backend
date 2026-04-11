# Gitflow CI/CD Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Set up Simplified Gitflow branching with GitHub Actions CI (lint + tests + build) on both repos, branch protection on `main` and `develop`, and Coolify auto-deploy for the backend.

**Architecture:** Two separate GitHub repos each get a `.github/workflows/ci.yml` that runs lint, tests, and a build/compile check in parallel. Branch protection on `main` and `develop` gates merges on all CI checks passing. Coolify watches `develop` (staging) and `main` (production) via GitHub webhook and auto-deploys on every push.

**Tech Stack:** GitHub Actions, `gh` CLI (branch protection), Docker (backend), Next.js (frontend build), Coolify (CD)

---

## File Structure

**`personal-finances-backend` repo:**
- Create: `.github/workflows/ci.yml` — 3 parallel jobs: lint (ruff), test (pytest), docker-build

**`personal-finances-frontend` repo:**
- Create: `.github/workflows/ci.yml` — 3 parallel jobs: lint (eslint), test (vitest), build (next build)

---

## Task 1: Create `develop` branch in both repos

**Files:** none (git operations only)

- [ ] **Step 1: Create and push `develop` in the backend repo**

```bash
cd personal-finances-backend
git checkout main && git pull origin main
git checkout -b develop
git push origin develop
```

Expected: branch `develop` appears on `github.com/nathanfiorito/personal-finances-backend`.

- [ ] **Step 2: Create and push `develop` in the frontend repo**

```bash
cd ../personal-finances-frontend
git checkout main && git pull origin main
git checkout -b develop
git push origin develop
```

Expected: branch `develop` appears on `github.com/nathanfiorito/personal-finances-frontend`.

---

## Task 2: Backend — add CI workflow

**Files:**
- Create: `personal-finances-backend/.github/workflows/ci.yml`

- [ ] **Step 1: Create the workflow file**

Create `personal-finances-backend/.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
    branches:
      - 'feature/**'
  pull_request:
    branches:
      - develop
      - main

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: 'pip'
      - run: pip install ruff
      - run: ruff check src/

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: 'pip'
      - run: pip install -r requirements.txt
      - run: pytest tests/ -v

  docker-build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - run: docker build .
```

- [ ] **Step 2: Commit and push to a feature branch to trigger CI**

```bash
cd personal-finances-backend
git checkout develop
git checkout -b feature/add-ci-workflow
git add .github/workflows/ci.yml
git commit -m "ci: add GitHub Actions CI workflow"
git push origin feature/add-ci-workflow
```

- [ ] **Step 3: Verify CI runs on GitHub**

Open `github.com/nathanfiorito/personal-finances-backend/actions` and confirm:
- Workflow `CI` appears with 3 jobs: `lint`, `test`, `docker-build`
- All 3 jobs pass (green checkmarks)

If any job fails, fix the issue before continuing.

- [ ] **Step 4: Open PR and merge to `develop`**

```bash
gh pr create \
  --repo nathanfiorito/personal-finances-backend \
  --base develop \
  --head feature/add-ci-workflow \
  --title "ci: add GitHub Actions CI workflow" \
  --body "Adds CI pipeline with lint, test, and docker-build jobs."
```

Confirm CI passes on the PR, then merge:

```bash
gh pr merge --repo nathanfiorito/personal-finances-backend --squash
```

---

## Task 3: Frontend — add CI workflow

**Files:**
- Create: `personal-finances-frontend/.github/workflows/ci.yml`

- [ ] **Step 1: Create the workflow file**

Create `personal-finances-frontend/.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
    branches:
      - 'feature/**'
  pull_request:
    branches:
      - develop
      - main

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci
      - run: npm run lint

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci
      - run: npm run test

  build:
    runs-on: ubuntu-latest
    env:
      NEXT_PUBLIC_SUPABASE_URL: https://placeholder.supabase.co
      NEXT_PUBLIC_SUPABASE_ANON_KEY: placeholder-anon-key
      NEXT_PUBLIC_API_BASE_URL: https://placeholder-api.example.com
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci
      - run: npm run build
```

> **Note:** `NEXT_PUBLIC_*` vars are set to placeholder values so the build succeeds without real credentials. They are embedded at build time and never used at runtime in CI.

- [ ] **Step 2: Commit and push to a feature branch to trigger CI**

```bash
cd personal-finances-frontend
git checkout develop
git checkout -b feature/add-ci-workflow
git add .github/workflows/ci.yml
git commit -m "ci: add GitHub Actions CI workflow"
git push origin feature/add-ci-workflow
```

- [ ] **Step 3: Verify CI runs on GitHub**

Open `github.com/nathanfiorito/personal-finances-frontend/actions` and confirm:
- Workflow `CI` appears with 3 jobs: `lint`, `test`, `build`
- All 3 jobs pass (green checkmarks)

If any job fails, fix the issue before continuing.

- [ ] **Step 4: Open PR and merge to `develop`**

```bash
gh pr create \
  --repo nathanfiorito/personal-finances-frontend \
  --base develop \
  --head feature/add-ci-workflow \
  --title "ci: add GitHub Actions CI workflow" \
  --body "Adds CI pipeline with lint, test, and build jobs."

gh pr merge --repo nathanfiorito/personal-finances-frontend --squash
```

---

## Task 4: Backend — configure branch protection

**Files:** none (GitHub API operations via `gh` CLI)

> **Prerequisite:** Complete Task 2 first. Branch protection check contexts are registered with GitHub only after the CI workflow runs at least once. The context names used below (`lint`, `test`, `docker-build`) match the job keys in the workflow YAML.

- [ ] **Step 1: Protect `main` in the backend repo**

```bash
gh api -X PUT repos/nathanfiorito/personal-finances-backend/branches/main/protection \
  --input - << 'EOF'
{
  "required_status_checks": {
    "strict": false,
    "contexts": ["lint", "test", "docker-build"]
  },
  "enforce_admins": false,
  "required_pull_request_reviews": {
    "required_approving_review_count": 0,
    "dismiss_stale_reviews": false,
    "require_code_owner_reviews": false
  },
  "restrictions": null
}
EOF
```

Expected output: JSON response with `"url": "...branches/main/protection"` and no error.

- [ ] **Step 2: Protect `develop` in the backend repo**

```bash
gh api -X PUT repos/nathanfiorito/personal-finances-backend/branches/develop/protection \
  --input - << 'EOF'
{
  "required_status_checks": {
    "strict": false,
    "contexts": ["lint", "test", "docker-build"]
  },
  "enforce_admins": false,
  "required_pull_request_reviews": {
    "required_approving_review_count": 0,
    "dismiss_stale_reviews": false,
    "require_code_owner_reviews": false
  },
  "restrictions": null
}
EOF
```

- [ ] **Step 3: Verify protection is active**

```bash
gh api repos/nathanfiorito/personal-finances-backend/branches/main/protection \
  --jq '.required_status_checks.contexts'
```

Expected output:
```json
["lint", "test", "docker-build"]
```

Repeat for `develop`:

```bash
gh api repos/nathanfiorito/personal-finances-backend/branches/develop/protection \
  --jq '.required_status_checks.contexts'
```

> **Troubleshooting:** If the `contexts` array shows `[]` after setting it, the check names may differ from the job keys. Open the GitHub Actions run at `github.com/nathanfiorito/personal-finances-backend/actions`, click into a completed `CI` run, and read the exact check names shown. Use those names in the `contexts` array and re-run this step.

---

## Task 5: Frontend — configure branch protection

**Files:** none (GitHub API operations via `gh` CLI)

> **Prerequisite:** Complete Task 3 first (CI must have run at least once).

- [ ] **Step 1: Protect `main` in the frontend repo**

```bash
gh api -X PUT repos/nathanfiorito/personal-finances-frontend/branches/main/protection \
  --input - << 'EOF'
{
  "required_status_checks": {
    "strict": false,
    "contexts": ["lint", "test", "build"]
  },
  "enforce_admins": false,
  "required_pull_request_reviews": {
    "required_approving_review_count": 0,
    "dismiss_stale_reviews": false,
    "require_code_owner_reviews": false
  },
  "restrictions": null
}
EOF
```

- [ ] **Step 2: Protect `develop` in the frontend repo**

```bash
gh api -X PUT repos/nathanfiorito/personal-finances-frontend/branches/develop/protection \
  --input - << 'EOF'
{
  "required_status_checks": {
    "strict": false,
    "contexts": ["lint", "test", "build"]
  },
  "enforce_admins": false,
  "required_pull_request_reviews": {
    "required_approving_review_count": 0,
    "dismiss_stale_reviews": false,
    "require_code_owner_reviews": false
  },
  "restrictions": null
}
EOF
```

- [ ] **Step 3: Verify protection is active**

```bash
gh api repos/nathanfiorito/personal-finances-frontend/branches/main/protection \
  --jq '.required_status_checks.contexts'
```

Expected output:
```json
["lint", "test", "build"]
```

---

## Task 6: Coolify — configure staging and production apps

**Files:** none (manual configuration in Coolify UI on your VPS)

These are manual steps in the Coolify dashboard. You will create two separate applications pointing to the same GitHub repo.

- [ ] **Step 1: Connect your GitHub account to Coolify**

In Coolify → Settings → Source → GitHub → connect via GitHub App or OAuth token. Grant access to `nathanfiorito/personal-finances-backend`.

- [ ] **Step 2: Create the staging app**

In Coolify → New Resource → Application:
- **Source:** GitHub → `nathanfiorito/personal-finances-backend`
- **Branch:** `develop`
- **Name:** `personal-finances-backend-staging`
- **Build Pack:** Dockerfile (Coolify auto-detects the `Dockerfile` in the repo root)
- **Port:** `8000`
- **Deploy on push:** enabled

Add all required environment variables (same as `.env` in your local dev, but pointing to a staging Supabase project or the same one with a different schema if you want environment isolation).

- [ ] **Step 3: Create the production app**

In Coolify → New Resource → Application:
- **Source:** GitHub → `nathanfiorito/personal-finances-backend`
- **Branch:** `main`
- **Name:** `personal-finances-backend-prod`
- **Build Pack:** Dockerfile
- **Port:** `8000`
- **Deploy on push:** enabled

Add all production environment variables.

- [ ] **Step 4: Verify webhook is registered on GitHub**

In GitHub → `nathanfiorito/personal-finances-backend` → Settings → Webhooks, confirm Coolify's webhook URL appears (one per Coolify app). Both `develop` and `main` push events should be listed.

- [ ] **Step 5: Trigger a test deploy**

Push a trivial commit to `develop`:

```bash
cd personal-finances-backend
git checkout develop
git commit --allow-empty -m "chore: trigger staging deploy test"
git push origin develop
```

In Coolify, open `personal-finances-backend-staging` → Deployments and confirm a new deploy started and completed successfully.

---

## Verification: End-to-End Flow

After completing all tasks, run through the full Gitflow loop once to confirm everything works:

```bash
# 1. Create a feature branch from develop
cd personal-finances-backend
git checkout develop && git pull origin develop
git checkout -b feature/test-gitflow

# 2. Make a trivial change
echo "# test" >> README.md
git add README.md
git commit -m "test: verify Gitflow CI/CD"
git push origin feature/test-gitflow

# 3. Open PR to develop — CI must run and pass
gh pr create \
  --repo nathanfiorito/personal-finances-backend \
  --base develop \
  --head feature/test-gitflow \
  --title "test: verify Gitflow CI/CD" \
  --body "End-to-end Gitflow verification."

# 4. Confirm: CI runs, all checks green, PR can be merged
# 5. Merge → Coolify staging deploys automatically
gh pr merge --repo nathanfiorito/personal-finances-backend --squash

# 6. Open PR from develop to main
gh pr create \
  --repo nathanfiorito/personal-finances-backend \
  --base main \
  --head develop \
  --title "chore: promote develop to main" \
  --body "Gitflow promotion: develop → main."

# 7. Confirm: CI runs on the PR, merge → Coolify prod deploys automatically
gh pr merge --repo nathanfiorito/personal-finances-backend --squash
```

Revert the README change afterwards if needed:

```bash
git checkout develop && git pull
git revert HEAD --no-edit
git push origin develop
```
