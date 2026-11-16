---
name: write-review-comment
description: Post the result of a code review on a pull request as one comment in a fixed format. Use when a review of a PR is finished and its findings need to go on the PR, when re-checking fixes for earlier findings, or when asked to comment review findings on a PR.
---

# Writing a review comment

One review round produces one comment on the PR, and every finding of that round is in it. Never
post one comment per finding, and never split a round across comments. This skill covers how the
comment is written and posted, not how the review is done.

The comment has two readers: a person deciding whether to merge, and an agent that will fix the
findings and may never open the browser. So the verdict comes first, every finding stands on its
own, and nothing depends on GitHub rendering.

Write the comment in English, unless the repo's own rules name another language.

## Before writing

- **Finish the review first.** Write from the complete list of findings.
- **Carry the findings over unchanged.** Do not add, drop, merge or soften findings while
  formatting. A finding that lacks a line of code or a failing scenario is not ready: get the
  evidence, or move it to "Not covered" as something you suspected and could not confirm.
- **Collect the facts the format needs:** the PR number, the base, the full head SHA
  (`gh pr view <number> --json headRefOid,baseRefName`) and the repo
  (`gh repo view --json nameWithOwner`).
- **Look for earlier review comments** on the PR (see "Posting"). They give you the round number,
  the ids already used, and whether this head was already reviewed.

## First review

```markdown
<!-- review-comment round=1 head=<full head SHA> -->
## Review: <Changes needed | No blocking findings> · <n> blocking, <m> not blocking

Reviewed `<base>...<head SHA, 7 chars>` · round 1 · <reviewer: model or agent name>

### Blocking

**F1** · [`<file>:<line>`](<permalink>) · <the defect in one line>
> `<the line of code it is about>`

Fails when: <the input or state, and the wrong result that follows>.
Fix: <what to change>.

### Not blocking

**F2** · [`<file>:<line>`](<permalink>) · <the defect in one line>
> `<the line of code it is about>`

Fails when: <scenario>.
Fix: <what to change>.

### Not covered

- <an area you did not read or could not verify, and why>
```

A filled-in finding:

```markdown
**F1** · [`src/billing/invoice.ts:88`](https://github.com/acme/shop/blob/4f2a9c1e7b3d5a6c8e0f1a2b3c4d5e6f7a8b9c0d/src/billing/invoice.ts#L88) · Discount is applied twice on retry
> `total = total - discount`

Fails when: the payment call times out and `charge()` retries; the second pass subtracts the
discount again, so a 100 order with a 10 discount is charged 80.
Fix: compute `total` from the order lines inside `charge()` instead of mutating it.
```

### Rules

- **The first visible line is the verdict.** "Changes needed" when at least one finding is
  blocking, otherwise "No blocking findings". The counts match the sections below.
- **Blocking** means a defect this change introduces that must be fixed before merge. Everything
  else is not blocking: defects in code that was already there, rare cases, small costs,
  suggestions. Do not invent further severity levels.
- **Ids are `F1`, `F2`, … in one sequence** across both sections, blocking first, most severe
  first within a section. An id never changes and is never reused on the same PR.
- **Each finding has all four parts:** location, quoted line, "Fails when", "Fix".
  - *Location:* the path from the repo root and the line at the reviewed head, linked to a
    permalink: `https://github.com/<owner>/<repo>/blob/<full head SHA>/<path>#L<line>`, or
    `#L<start>-L<end>` for a range. Use the full SHA, never a branch name: a branch link points at
    different code after the next push.
  - *Quoted line:* the one line the finding is about, copied exactly. For a finding about missing
    code, quote the line where it belongs.
  - *Fails when:* one concrete scenario with its wrong result. "May cause issues" is not a
    scenario.
  - *Fix:* the change you suggest, in a sentence. Add a `diff` block only when the sentence would
    be ambiguous. Do not use `suggestion` blocks; they render only in inline review comments.
- **State facts about the code.** No praise, no summary of the diff, no remarks about the author,
  no closing line. The PR description already says what the change does.
- **Leave out an empty findings section.** Always keep "Not covered"; write `- Nothing` when the
  whole diff was read, so the reader knows the section was not forgotten.
- **Zero findings is a valid review.** Post the comment anyway: marker, verdict line, reviewed
  range, "Not covered".
- **Fold a long tail.** With more than five not-blocking findings, wrap that section's findings in
  `<details><summary>Not blocking (<m>)</summary> … </details>`. Never fold blocking findings.
- **Never quote a secret.** When the finding is an exposed credential or personal data, give the
  location and describe it; leave the quoted line out.

## Re-check after fixes

A re-check is a new comment, so the PR timeline shows which commits each round looked at. Reuse
the ids of the earlier rounds.

```markdown
<!-- review-comment round=<n> head=<full head SHA> -->
## Re-check: <Changes needed | No blocking findings> · <n> open

Reviewed `<previous head SHA>..<new head SHA>` · round <n> · <reviewer>

- **F1** ADDRESSED
- **F2** NOT ADDRESSED: <what still fails, in one line>
- **F3** NOT ADDRESSED (not blocking)

### New in the fixed lines

**F4** · [`<file>:<line>`](<permalink>) · <the defect in one line>
> `<the line of code it is about>`

Fails when: <scenario>.
Fix: <what to change>.

### Not covered

- <as in the first review>
```

- List every finding that was still open after the previous round, one line each.
- New findings continue the numbering and come only from the lines the fix touched. Say whether
  each is blocking by adding `(not blocking)` after its title; without it, it is blocking. Leave
  the section out when there are none.
- "Open" in the verdict line counts blocking findings that are not addressed, old and new.

## Posting

Find the review comments already on the PR:

```bash
gh pr view <number> --json comments \
  --jq '.comments[] | select(.body | startswith("<!-- review-comment")) | {url, marker: (.body | split("\n")[0])}'
```

- **No comment for this head SHA:** write the comment to a file and post it once with
  `gh pr comment <number> --body-file <file>`.
- **A comment for this head SHA already exists** (a retried or repeated run): do not post a second
  one. Replace its body: take the numeric id from the end of its URL and run
  `gh api -X PATCH repos/<owner>/<repo>/issues/comments/<id> -F body=@<file>`.
- **Post a plain comment, not a review.** `gh pr review --request-changes` fails when the reviewer
  uses the same account as the PR author, which is the usual case for agents.
- **Fall back to REST when GraphQL is rate-limited:**
  `gh api repos/<owner>/<repo>/issues/<number>/comments -F body=@<file>`.
- **Check that it posted,** then return the comment URL together with the findings to whoever
  asked for the review.

## Credits

The blocking / not-blocking split follows Conventional Comments. "Not covered" is modelled on the
"Declined to judge" section of the code-reviewer prompt in obra/superpowers.
