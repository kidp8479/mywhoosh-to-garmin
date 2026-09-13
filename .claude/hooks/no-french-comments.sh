#!/bin/sh
# PostToolUse hook (matcher "Write|Edit"): EXPERIMENTAL.
#
# Goal: automate the Hypertube rule "check no French comment slipped into
# the code before merging".
#
# PostToolUse runs AFTER the write, so this does not block: it flags.
# exit 0 -> nothing; exit 2 -> message sent back to the model (it can fix).
#
# Deliberately simple heuristic. Word list measured against 272 real
# comment lines in Hypertube (2026-09-11): "on", "car", "un", "est" fired
# 34 false positives (12.5%), all on ordinary English ("relies on
# handlers", "on login", "the car object"). Dropped from the list below;
# 0 false positives on the same corpus after that, true positive still
# caught on a synthetic French comment.

set -eu

input=$(cat)
path=$(printf '%s' "$input" | jq -r '.tool_input.file_path // ""')

# only care about code files
case "$path" in
	*.ts|*.tsx|*.js|*.jsx|*.c|*.h|*.cpp|*.hpp|*.go|*.py|*.rs) : ;;
	*) exit 0 ;;
esac

[ -f "$path" ] || exit 0

# comment lines only (// or # or * at the start of the line)
comments=$(grep -nE '^\s*(//|#|\*)' "$path" || true)
[ -n "$comments" ] || exit 0

# common French markers in comments, low ambiguity with English
hits=$(printf '%s\n' "$comments" | grep -inE \
	'\b(le|la|les|une|des|du|sont|avec|pour|dans|mais|donc|parce que|ça|cela|être|faire|faut|ici|cette|qui|que|quoi|pas de|il faut|permet|renvoie|vérifie)\b' \
	|| true)

if [ -n "$hits" ]; then
	echo "no-french-comments.sh: possibly French comment in $path" >&2
	printf '%s\n' "$hits" >&2
	echo "Code and comments must be in English. Fix if this is indeed French." >&2
	exit 2
fi

exit 0
