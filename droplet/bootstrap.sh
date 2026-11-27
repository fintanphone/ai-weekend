#!/usr/bin/env bash
#
# Workshop droplet bootstrap. Run ONCE, as root, on a clean Ubuntu 24.04 box.
#
#   ./bootstrap.sh
#
# It is safe to run again: every step checks before it acts. If a step fails,
# fix the cause and re-run — you will not get duplicate users or a second swap
# file.
#
# What it expects next to it:
#
#   keys/alice.pub          one SSH public key per person. The FILENAME becomes
#   keys/bob.pub            the Unix username, so name them carefully.
#   keys/carol.pub
#   ai-agents-weekend/      the repo (a directory or a .zip)
#
# What it deliberately does NOT do:
#
#   * put anybody's Anthropic API key anywhere. Each person adds their own to
#     their own ~/ai-agents-weekend/.env after first login.
#   * give the workshop users sudo. They do not need it.
#   * export ANTHROPIC_API_KEY into the shell. If it were in the environment,
#     Claude Code would offer to bill Lab 7 against your prepaid API credit
#     instead of using its own login. Keeping it in .env, where only
#     python-dotenv looks, avoids that.
#
set -Eeuo pipefail

# --------------------------------------------------------------- settings
# Relative to where you RUN it, not where it lives — so the documented flow
# (cd /root, with keys/ and ai-agents-weekend/ both there) needs no arguments.
KEYDIR="${KEYDIR:-./keys}"
REPO_SRC="${REPO_SRC:-./ai-agents-weekend}"
VENV="${VENV:-/opt/workshop-venv}"
SWAP_GB="${SWAP_GB:-2}"
NODE_MAJOR="${NODE_MAJOR:-22}"

GREEN=$'\033[32m'; RED=$'\033[31m'; YELL=$'\033[33m'; DIM=$'\033[90m'; OFF=$'\033[0m'
step() { printf '\n%s==> %s%s\n' $'\033[1m' "$1" "$OFF"; }
ok()   { printf '    %s✓%s %s\n' "$GREEN" "$OFF" "$1"; }
skip() { printf '    %s·%s %s\n' "$DIM" "$OFF" "$1"; }
warn() { printf '    %s!%s %s\n' "$YELL" "$OFF" "$1"; }
die()  { printf '\n    %s✗ %s%s\n\n' "$RED" "$1" "$OFF" >&2; exit 1; }

USERS=()

