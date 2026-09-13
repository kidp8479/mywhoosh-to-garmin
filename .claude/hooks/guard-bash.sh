#!/bin/sh
# PreToolUse hook (matcher "Bash"): deterministic safety net.
#
# The harness sends a JSON object on stdin:
#   {"tool_name":"Bash","tool_input":{"command":"..."},...}
#
# PreToolUse output contract:
#   exit 0  -> the tool call proceeds normally
#   exit 2  -> the call is BLOCKED, stderr is sent back to the model
#   other   -> non-blocking error (message shown, call proceeds)
#
# POSIX sh + jq, to stay portable (home Docker / school Podman).

set -eu

input=$(cat)
cmd=$(printf '%s' "$input" | jq -r '.tool_input.command // ""')

# Refuse and explain. The reason goes to the model, which should adapt
# rather than retry verbatim.
block() {
	echo "BLOCKED by guard-bash.sh: $1" >&2
	echo "Refused command: $cmd" >&2
	exit 2
}

case "$cmd" in
	*--no-verify*)
		block "--no-verify bypasses the pre-commit hook. Fix formatting/lint and re-commit." ;;
esac

# push --force / -f: dangerous on a shared branch. --force-with-lease is
# tolerated (it fails if someone else pushed in the meantime).
case "$cmd" in
	*"git push"*)
		case "$cmd" in
			*--force-with-lease*) : ;;
			*--force*|*" -f"*|*" -f")
				block "git push --force overwrites remote history. Use --force-with-lease if it is really needed." ;;
		esac ;;
esac

# rm -rf on an absolute root or the home directory: almost always a mistake.
case "$cmd" in
	*"rm -rf /"*|*"rm -rf ~"*|*"rm -rf \$HOME"*|*"rm -fr /"*)
		block "rm -rf on an absolute path or the home directory. Target a specific subdirectory." ;;
esac

# git reset --hard / git clean -fdx: loss of uncommitted work.
# Not forbidden (sometimes useful) but forced through exit 2: the model
# has to rephrase or ask the user.
case "$cmd" in
	*"reset --hard"*|*"clean -fdx"*|*"clean -fd "*)
		block "This command destroys uncommitted work. Confirm the intent with the user first." ;;
esac

exit 0
