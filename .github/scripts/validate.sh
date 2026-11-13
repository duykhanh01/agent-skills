#!/usr/bin/env bash
# Structural checks for the skill: frontmatter, referenced files, and pr-ci.sh verdict logic.
set -euo pipefail
cd "$(dirname "$0")/../.."

fail=0
err() { echo "error: $*" >&2; fail=1; }

[[ $(sed -n 1p SKILL.md) == --- ]] || err "SKILL.md must start with frontmatter"
name=$(sed -n '/^---$/,/^---$/p' SKILL.md | sed -n 's/^name: *//p')
[[ $name == lead-agent-workflow ]] || err "frontmatter name is '$name'"
sed -n '/^---$/,/^---$/p' SKILL.md | grep -q '^description:' || err "frontmatter lacks description"

# Every references/ or scripts/ path mentioned anywhere must exist.
while read -r path; do
  [[ -e $path ]] || err "referenced path does not exist: $path"
done < <(grep -rhoE '(references|scripts)/[A-Za-z0-9_.-]+\.(md|sh)' SKILL.md README.md references scripts | sort -u)

# Every file in references/ and scripts/ must be reachable from SKILL.md or README.md.
for f in references/*.md scripts/*.sh; do
  grep -q "$f" SKILL.md README.md || err "$f is not mentioned in SKILL.md or README.md"
done

# pr-ci.sh classification, offline.
check() {
  local want=$1 workflows=$2 json=$3 got
  got=$(PR_CI_CLASSIFY_ONLY=$workflows bash scripts/pr-ci.sh 1 <<<"$json")
  [[ $got == "$want"* ]] || err "classify($json) = '$got', want '$want'"
}
check NO_RUN  1 '[]'
check PENDING 1 '[{"name":"a","bucket":"pending","workflow":"ci","link":""}]'
check RED     1 '[{"name":"a","bucket":"fail","workflow":"ci","link":"u"}]'
check GREEN   1 '[{"name":"a","bucket":"pass","workflow":"ci","link":""}]'
check NO_RUN  1 '[{"name":"scan","bucket":"pass","workflow":"","link":""}]'
check GREEN   0 '[{"name":"scan","bucket":"pass","workflow":"","link":""}]'

exit $fail
