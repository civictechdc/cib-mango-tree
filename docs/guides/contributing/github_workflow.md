# GitHub Contribution Workflow

Complete [Installation](../get-started/installation.md) first. For the big picture of contributing a new analyzer (“test”), see the [New Contributor Guide](./new_contributor_guide.md).

All code changes go through a **fork** and a **pull request (PR)** into the upstream [`main`](https://github.com/civictechdc/cib-mango-tree) branch. Maintainers cut releases from `main`.

If you use AI tools while contributing, follow the project [AI Use Policy](https://github.com/civictechdc/cib-mango-tree/blob/main/AI_POLICY.md).

## Opening a pull request

1. **Fork the repository** on GitHub: open [civictechdc/cib-mango-tree](https://github.com/civictechdc/cib-mango-tree) and click **Fork**.

2. **Point Git at your fork and upstream**

    If you followed Installation, you likely cloned the org repo as `origin`. Either re-clone your fork, or keep that clone and set remotes like this (replace `YOUR-USERNAME`):

    ```bash
    git remote rename origin upstream
    git remote add origin https://github.com/YOUR-USERNAME/cib-mango-tree.git
    git remote -v
    ```

    `origin` should be your fork; `upstream` should be `civictechdc/cib-mango-tree`.

3. **Create a branch** from an up-to-date `main`. Name it after the work (examples: `issue_433`, `fix/…`, `docs/…`, `feature/…`):

    ```bash
    git checkout main
    git pull upstream main
    git checkout -b issue_123
    ```

4. **Commit and push** to your fork:

    ```bash
    git add .
    git commit -m "Describe the change and why."
    git push -u origin issue_123
    ```

5. **Open the pull request** on [civictechdc/cib-mango-tree](https://github.com/civictechdc/cib-mango-tree): **Pull requests** → **New pull request** → **Compare across forks**. Base = org `main`; compare = your fork’s branch. Fill in the PR template, link the issue when there is one (`Fixes #123` / `Closes #123`), wait for CI, and address review feedback.

6. **Keep `main` synced** with upstream, and after merge delete the feature branch on your fork:

    ```bash
    git checkout main
    git pull upstream main
    git push origin main
    git branch -d issue_123
    git push origin --delete issue_123
    ```

## Tips

- Prefer **one concern per PR** (the PR template asks you to limit type and scope).
- Docs-only and UX-handoff changes still use this same fork/PR flow; CI may skip some jobs for paths that do not affect the app.
- For release cutovers, maintainers follow `.github/PULL_REQUEST_TEMPLATE/release.md` — contributors normally do not need that template.
