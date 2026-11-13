# lead-agent-workflow

An agent skill that lets one lead agent run coding work through worker agents: from a request to
merged pull requests. The lead builds a task graph, dispatches coders and reviewers, runs the
review loop, gates merges on CI, and keeps its own context small.

It is tool-neutral. Cards for Paseo, T3 Code and Claude Code
are in `references/tools.md`; other tools fall back to a generic probe-and-adapt procedure.

## What is in it

| Path | Purpose |
| --- | --- |
| `SKILL.md` | The workflow: sizing, task states, seven steps, the lead loop, defaults |
| `references/contracts.md` | Ledger, brief, report and finding formats |
| `references/review.md` | Triage, fix rounds, re-checks, round cap |
| `references/supervision.md` | Waiting, stuck workers, CI verdicts, quota, handover |
| `references/tools.md` | Per-tool cards and the capabilities the skill needs |
| `references/pitfalls.md` | Traps learned from real runs |
| `scripts/pr-ci.sh` | One CI verdict for a PR's head commit (GitHub) |

## Install

Copy or symlink the directory into your agent's skills folder, keeping the name
`lead-agent-workflow`:

```sh
git clone https://github.com/duykhanh01/lead-agent-workflow ~/.claude/skills/lead-agent-workflow
```

Other agents that read `SKILL.md` skills (for example from `~/.agents/skills/`) work the same way.

## Requirements

- An agent harness that can spawn, resume and wait on worker agents.
- GitHub with the `gh` CLI (authenticated) and `jq` for `scripts/pr-ci.sh`. For another git host,
  see "Git host" in `references/tools.md`.

## Use

Ask explicitly, for example: "orchestrate agents to fix these five issues" or "dispatch coders and
reviewers for this plan". The skill does not trigger for ordinary single-agent work.

The defaults in `SKILL.md` (parallelism, models, merge style) are starting points; override them
in your request or your repository's own rules.

## Status

The tool cards come from the author's own sessions. Items marked "Not verified" in
`references/tools.md` were not tested; treat them as hypotheses and update the card when you do.

## License

Apache License 2.0. See [LICENSE](LICENSE).
