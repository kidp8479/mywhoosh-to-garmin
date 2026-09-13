#!/bin/sh
# PostToolUse hook (matcher "Write|Edit"): EXPERIMENTAL.
#
# Goal: close the slop-control loop IN SESSION. The ESLint ratchet
# (notes/eslint-hardening.md) runs at commit / CI time; this runs the
# same linter on the single file the agent just wrote, so it fixes the
# warning now instead of at commit.
#
# PostToolUse runs AFTER the write, so this flags, it does not block.
#   exit 0 -> nothing
#   exit 2 -> stderr sent back to the model (it can fix straight away)
#
# Deliberately conservative: no-ops unless the project actually has a
# local eslint.
#
# Only findings on lines the agent actually touched (vs HEAD) are
# reported. First version reported every eslint finding in the file,
# which contradicts the ratchet design (notes/eslint-hardening.md
# tolerates a nonzero warning baseline): on a real project this fired on
# every pre-existing warning in the file on every edit, as if the agent
# had just caused it. Filtering to changed lines fixes that and is more
# robust than tracking a running warning count, which breaks across
# multiple edits in one session.

set -eu

input=$(cat)
path=$(printf '%s' "$input" | jq -r '.tool_input.file_path // ""')

case "$path" in
	*.ts|*.tsx|*.js|*.jsx|*.mjs|*.cjs) : ;;
	*) exit 0 ;;
esac
[ -f "$path" ] || exit 0

# walk up from the file to the nearest package.json with a local eslint
search_dir=$(CDPATH= cd -- "$(dirname -- "$path")" && pwd)
pkg_dir=""
while [ "$search_dir" != "/" ]; do
	if [ -f "$search_dir/package.json" ] && [ -x "$search_dir/node_modules/.bin/eslint" ]; then
		pkg_dir="$search_dir"
		break
	fi
	search_dir=$(dirname "$search_dir")
done
[ -n "$pkg_dir" ] || exit 0

# lint just this file, quiet (errors only would hide the warn-level slop
# rules, so keep warnings), cap runtime. --format json: ESLint 10 dropped
# the "unix" formatter from core (needs the separate
# eslint-formatter-unix package, not installed here) - a prior version of
# this hook asked for it anyway and silently found nothing, every time.
# json ships with ESLint itself, so parse that with jq instead.
out=$(cd "$pkg_dir" && timeout 30 ./node_modules/.bin/eslint --no-error-on-unmatched-pattern --format json "$path" 2>/dev/null || true)

findings=$(printf '%s' "$out" | jq -r --arg path "$path" '
	.[0].messages[]? |
	"\($path):\(.line):\(.column): " +
	(if .severity == 2 then "error" else "warning" end) +
	"  \(.message)  [\(.ruleId // "")]"
' 2>/dev/null || true)
[ -n "$findings" ] || exit 0

# Keep only findings on lines changed since HEAD. A file with no git repo
# above it, or a brand new untracked file, yields no changed-line ranges
# and every finding is kept (fail open on "which file", not silent on a
# new file full of fresh warnings).
file_dir=$(CDPATH= cd -- "$(dirname -- "$path")" && pwd)
repo_root=$(cd "$file_dir" && git rev-parse --show-toplevel 2>/dev/null || true)
if [ -n "$repo_root" ]; then
	abs_path=$(CDPATH= cd -- "$file_dir" && pwd)/$(basename -- "$path")
	rel_path=${abs_path#"$repo_root"/}
	changed_lines=$(cd "$repo_root" && git diff -U0 HEAD -- "$rel_path" 2>/dev/null | awk '
		/^@@/ {
			split($3, a, ",")
			start = substr(a[1], 2) + 0
			count = (a[2] == "" ? 1 : a[2] + 0)
			for (i = 0; i < count; i++) print start + i
		}
	')
	if [ -n "$changed_lines" ]; then
		findings=$(printf '%s\n' "$findings" | awk -F: -v lines="$changed_lines" '
			BEGIN { n = split(lines, arr, "\n"); for (i = 1; i <= n; i++) keep[arr[i]] = 1 }
			{ if ($2 in keep) print }
		')
	fi
fi
[ -n "$findings" ] || exit 0

echo "lint-feedback.sh: eslint findings on lines you just touched in $path:" >&2
printf '%s\n' "$findings" >&2
echo "Fix these now (see skills/anti-slop). Do not disable the rule." >&2
exit 2
