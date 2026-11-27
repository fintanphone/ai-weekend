#!/usr/bin/env bash
#
# Put the repo under git on the droplet, so updates reach everyone with
# `git pull` instead of a re-upload that would flatten their work.
#
#   cd /root
#   bash ai-agents-weekend/droplet/setup_git.sh
#
# Run it once. Afterwards the loop is:
#
#   cd /root/ai-agents-weekend          # you, after dropping in new files
#   git add -A && git commit -m "..." && git push
#
#   cd ~/ai-agents-weekend              # each person, whenever they like
#   git pull
#
# No GitHub and no credentials: the origin is a bare repo on this box at a
# filesystem path, so a clone is just a file read.
#
# Each person's .env is gitignored, so a pull never touches their API key. Their
# own edits survive a pull too, and git shows them as modified files — which
# matters, because half the labs end in a "break it deliberately" section.
#
set -Eeuo pipefail

BARE="${BARE:-/opt/ai-agents-weekend.git}"
SRC="${SRC:-/root/ai-agents-weekend}"
BRANCH=main

GREEN=$'\033[32m'; YELL=$'\033[33m'; DIM=$'\033[90m'; OFF=$'\033[0m'
step() { printf '\n%s==> %s%s\n' $'\033[1m' "$1" "$OFF"; }
ok()   { printf '    %s✓%s %s\n' "$GREEN" "$OFF" "$1"; }
skip() { printf '    %s·%s %s\n' "$DIM" "$OFF" "$1"; }
warn() { printf '    %s!%s %s\n' "$YELL" "$OFF" "$1"; }
die()  { printf '\n    %s✗ %s%s\n\n' $'\033[31m' "$1" "$OFF" >&2; exit 1; }

[[ $EUID -eq 0 ]] || die "Run this as root."
[[ -d "$SRC" ]] || die "No repo at $SRC. Upload it there first."
command -v git >/dev/null || { apt-get update -qq && apt-get install -y -qq git; }

step "Identity for the commits"
git config --global user.name  >/dev/null 2>&1 || git config --global user.name "Workshop"
git config --global user.email >/dev/null 2>&1 || git config --global user.email "workshop@localhost"
git config --global init.defaultBranch "$BRANCH"
# Pushing to a local path makes git try a negotiation the filesystem transport
# doesn't answer. Harmless, but it prints an alarming warning.
git config --global push.negotiate false
ok "$(git config --global user.name) <$(git config --global user.email)>"

step "The origin: a bare repo on this box"
if [[ -d "$BARE" ]]; then
    skip "$BARE exists"
else
    git init --bare -q "$BARE"
    ok "created $BARE"
fi
chmod -R a+rX "$BARE"
# git refuses a repo owned by another user ("dubious ownership"). One
# system-wide exception beats telling three people to run a git config command.
git config --system --add safe.directory "$BARE" 2>/dev/null || true
git config --system --get-all safe.directory | grep -qx "$BARE" \
    && ok "readable by everyone, and trusted system-wide" \
    || warn "could not set safe.directory; users may need to add it themselves"

step "Pushing $SRC into it"
cd "$SRC"
if [[ ! -d .git ]]; then
    git init -q
    git add -A
    git commit -qm "Workshop repo as built"
    ok "initialised and committed $(git ls-files | wc -l) files"
    BRANCH=$(git branch --show-current)
else
    skip "already a git repo"
    BRANCH=$(git branch --show-current)
    [[ -n "$BRANCH" ]] || die "detached HEAD — check out a branch before running this."
    ok "on branch '$BRANCH', which is left as it is"
    if [[ -n "$(git status --porcelain)" ]]; then
        warn "committing these outstanding changes as 'Workshop update':"
        git status --porcelain | head -10 | sed 's/^/        /'
        git add -A && git commit -qm "Workshop update"
    fi
fi

# Never repoint an existing 'origin'. It may be GitHub, and git keeps no record
# of a URL you overwrite, so this would quietly cut the repo off from where it
# actually lives.
REMOTE=origin
if existing=$(git remote get-url origin 2>/dev/null) && [[ "$existing" != "$BARE" ]]; then
    REMOTE=droplet
    warn "origin already points at $existing"
    ok "leaving it alone; adding a second remote named '$REMOTE'"
fi
git remote get-url "$REMOTE" >/dev/null 2>&1 || git remote add "$REMOTE" "$BARE"
git remote set-url "$REMOTE" "$BARE"
git push -q -u "$REMOTE" "$BRANCH"
ok "pushed $(git rev-list --count HEAD) commit(s) to '$REMOTE' ($BRANCH)"
git ls-files | grep -qx ".env" && warn ".env is TRACKED — check .gitignore" \
                              || ok ".env is not tracked, so pulls never touch anyone's key"

step "Converting the copies people already have"
shopt -s nullglob
for home in /home/*; do
    u=$(basename "$home")
    id "$u" &>/dev/null || continue
    dest="$home/ai-agents-weekend"
    [[ -d "$dest" ]] || { skip "$u has no copy"; continue; }
    if [[ -d "$dest/.git" ]]; then skip "$u is already a clone"; continue; fi

    backup="$home/ai-agents-weekend.before-git"
    [[ -e "$backup" ]] && backup="$backup.$(date +%s)"
    mv "$dest" "$backup"
    sudo -u "$u" git clone -q "$BARE" "$dest" \
        || { mv "$backup" "$dest"; die "clone failed for $u; their copy was put back"; }
    # Carry their key across. Everything else they changed is in the backup.
    [[ -f "$backup/.env" ]] && install -m 600 -o "$u" -g "$u" "$backup/.env" "$dest/.env"
    chown -R "$u:$u" "$dest"
    ok "$u → clone (their .env carried over; old copy kept as $(basename "$backup"))"
done
shopt -u nullglob

cat <<EOF

${DIM}From now on:${OFF}

    ${GREEN}you${OFF}, after changing anything in /root/ai-agents-weekend:
        cd /root/ai-agents-weekend && git add -A && git commit -m "what changed"
        git push $REMOTE $BRANCH$([[ "$REMOTE" != origin ]] && printf '%s' "     # and 'git push origin $BRANCH' for your own remote")

    ${GREEN}each person${OFF}, to catch up:
        cd ~/ai-agents-weekend && git pull

${DIM}Their .env is never touched. Their own edits survive and show up in
'git status'. If someone has edits that collide with yours, git will say so —
'git stash' then 'git pull' then 'git stash pop' is the way out.

Tell everyone to check their ai-agents-weekend.before-git folder for anything
they want to keep, then delete it.${OFF}

EOF
