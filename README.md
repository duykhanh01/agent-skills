# agent-skills

Agent skills for running coding work through AI agents: one to lead a team of workers from request
to merged PR, and one to write the pull request. They work in Claude Code and any harness that
reads `SKILL.md` skills.

## Skills

| Skill | Say | What it does |
| --- | --- | --- |
| [`lead-agent-workflow`](skills/lead-agent-workflow) | "orchestrate agents to fix these issues", "dispatch coders and reviewers" | One lead agent builds a task graph, dispatches coders and reviewers, runs the review loop, gates merges on CI, and keeps its own context small. |
| [`write-pr`](skills/write-pr) | "open a PR", "write the PR description" | Writes a short PR that leads with the problem, shows evidence, and states the merge risk. |

`lead-agent-workflow` tells its coders to write PRs with a PR-writing skill. `write-pr` is the one
meant for that, but any other works.

## Install

```bash
git clone https://github.com/duykhanh01/agent-skills
cp -R agent-skills/skills/* ~/.claude/skills/   # Claude Code
cp -R agent-skills/skills/* ~/.agents/skills/   # other harnesses that read this folder
```

Copy only the folders you want. Each skill is self-contained.

## Requirements

- An authenticated [GitHub CLI](https://cli.github.com) (`gh`) and `jq`.
- `lead-agent-workflow` needs a harness that can spawn, resume and wait on worker agents. Cards for
  Paseo, T3 Code and Claude Code are in its `references/tools.md`.

## Make them yours

These are starting points. Edit them. Put personal settings, such as which models coders and
reviewers use, in your `CLAUDE.md` or `AGENTS.md`, so you can update the skills without losing them.

## Credits and license

[MIT](LICENSE). `write-pr` builds on work by Matt Pocock, Theo Browne and HumanLayer; see
[NOTICE.md](NOTICE.md).
