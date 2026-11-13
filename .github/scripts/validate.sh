#!/usr/bin/env bash
# Structural checks for every skill under skills/, plus pr-ci.sh verdict logic.
set -euo pipefail
cd "$(dirname "$0")/../.."

fail=0
err() { echo "error: $*" >&2; fail=1; }

for dir in skills/*/; do
  dir=${dir%/}; skill=${dir#skills/}
  md=$dir/SKILL.md
  [[ -f $md ]] || { err "$dir has no SKILL.md"; continue; }
  [[ $(sed -n 1p "$md") == --- ]] || err "$md must start with frontmatter"
  front=$(sed -n '2,/^---$/p' "$md")
  [[ $(sed -n 's/^name: *//p' <<<"$front") == "$skill" ]] || err "$md: name must equal '$skill'"
  grep -q '^description:' <<<"$front" || err "$md lacks a description"

  # Paths a skill mentions must exist; every bundled file must be mentioned.
  while read -r path; do
    [[ -e $dir/$path ]] || err "$md mentions missing $path"
  done < <(grep -rhoE '(references|scripts)/[A-Za-z0-9_.-]+\.(md|sh)' "$dir" | sort -u)
  for f in "$dir"/references/*.md "$dir"/scripts/*.sh; do
    [[ -e $f ]] || continue
    grep -q "${f#"$dir"/}" "$md" || err "$f is not mentioned in $md"
  done

  grep -q "\`$skill\`" README.md || err "README.md does not list $skill"
done

# pr-ci.sh classification, offline.
ci=skills/lead-agent-workflow/scripts/pr-ci.sh
check() {
  local want=$1 workflows=$2 json=$3 got
  got=$(PR_CI_CLASSIFY_ONLY=$workflows bash "$ci" 1 <<<"$json")
  [[ $got == "$want"* ]] || err "classify($json) = '$got', want '$want'"
}
check NO_RUN  1 '[]'
check PENDING 1 '[{"name":"a","bucket":"pending","workflow":"ci","link":""}]'
check RED     1 '[{"name":"a","bucket":"fail","workflow":"ci","link":"u"}]'
check GREEN   1 '[{"name":"a","bucket":"pass","workflow":"ci","link":""}]'
check NO_RUN  1 '[{"name":"scan","bucket":"pass","workflow":"","link":""}]'
check GREEN   0 '[{"name":"scan","bucket":"pass","workflow":"","link":""}]'

exit $fail
