#!/usr/bin/env bash
# Structural checks for every skill, plus offline helper behavior tests.
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
  done < <(grep -rhoE '(references|scripts|templates)/[A-Za-z0-9_.-]+\.(md|sh|py)' "$dir" --include='*.md' --include='*.sh' --include='*.py' | sort -u)
  for f in "$dir"/references/*.md "$dir"/templates/*.md "$dir"/scripts/*.sh "$dir"/scripts/*.py; do
    [[ -e $f ]] || continue
    grep -rq "${f#"$dir"/}" "$dir" --include='*.md' --include='*.sh' || err "$f is not referenced by the skill"
  done

  grep -q "\`$skill\`" README.md || err "README.md does not list $skill"
done

# Offline helper behavior; exercises shell entry points without mutating GitHub.
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s .github/tests -v || fail=1

exit $fail
