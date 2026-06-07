# GitHub Automation

## Branch naming → pull request

Push a branch with one of these prefixes and a PR to the default branch (`main`) is opened automatically if none exists:

| Prefix | Example branch | PR title |
|--------|------------------|----------|
| `feature/` | `feature/retrieval-strategy` | Feature: Retrieval Strategy |
| `bug/` / `bugfix/` / `fix/` | `bug/otp-timeout` | Bug fix: Otp Timeout |
| `hotfix/` | `hotfix/redis-pool` | Hotfix: Redis Pool |
| `chore/` | `chore/ci-cache` | Chore: Ci Cache |
| `docs/` | `docs/docker-setup` | Docs: Docker Setup |
| `refactor/` | `refactor/fetch-queue` | Refactor: Fetch Queue (draft) |

Workflow: [open-pull-request.yml](workflows/open-pull-request.yml)

Features and refactors open as **draft** PRs; fixes and hotfixes open as ready for review.

### One-time repo setup (required)

In **Settings → Actions → General → Workflow permissions**:

1. Select **Read and write permissions**
2. Enable **Allow GitHub Actions to create and approve pull requests**

Or via CLI (repo admin):

```bash
gh api repos/OWNER/REPO/actions/permissions/workflow -X PUT \
  -f default_workflow_permissions=write \
  -F can_approve_pull_request_reviews=true
```

Optional: add a `BOT_PAT` repository secret (fine-grained PAT with pull requests + contents write) if your org blocks the setting above.

## Release tags

Version is read from `pyproject.toml` (`version = "0.1.0"` → tag `v0.1.0`).

| Trigger | Behavior |
|---------|----------|
| Push to `main` with **version bump** in `pyproject.toml` | Creates tag `v{X.Y.Z}` and GitHub Release |
| Push existing tag `v*.*.*` | Publishes GitHub Release |
| Manual **Run workflow** | Tag + release for current (or overridden) version |

Skip a release on a merge commit: `[skip release]` in the commit message.

Workflow: [release.yml](workflows/release.yml)

### Cut a release

1. Bump version in `pyproject.toml` (and optionally `apps/web/package.json`).
2. Merge to `main`.
3. The release workflow creates `v{X.Y.Z}` and release notes from merged PRs.

Or run **Actions → Release → Run workflow** with an optional version override.
