# Contributing

This guide defines how we contribute to `ai-voice`.

Right now this repository is primarily for the internal team and trusted collaborators. The goal is to keep changes easy to review, easy to test, and easy to merge without creating messy history on `main`.

## Core Rules

- Do not push feature work directly to `main`.
- Always create a feature branch for any code or docs change.
- Keep each branch and PR focused on one clear task.
- Use conventional commit messages.
- Do not commit secrets, tokens, credentials, or `.env` files.

## Branch Workflow

Create a branch from `main` before starting work.

Recommended branch naming:

- `feature/short-description`
- `fix/short-description`
- `docs/short-description`
- `chore/short-description`

Examples:

- `feature/voice-pipeline`
- `fix/login-redirect`
- `docs/update-readme`

## Commit Rules

Use conventional commits.

Examples:

- `feat: add initial Twilio webhook handler`
- `fix: handle missing tenant config`
- `docs: update roadmap wording`
- `chore: clean up local setup notes`

Keep commits small and relevant to the branch purpose. Do not mix unrelated changes in one commit.

## Testing Expectations

Every PR must include a test plan or test result summary.

### Frontend changes

If the change affects frontend behavior, do manual testing for the affected flows before opening the PR.

Examples of what to verify:

- page loads correctly
- navigation works
- form submission works
- no obvious UI breakage
- no console-breaking behavior in the changed flow

In the PR, clearly write what was tested manually.

### Backend changes

If the change affects backend logic, validate it through terminal-based testing.

Preferred workflow:

1. Create a temporary local `pytest` file or temporary backend test only if needed to verify the change.
2. Run the relevant tests in the terminal.
3. Check which tests are failing and fix the issue.
4. Remove the temporary test file before committing if it was created only for local verification.

Do not commit throwaway `pytest` files created only for debugging or one-time local checks.

If a permanent backend test is intentionally part of the feature and meant to stay in the codebase, it should be reviewed like normal code.

### If testing was limited

Do not hide it. Say clearly in the PR what was tested, what was not tested, and why.

## Pull Request Requirements

Each PR should include:

- a short summary of the change
- a test plan or test result summary

Good PRs should also stay focused. One PR should solve one main problem. Avoid mixing refactors, docs edits, bug fixes, and new features unless they truly belong together.

## Review Policy

For normal workflow:

- contributors open a PR from their feature branch into `main`
- the repo owner decides whether the PR is ready to merge

At this stage, the repo owner controls merges to `main`. Other contributors should not merge their own work unless explicitly told to do so.

## Merge Strategy

Use **merge commits** when merging PRs.

Do not squash by default.
Do not rebase by default.

The repo should preserve branch history for merged work unless the owner decides otherwise for a special case.

## Practices To Follow

- keep PRs small and reviewable
- use clear branch names
- use clear conventional commit messages
- mention testing honestly
- call out any breaking change explicitly
- keep docs updated when behavior or process changes

## Practices To Avoid

- pushing large feature work directly to `main`
- merging untested changes without saying so
- committing secrets, API keys, credentials, or `.env` files
- mixing unrelated changes in one PR
- shipping breaking changes without calling them out
- force-pushing shared branches without coordination

## PR Template

Use this structure in PR descriptions:

### Summary

What changed?

### Test Plan

What did you test?

Examples:

- manually tested login and dashboard flow
- ran backend checks in terminal
- verified affected API behavior locally
- not fully tested yet because `reason`

## Final Reminder

The standard path is:

1. branch from `main`
2. make one focused change
3. test it properly
4. open a PR with summary and test plan
5. merge with a merge commit after owner review
