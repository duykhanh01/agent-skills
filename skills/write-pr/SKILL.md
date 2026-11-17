---
name: write-pr
description: Write or update a pull request title and description. Use when opening a PR, filling in a PR template, or revising a PR description after the change has moved on.
---

# Writing a PR description

Use the PR template the caller gives you, as given. Otherwise use the repository's own:
`.github/pull_request_template.md` or one under `.github/PULL_REQUEST_TEMPLATE/`. With no template,
use these headings: Why, Changes, Evidence, Merge risk. This skill covers how to fill in a template
well, not which headings it has. Write in the language the repo's template and history use.

## Before writing

- **Check for an existing open PR.** Determine the target repo, head owner/branch and base, then
  query `gh pr list --repo <owner/repo> --state open --head <head-branch> --base <base> --json number,url,headRepositoryOwner,headRepository`.
  Verify the head repository for fork PRs. Update a matching open PR with `gh pr edit`; do not
  duplicate it. A successful empty query means no open match; an authentication, network or quota
  error does not. Resolve the error (or use REST) before creating. Closed or merged PRs do not
  prevent a new PR for later work on the branch; multiple matches need clarification.
- **Write from the diff, not from memory.** Read `git diff <base>...HEAD` and check it against the
  goal. After several rounds of fixes, describe what the diff contains now, not what you remember
  doing.
- **Screen for secrets and private data.** Check the title, description, quoted logs and attached
  images for tokens, credentials, internal hostnames and personal details before sending.

## Principles

- **Write a specific title.** Name the problem solved or the outcome, not the activity: "Keep the
  cursor visible after a signal", not "Update select code". Follow the repo's title conventions, such
  as a commit-type prefix.
- **Lead with why.** State the problem or need in one to three sentences before describing the change.
- **Describe behaviour, not files.** Say what a user or the system now does differently. The diff
  already lists the files.
- **Show evidence.** Give a concrete before and after: a test that failed and now passes, command
  output, a screenshot. Do not restate the gates and CI checks; they are recorded elsewhere. Say what
  was not verified.
- **State the merge risk.** Ask what a revert would not undo once the change has run: data already
  written in a new format, clients or scripts that already depend on new behaviour, messages already
  sent, data deleted. Nothing means a two-way door. Anything means a one-way door: say exactly where
  rollback stops, and how to go through safely. A changed schema or CLI is not one-way by itself; it
  is when something has come to rely on it. Name the blast radius in a short phrase: what breaks if
  the PR is wrong.
- **Be brief.** Skip preambles. Use the project's own vocabulary, including its glossary if it has one.
- **Keep it accurate.** When later commits change the scope, update the title and description too.
- **Keep follow-ups current.** List deferred work, such as review findings left for later, as a
  checklist in the template's appropriate section. The template controls headings; add a final
  "Follow-ups" heading only when no template exists. Update it on every fix round: tick or drop
  what was done, add what was deferred.

## Filing

- **Follow the caller's and repository's draft policy.** If neither specifies one, open ready so
  checks and bots run. Write multiline descriptions to a file and use `--body-file` with `gh`.
- **Fall back to REST when GraphQL is rate-limited.** Preserve the selected repository, head
  (including fork owner), base, title, body and draft state. For a draft, use:
  `gh api repos/<owner>/<repo>/pulls -f title=... -f head=<head> -f base=<base> -F body=@<file> -F draft=true`.
  Use `-F draft=false` only when ready was selected. For an ambiguous create error, query open PRs
  again before retrying; the server may already have created it. Use
  `gh api -X PATCH repos/<owner>/<repo>/pulls/<number> -F body=@<file>` to update the body; that
  operation preserves draft state. Change draft/ready only through the explicit lifecycle operation.

## Sketching structural changes

A diff is ordered by file. It does not show execution order or where new code sits in a flow. A
sketch of a few lines gives the reviewer that picture before they read the diff.

Add a sketch only when the PR changes structure: control flow, call order, state transitions, module
layout, or how components communicate. Skip it for wording, styling, configuration values, or a
small local fix.

### Choosing a form

Use the smallest form that makes the point. One is usually enough; more than two is rarely needed.
Place the sketch next to the sentence it supports, and keep only the functions, files, states, and
boundaries that point needs. Use the names from the code.

| To show | Use |
| --- | --- |
| Logic, conditions, an algorithm | Pseudocode |
| Call order at runtime | Call tree |
| What each directory or module owns | File tree |
| How components exchange messages | Mermaid `sequenceDiagram` |
| States and transitions | Mermaid `stateDiagram-v2` |
| What changes, when the shape already exists | A `diff` of one of the above |

Read [structural-sketches.md](references/structural-sketches.md) when you need an example of the
selected form or guidance on showing a code block in full.

## Credits

Adapted from Matt Pocock's `pr` skill and Theo Browne's `file-pr` skill. The catalogue of sketches
comes from Dex Horthy's `show-me` skill (HumanLayer). See the bundled [NOTICE.md](NOTICE.md).