# --------------------------------------------------------------- 1. preflight
preflight() {
    step "Preflight"
    [[ $EUID -eq 0 ]] || die "Run this as root."
    . /etc/os-release
    [[ "${VERSION_ID:-}" == "24.04" ]] || warn "Expected Ubuntu 24.04, found ${PRETTY_NAME:-unknown}. Continuing."

    # Resolve to absolute paths before anything else, so no later step depends
    # on the directory this was launched from.
    [[ -d "$KEYDIR" ]] || die "No keys directory at '$KEYDIR' (looked from $PWD).
      Create it and put one .pub file in it per person, or pass KEYDIR=/path."
    KEYDIR=$(cd "$KEYDIR" && pwd)

    if [[ -d "$REPO_SRC" ]]; then
        REPO_SRC=$(cd "$REPO_SRC" && pwd)
    elif [[ -f "${REPO_SRC}.zip" ]]; then
        REPO_SRC="$(cd "$(dirname "$REPO_SRC")" && pwd)/$(basename "$REPO_SRC")"
    else
        local found msg me
        me="${BASH_SOURCE[0]}"
        found=$(find /root /home "$PWD" -maxdepth 4 -name requirements.txt \
                     -not -path '*/.*' -printf '        %h\n' 2>/dev/null | sort -u | head -5)
        msg="No repo at '$REPO_SRC' and no '${REPO_SRC}.zip' (looked from $PWD).
      The venv is built from its requirements.txt, so this is fatal."
        if [[ -n "$found" ]]; then
            msg+="

      A repo looks like it is actually here:
$found
      Re-run pointing at it:
        REPO_SRC=<path from above> bash $me"
        fi
        die "$msg"
    fi
    ok "keys:  $KEYDIR"
    ok "repo:  $REPO_SRC"

    shopt -s nullglob
    local f
    for f in "$KEYDIR"/*.pub; do
        local u; u=$(basename "$f" .pub)
        [[ "$u" =~ ^[a-z][a-z0-9_-]{1,31}$ ]] || die "'$u' is not a usable Unix username (from $f)."
        # A copied-but-not-renamed key file is a valid username and a useless
        # account. Catch it rather than silently creating a user called
        # 'id_ed25519' that nobody will think to log in as.
        case "$u" in
            id_*|*_rsa|*_ed25519|*_ecdsa|authorized_keys|key|pubkey|ssh-key)
                die "'$f' still has its original filename, so the account would be
      called '$u'. The FILENAME becomes the Unix username — rename it to the
      person's login name first:
        mv $f $(dirname "$f")/yourname.pub" ;;
        esac
        grep -qE '^(ssh-(rsa|ed25519)|ecdsa-sha2-)' "$f" || die "$f does not look like an SSH public key."
        USERS+=("$u")
    done
    shopt -u nullglob
    [[ ${#USERS[@]} -gt 0 ]] || die "No .pub files in $KEYDIR. Nothing to do."
    ok "Will create: ${USERS[*]}"

    # The lockout check. After hardening, root can only get in by SSH key, and
    # the workshop users have no sudo. If root has neither a key nor a password
    # for the web console, a failed step later leaves nobody able to administer
    # the box.
    local rootkey=no rootpw
    [[ -s /root/.ssh/authorized_keys ]] && rootkey=yes
    rootpw=$(passwd -S root 2>/dev/null | awk '{print $2}')
    if [[ "$rootkey" == yes ]]; then
        ok "root has an SSH key — admin access survives hardening"
    elif [[ "$rootpw" == "P" ]]; then
        warn "root has no SSH key. After hardening, your only admin route is the"
        warn "DigitalOcean web console with the root password. Make sure you have it."
    elif [[ "${FORCE:-0}" != "1" ]]; then
        die "root has neither an SSH key nor a password, and the workshop users get no sudo.
      Hardening would leave nobody able to administer this box.
      Fix one of these first:
        ssh-copy-id root@<droplet>          (preferred)
        passwd root                          (then keep it in your password manager)
      Or re-run with FORCE=1 if you are certain."
    fi
}

# --------------------------------------------------------------- 2. packages
apt_base() {
    step "Base packages"
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -qq
    apt-get install -y -qq \
        python3-venv python3-pip build-essential git curl ca-certificates gnupg \
        ufw postgresql unattended-upgrades unzip >/dev/null
    ok "installed"

    cat >/etc/apt/apt.conf.d/20auto-upgrades <<'EOF'
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
EOF
    ok "unattended security upgrades enabled"
}

# --------------------------------------------------------------- 3. swap
swapfile() {
    step "Swap"
    if [[ -e /swapfile ]]; then skip "/swapfile already exists"; return; fi
    fallocate -l "${SWAP_GB}G" /swapfile || dd if=/dev/zero of=/swapfile bs=1M count=$((SWAP_GB*1024)) status=none
    chmod 600 /swapfile
    mkswap -q /swapfile >/dev/null
    swapon /swapfile
    grep -q '^/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' >>/etc/fstab
    ok "${SWAP_GB}G swap on, and in /etc/fstab"
}

# --------------------------------------------------------------- 4. users
make_users() {
    step "User accounts"
    local u
    for u in "${USERS[@]}"; do
        if id "$u" &>/dev/null; then
            skip "$u exists"
        else
            adduser --disabled-password --gecos "" "$u" >/dev/null
            ok "created $u (no password, no sudo)"
        fi
        # 700, or each person can read the others' .env — and so their API key.
        chmod 700 "/home/$u"
        install -d -m 700 -o "$u" -g "$u" "/home/$u/.ssh"
        install -m 600 -o "$u" -g "$u" "$KEYDIR/$u.pub" "/home/$u/.ssh/authorized_keys"
    done
    ok "home directories are 0700; keys installed"
}

# --------------------------------------------------------------- 5. sshd
harden_ssh() {
    step "SSH hardening"
    # Ubuntu's sshd_config includes sshd_config.d/*.conf on its FIRST line, and
    # for any keyword sshd uses the FIRST value it reads. DigitalOcean images
    # ship 50-cloud-init.conf turning password auth back on, so this file has to
    # sort before it. Hence 00-, not 99-.
    cat >/etc/ssh/sshd_config.d/00-workshop.conf <<'EOF'
# Workshop box: keys only, no root over SSH.
PasswordAuthentication no
KbdInteractiveAuthentication no
PermitRootLogin prohibit-password
X11Forwarding no
MaxAuthTries 3
EOF

    sshd -t || die "sshd rejected the new config; nothing was restarted."

    # Check the EFFECTIVE value, not just that we wrote a file — another
    # drop-in could still be winning.
    local effective
    effective=$(sshd -T 2>/dev/null | awk '/^passwordauthentication /{print $2}')
    if [[ "$effective" != "no" ]]; then
        rm -f /etc/ssh/sshd_config.d/00-workshop.conf
        die "Password auth is still '$effective' — another drop-in overrides us. Config reverted, sshd untouched."
    fi

    systemctl restart ssh 2>/dev/null || systemctl restart sshd
    ok "keys only; root login by key only; sshd restarted"

    # Say this HERE, not only in the summary. Password auth is off as of this
    # second, and the remaining steps take minutes — long enough that a failure
    # in one of them would otherwise mean never seeing the login names at all.
    local ip; ip=$(hostname -I | awk '{print $1}')
    printf '\n    %sTest this NOW, in another terminal, while this session is open:%s\n' $'\033[1m' "$OFF"
    local u; for u in "${USERS[@]}"; do printf '        ssh %s@%s\n' "$u" "$ip"; done
    printf '    %sIf that fails, fix it from here before closing this session.%s\n' "$YELL" "$OFF"
}

# --------------------------------------------------------------- 6. firewall
firewall() {
    step "Host firewall (second layer; the DO cloud firewall is the first)"
    ufw allow OpenSSH >/dev/null
    ufw --force enable >/dev/null
    ok "ufw: inbound 22 only, outbound open"
}

# --------------------------------------------------------------- 7. postgres
postgres_setup() {
    step "PostgreSQL — one database per person"
    systemctl enable --now postgresql >/dev/null 2>&1 || true
    local u
    for u in "${USERS[@]}"; do
        if sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='$u'" | grep -q 1; then
            skip "role $u exists"
        else
            sudo -u postgres createuser "$u"
            ok "role $u"
        fi
        if sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='support_$u'" | grep -q 1; then
            skip "database support_$u exists"
        else
            sudo -u postgres createdb -O "$u" "support_$u"
            ok "database support_$u"
        fi
        # PostgreSQL grants CONNECT on a new database to PUBLIC, so without
        # this every user can open everyone else's. They still could not read
        # the tables, but a box that teaches scoping should be scoped.
        sudo -u postgres psql -q -c "REVOKE CONNECT ON DATABASE \"support_$u\" FROM PUBLIC"
    done
    ok "peer auth on the local socket — no passwords to distribute"
    ok "each database is reachable only by its owner"
}

# --------------------------------------------------------------- 8. python
python_venv() {
    step "Shared Python environment at $VENV"
    [[ -d "$VENV" ]] || python3 -m venv "$VENV"
    "$VENV/bin/python" -m pip install -q --upgrade pip

    # CPU-only torch FIRST. Left to itself, sentence-transformers pulls ~2.4 GB
    # of NVIDIA CUDA wheels onto a droplet with no GPU.
    step "  torch (CPU build — saves ~2.4 GB of CUDA wheels)"
    "$VENV/bin/pip" install -q --index-url https://download.pytorch.org/whl/cpu torch \
        || warn "CPU index unreachable; falling back to the default index (large download)"

    step "  workshop requirements"
    "$VENV/bin/pip" install -q -r "$REPO_DIR/requirements.txt"
    "$VENV/bin/pip" install -q "psycopg[binary]"      # Lab 3b against PostgreSQL

    chmod -R a+rX "$VENV"
    ok "$("$VENV/bin/python" -V), readable by everyone, writable by root only"
}

# --------------------------------------------------------------- 9. node + cc
node_and_claude() {
    step "Node.js (Lab 6 runs MCP servers with npx)"
    if command -v node &>/dev/null && [[ "$(node -v | tr -d v | cut -d. -f1)" -ge 20 ]]; then
        skip "node $(node -v) already present"
    else
        curl -fsSL "https://deb.nodesource.com/setup_${NODE_MAJOR}.x" | bash - >/dev/null 2>&1 \
            && apt-get install -y -qq nodejs >/dev/null \
            && ok "node $(node -v) from NodeSource" \
            || { apt-get install -y -qq nodejs npm >/dev/null
                 warn "NodeSource unreachable; installed Ubuntu's node $(node -v). Fine for npx." ; }
    fi

    step "Claude Code (Lab 7)"
    if command -v claude &>/dev/null; then
        skip "claude $(claude --version 2>/dev/null | head -1) already present"
        return
    fi
    # The signed apt repo, not npm: one system-wide copy for all three users,
    # no Node version constraint, and no 'sudo npm install -g'.
    install -d -m 0755 /etc/apt/keyrings
    if curl -fsSL https://downloads.claude.ai/keys/claude-code.asc \
            -o /etc/apt/keyrings/claude-code.asc 2>/dev/null \
       && gpg --show-keys /etc/apt/keyrings/claude-code.asc 2>/dev/null \
            | tr -d ' ' | grep -q 31DDDE24DDFAB679F42D7BD2BAA929FF1A7ECACE; then
        echo "deb [signed-by=/etc/apt/keyrings/claude-code.asc] https://downloads.claude.ai/claude-code/apt/stable stable main" \
            >/etc/apt/sources.list.d/claude-code.list
        apt-get update -qq && apt-get install -y -qq claude-code >/dev/null
        ok "claude $(claude --version 2>/dev/null | head -1) (apt, signing key verified)"
    else
        rm -f /etc/apt/keyrings/claude-code.asc /etc/apt/sources.list.d/claude-code.list
        warn "Could not fetch or verify the Claude Code signing key."
        warn "Install it by hand later:  curl -fsSL https://claude.ai/install.sh | bash"
    fi
}

# --------------------------------------------------------------- 10. the repo
place_repo() {
    step "The repo, one copy per person"
    if [[ ! -d "$REPO_DIR" ]]; then warn "no repo staged; skipping"; return; fi
    local u dest
    for u in "${USERS[@]}"; do
        dest="/home/$u/ai-agents-weekend"
        if [[ -d "$dest" ]]; then
            skip "$u already has a copy (left untouched)"
        else
            mkdir -p "$dest"
            # tar rather than rsync: always present, and it keeps this step
            # working even if the package install was interrupted.
            # facilitator/ holds the Lab 7 answer key and the cut-list. It is
            # gitignored, but /root may still have it, and this is the step
            # that would quietly hand it to everybody.
            (cd "$REPO_DIR" && tar --exclude=.git --exclude=.env \
                 --exclude=__pycache__ --exclude='*.pyc' \
                 --exclude=facilitator --exclude=fake_pi_home -cf - .) | tar -xf - -C "$dest"
            ok "$u"
        fi
        [[ -f "$dest/.env" ]] || cp "$dest/.env.example" "$dest/.env" 2>/dev/null || true
        chown -R "$u:$u" "$dest"
        chmod 600 "$dest/.env" 2>/dev/null || true

        # Activate the shared venv on login, and point Lab 3b at this person's
        # own database. `unset DATABASE_URL` goes back to the SQLite default.
        if ! grep -q workshop-venv "/home/$u/.bashrc"; then
            cat >>"/home/$u/.bashrc" <<EOF

# --- workshop ---
source $VENV/bin/activate
export DATABASE_URL="postgresql:///support_$u"
cd ~/ai-agents-weekend 2>/dev/null || true
EOF
        fi
    done
    ok "each person has their own copy, their own .env (0600) and their own database"
}

# --------------------------------------------------------------- 11. summary
summary() {
    step "Done"
    local u
    printf '\n    %sVerify from your laptop, in a NEW terminal, before closing this one:%s\n\n' $'\033[1m' "$OFF"
    for u in "${USERS[@]}"; do printf '        ssh %s@%s\n' "$u" "$(hostname -I | awk '{print $1}')"; done
    cat <<EOF

    ${DIM}Then each person, once logged in:${OFF}

        nano ~/ai-agents-weekend/.env     # paste their own ANTHROPIC_API_KEY
        python check_setup.py

    ${DIM}Still to do by hand:${OFF}

        * each person needs their OWN API key (platform.claude.com/settings/keys)
        * leave auto-reload OFF so prepaid credit stays a hard ceiling
        * snapshot the droplet once check_setup.py is green

EOF
}

main() {
    preflight
    # Unpack the repo once, before anything needs it.
    REPO_DIR="$REPO_SRC"
    if [[ ! -d "$REPO_SRC" && -f "${REPO_SRC}.zip" ]]; then
        rm -rf /opt/_repo_src && mkdir -p /opt/_repo_src
        unzip -q "${REPO_SRC}.zip" -d /opt/_repo_src
        REPO_DIR=$(find /opt/_repo_src -maxdepth 2 -name requirements.txt -printf '%h\n' | head -1)
        ok "unpacked ${REPO_SRC}.zip"
    fi
    apt_base
    swapfile
    make_users
    harden_ssh
    firewall
    postgres_setup
    python_venv
    node_and_claude
    place_repo
    summary
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
