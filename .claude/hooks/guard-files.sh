#!/bin/sh
# PreToolUse hook (matcher "Write|Edit"): stop the agent from writing to
# sensitive files.
#
# stdin: {"tool_name":"Write","tool_input":{"file_path":"...","content":"..."}}
#        (Edit also uses file_path)
#
# exit 0 -> allowed; exit 2 -> blocked, stderr sent back to the model.

set -eu

input=$(cat)
path=$(printf '%s' "$input" | jq -r '.tool_input.file_path // ""')

block() {
	echo "BLOCKED by guard-files.sh: $1" >&2
	echo "Target file: $path" >&2
	exit 2
}

base=$(basename "$path")
case "$base" in
	.env.example|.env.sample) : ;;                 # templates: OK
	.env|.env.*|*.pem|*.key|id_rsa|id_ed25519)
		block "secrets file. Edit .env.example with placeholder values instead, or ask the user." ;;
esac

# internal .git directory: never by hand
case "$path" in
	*/.git/*|.git/*) block "direct edits to the .git directory are not allowed." ;;
esac

exit 0
