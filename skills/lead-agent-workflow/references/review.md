# The review loop

```text
reviewer: review the PR
  no findings                 -> ready
  findings -> lead triages
    fix                       -> same coder fixes -> same reviewer re-checks -> repeat
    fix without re-check      -> same coder fixes -> ready
    defer / reject            -> ledger -> ready
```

## Triage

Wait until the reviewer has finished, then judge every finding in one pass. Triage as findings
trickle in and some get forgotten.

Judge each finding on its own evidence:

- A finding needs the line of code it is about and a concrete failing scenario. One that has
  neither goes back to the reviewer once for evidence, and is rejected if none comes.
- Read only the lines in question to settle a doubt.
- A reviewer's severity label is advice. The route is your call.

| Route | When | What happens |
| --- | --- | --- |
| **Fix** | A real defect this change introduced, in the intended case. | Coder fixes; reviewer re-checks. A defect this change caused is never deferred. |
| **Fix without re-check** | Real, small, and the fix is unambiguous: it adds no public surface and guards no state nobody demonstrated. | Coder fixes; CI is the check. |
| **Defer** | Real, but outside this change: another path, a rare case, a small cost, code that was already there. | One checklist line in the PR description, and a line under Deferred in the ledger. |
| **Reject** | Wrong, or it asks for something the goal does not need. | A ruling in the ledger with the reason. |

Anything that weakens a test or a CI gate goes to the user, whatever the route: removed or skipped
tests, loosened assertions, raised thresholds, regenerated snapshots.

## Reviewer sub-agents

A review skill may spawn sub-agents (for example one for standards and one for the spec). The
**reviewer** spawns them, not you: splitting the axes yourself pulls the reviewer's context into
yours. Name the skill in the brief, allow sub-agents explicitly, and ask the reviewer to say how it
ran. If it cannot spawn them it does the axes one after the other. Do not replace the repo's
review skill with a checklist of your own; a first round written that way skipped the skill and
had to be redone.

## Fix rounds

A round is one fix by the coder plus one re-check by the reviewer.

- **The same coder and the same reviewer,** both resumed. The coder knows the task and
  its own reasons; the reviewer knows its own findings.
- **The re-check is narrow.** For each open finding the reviewer answers ADDRESSED or NOT
  ADDRESSED, and it looks for breakage only in the lines the fix touched. Anything new outside
  those lines goes under Deferred and never extends the loop.
- **The coder may disagree.** A pushback with evidence (file and line, a test, command output) is a
  valid answer. You settle the dispute after one exchange; the same argument does not go round
  twice.
- **Keep the PR the size of the goal.** Take the fix that deletes or narrows code over a new guard,
  helper or option. If review grew the diff, cut before the next round.
- After each round, write the ledger: round number, what was addressed, what is open, and the
  head SHA the reviewer last read.

There is no round limit. The loop ends when no blocking finding is open; a loop that stops
converging gets a diagnosis, not a cap.

## When the loop does not converge

If the same finding survives two rounds, or each round opens as many blockers as it closes, find
the cause before sending another round:

- **One root decision keeps producing findings.** Group the findings by the decision they come
  from, settle that decision, then fix.
- **The brief or the spec is unclear,** or coder and reviewer read it differently. Settle it with a
  ruling, or re-brief.
- **The reviewer raises new nits each round.** Look at what truly blocks, defer the rest, move on.
- **The coder cannot see its own problem.** If the user allows escalation, move it to a stronger
  model: change the model on the same agent where the tool can, otherwise start a new coder that
  reads the report file first.
- **The cause is outside the code:** a broken environment or toolchain, missing access, flaky
  infrastructure, or a decision only the user can make. Mark the task `blocked`, leave the PR open,
  record the evidence, and carry on with the other tasks.

When the cause is a dispute rather than a fix the coder can make, rule on the open finding
yourself instead of sending another round:

- the reviewer is wrong, or the point is contestable: reject it, with the reason;
- real, and nothing downstream builds on it: defer it;
- real and load-bearing: rule on the smallest change that unblocks dependent work, or mark the task
  `blocked`.

Rule on findings only at triage or after such a diagnosis. Dropping one mid-loop to end the loop
sooner is a silent discard.

## Same agent or a new one

The first review of any PR goes to an agent that has seen none of the coder's reasoning. After
that, resume the same agents: the coder fixes its own code and the reviewer re-checks its own
findings, whatever the size of the fix.

A new agent comes in two kinds, and they do different jobs.

**A replacement** continues a job the old agent cannot finish: the tool cannot resume it, its
context is very large, or it went down a wrong path. A new coder also replaces one that is stuck
(see above). A replacement picks up where the old one stopped. A replacement coder
reads the report file first; a replacement reviewer gets the open findings and the fix range and
does the narrow re-check, not a new review.

**A fresh review** reads the whole diff again. Whether a fix is "significant" is a call the lead
makes badly, so start one only on a trigger you can check:

1. **A ruling changed a decision the PR is built on,** after its first review. The ledger shows it.
2. **The fixes rewrote much of the PR:** the lines changed by the fix commits
   (`git log --no-merges --shortstat <reviewed-sha>..HEAD`) are more than half of the lines in the
   PR's diff at the reviewed SHA.

Below these, the old reviewer's narrow re-check is the check, however large the coder calls the
fix.

Bound it so it cannot restart the loop:

- **Brief it with the settled list.** The first-review brief, plus a short list from the ledger:
  each earlier finding as its id, one line and its route, and each ruling that touches the PR.
  These are settled. It does not raise them again; if it thinks a ruling is wrong, it says so in
  one line with evidence the ledger does not have, outside its findings. Give it neither the
  coder's report nor the earlier reviewer's reasoning. The list keeps it off old ground; the
  missing reasoning keeps its view independent.
- **It takes over the re-checks.** The fresh reviewer is resumed for every later round and the old
  one is done. A fresh review is never re-checked by another fresh review.
- **Triage its findings as usual,** and reject one that repeats a settled point by citing the
  ruling.

There is no routine fresh review before merge. A new reviewer reading the whole diff nearly always
finds something the first did not, so a fresh review at the end of every PR restarts a loop that
had converged. The first review was already independent, and CI and the narrow re-checks cover the
fixes. On an integration branch the whole-branch review below is the fresh look.

## After a conflict

- Tell the coder which merge caused the conflict and which side wins. It rebases, compares the
  series before and after with `git range-diff`, and pushes with `--force-with-lease`.
- If the resolution combined two features in shared code, have the reviewer check the resolution
  alone before the PR merges. Seam bugs appear only there.
- If the base has moved so far that the PR no longer fits, choose before any rebase: update it,
  rework it, or recommend closing it. Closing a PR needs the user's word.

## Integration branch

When tasks share one integration branch, each task still gets its own review by risk. After the
last task lands on the branch:

- one whole-branch review on the strongest model, pointed at the Deferred list in the ledger;
- one fix agent that takes the complete findings list;
- one narrow re-check of that fix. What remains after it goes to the user with the report.
