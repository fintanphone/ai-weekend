#!/usr/bin/env bash
#
# Add people to a droplet that bootstrap.sh has already set up.
#
#   cd /root
#   cp /path/to/bob.pub keys/
#   bash ai-agents-weekend/droplet/add_user.sh
#
# Creates an account, a database and a repo copy for every keys/*.pub that
# isn't a user yet, and leaves the existing ones completely alone — including
# their .env, their edits and anything they have run.
#
# It skips the whole-machine work bootstrap.sh already did: no apt, no pip, no
# swap, no sshd restart. Seconds, not minutes, which is what you want when you
# are doing this with people watching.
#
set -Eeuo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# bootstrap.sh only runs main() when executed directly, so sourcing it gives
# us its functions without re-running the install.
# shellcheck source=./bootstrap.sh
source "$HERE/bootstrap.sh"

# Consumed by place_repo in the sourced bootstrap.sh, not by this file.
# shellcheck disable=SC2034
REPO_DIR="$REPO_SRC"
if [[ ! -d "$REPO_SRC" && -f "${REPO_SRC}.zip" ]]; then
    rm -rf /opt/_repo_src && mkdir -p /opt/_repo_src
    unzip -q "${REPO_SRC}.zip" -d /opt/_repo_src
    # shellcheck disable=SC2034
    REPO_DIR=$(find /opt/_repo_src -maxdepth 2 -name requirements.txt -printf '%h\n' | head -1)
fi

[[ -x "$VENV/bin/python" ]] || die "No venv at $VENV — run bootstrap.sh first."

preflight
make_users
postgres_setup
place_repo
summary
