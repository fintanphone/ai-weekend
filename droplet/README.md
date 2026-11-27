# Droplet setup, start to finish

For a clean Ubuntu 24.04 droplet you are logged into as `root`, with the
DigitalOcean cloud firewall already configured (inbound TCP 22 only, outbound
left open).

Allow about 25 minutes, most of which is `pip` downloading things.

---

## Before you start

**Make sure root can still get in after hardening.** The script disables
password authentication, and the three workshop users deliberately get no
`sudo`. If root has neither an SSH key nor a password you would have no way to
administer the box, so `bootstrap.sh` refuses to run and tells you so.

If you created the droplet with an SSH key, you are already fine. If you
created it with a password, either copy a key up now:

```bash
ssh-copy-id root@DROPLET_IP
```

or set a root password you keep in your password manager, so the DigitalOcean
web console stays usable. The console gives you a login prompt, and without a
password there is nothing to type at it.

## Setting up for yourself now, adding people later

This is the expected way to do it. Put in only your own key, run the whole
thing, and get the box working while you have time to debug it in peace.

```bash
mkdir -p upload/keys
cp ~/.ssh/id_ed25519.pub upload/keys/alice.pub      # just you
```

Everything below works unchanged — it creates one account instead of three.

When your friends are with you, they generate their own keys, you drop the
`.pub` files into `/root/keys/` and run **`add_user.sh`** instead of
`bootstrap.sh`:

```bash
cd /root
cp bob.pub carol.pub keys/
bash ai-agents-weekend/droplet/add_user.sh
```

That creates the new accounts, databases and repo copies and **leaves existing
users completely alone** — their `.env`, their edits, their outboxes, all
untouched. It skips the machine-wide work that is already done (no apt, no pip,
no swap, no sshd restart), so it finishes in seconds rather than minutes, which
is what you want with people watching.

Re-running `bootstrap.sh` would also work and is equally safe, it just spends a
few minutes re-checking packages first.

**One thing to remember:** new users get their copy from `/root/ai-agents-weekend`,
not from yours. If you have improved the repo in the meantime, re-upload it to
`/root/` before adding them — otherwise they start from the older version.

## Step 1 — stage the files, on your laptop

The script needs two things next to each other: the public keys, and the repo.
**The key filenames become the Unix usernames**, so name them deliberately.

```bash
mkdir -p upload/keys
cp ~/.ssh/id_ed25519.pub        upload/keys/alice.pub
cp /path/to/friend1_key.pub     upload/keys/bob.pub
cp /path/to/friend2_key.pub     upload/keys/carol.pub

cp -r /path/to/ai-agents-weekend upload/
```

Each person generates their own key on their own machine with
`ssh-keygen -t ed25519` and sends you **only the `.pub` file**. If anybody
sends you a private key, tell them to delete it and start again.

Then copy it all up:

```bash
scp -r upload/keys upload/ai-agents-weekend root@DROPLET_IP:/root/
```

## Step 2 — run it, as root on the droplet

```bash
ssh root@DROPLET_IP
cd /root
bash ai-agents-weekend/droplet/bootstrap.sh
```

It prints a banner per stage. It is safe to re-run: every step checks before it
acts, so a failure part-way through means you fix the cause and run it again
rather than rebuilding the droplet.

What it does, in order:

| Stage | What happens |
|---|---|
| Preflight | validates the keys, checks root won't be locked out |
| Base packages | Python, git, build tools, `ufw`, PostgreSQL, unattended security upgrades |
| Swap | 2 GiB swap file, and an `/etc/fstab` entry so it survives a reboot |
| Users | one account per `.pub`, no password, **no sudo**, home directory `0700` |
| SSH | keys only, no root password login, `MaxAuthTries 3` |
| Firewall | `ufw` allowing 22 only — a second layer behind the cloud firewall |
| PostgreSQL | a role and a private database per person |
| Python | shared venv at `/opt/workshop-venv`, CPU-only torch first |
| Node + Claude Code | Node 22 for Lab 6's `npx`; Claude Code from the signed apt repo |
| Repo | a separate copy in each home, with its own `.env` at `0600` |

## Step 3 — verify before you close that session

**Keep the root session open.** In a *new* terminal, confirm each person can
get in:

```bash
ssh alice@DROPLET_IP
```

If that works, hardening succeeded. If it doesn't, you still have the root
session open to fix it. Only close it once a user login works.

## Step 4 — each person, on first login

Logging in drops them straight into `~/ai-agents-weekend` with the shared venv
already active. They need one thing: their own API key.

```bash
nano .env          # paste after ANTHROPIC_API_KEY=
python check_setup.py
```

**One key each, not one shared key.** Create them at
<https://platform.claude.com/settings/keys>. Separate keys mean you can see
whose work is burning the credit and revoke one without disturbing the others.
Leave auto-reload off so the prepaid balance stays a hard ceiling.

## Step 5 — snapshot it

Once `check_setup.py` is green for all three, take a snapshot. Snapshots cost
$0.06/GiB/month, so a configured box costs pennies to keep. It means a January
Part 2 — or recovering from someone running something regrettable — starts from
a working box rather than a bare Ubuntu.

---

## Things worth knowing

**Each person has their own copy of the repo.** That is deliberate: half the
labs end with a "break it deliberately" section, and a shared copy would mean
three people editing the same files. Their `.env` is `0600` and their home
directory is `0700`, so nobody can read anyone else's key.

**Lab 3b points at PostgreSQL, not SQLite.** Each login exports
`DATABASE_URL=postgresql:///support_<user>`, so `seed_db.py` and `agent.py` use
the real server over a Unix socket with peer authentication — no password
anywhere. To demonstrate the SQLite path instead:

```bash
unset DATABASE_URL
python seed_db.py --reset
```

**Nobody has sudo, and that is fine.** The shared venv covers every package the
labs need. Anything extra goes in with `pip install --user`. If you genuinely
need to install a system package, do it yourself as root.

**`ANTHROPIC_API_KEY` is never exported into the shell.** It lives only in
`.env`, where `python-dotenv` finds it. This matters for Lab 7: if the key were
in the environment, Claude Code would offer to bill against your prepaid API
credit instead of using its own login, and agentic coding can get through credit
quickly. Each person should log Claude Code in with `claude` and their own
Claude account.

**Don't port-forward the GPU box to reach it from here.** `llama-server` and
Ollama have no authentication by default. If you want the droplet talking to it,
run a reverse tunnel from the GPU box instead:

```bash
ssh -R 8080:localhost:8080 you@DROPLET_IP       # then LOCAL_API_BASE=http://localhost:8080
```

**Lab servers should bind to localhost**, and you reach them over SSH:

```bash
ssh -L 8080:localhost:8080 alice@DROPLET_IP
```

## If something goes wrong

**`root has neither an SSH key nor a password`** — see *Before you start*. This
is the script refusing to lock you out, not a bug.

**`No repo at './ai-agents-weekend' ... this is fatal`** — you ran it from a
directory that doesn't have the repo beside `keys/`. The message lists where the
repo actually is; re-run pointing at it:

```bash
REPO_SRC=/root/ai-agents-weekend bash ai-agents-weekend/droplet/bootstrap.sh
```

Paths are resolved to absolute ones in preflight, so once it gets past that
banner nothing later depends on where you launched it from.

**`Password auth is still 'yes' — another drop-in overrides us`** — something in
`/etc/ssh/sshd_config.d/` sorts before `00-workshop.conf` and sets it. The
script reverted its own change and left `sshd` running, so you are not locked
out. Find the culprit with `sshd -T | grep passwordauth` and
`ls /etc/ssh/sshd_config.d/`.

**A user can't log in after hardening** — from your still-open root session:

```bash
ls -la /home/alice/.ssh/           # want 700 dir, 600 authorized_keys, owned by alice
journalctl -u ssh -n 30
```

Nine times in ten it's the wrong public key in `keys/alice.pub`.

**`CPU index unreachable; falling back to the default index`** — the PyTorch CPU
wheel index wasn't reachable, so `pip` will pull the CUDA build instead: about
2.4 GB of NVIDIA libraries this droplet can't use. Not fatal, just wasteful. To
redo it:

```bash
/opt/workshop-venv/bin/pip uninstall -y torch
/opt/workshop-venv/bin/pip install --index-url https://download.pytorch.org/whl/cpu torch
```

**`Could not fetch or verify the Claude Code signing key`** — the script leaves
Claude Code uninstalled rather than trusting an unverified key. Install it by
hand with `curl -fsSL https://claude.ai/install.sh | bash`.

**Out of memory during Lab 4** — three people embedding at once on 4 GiB is the
tight case. The swap file absorbs it, slowly. Have them run it one at a time.

**`ModuleNotFoundError` when running something over SSH in one command** — the
venv is activated from `.bashrc`, and Ubuntu's stock `.bashrc` returns early for
non-interactive shells, so `ssh alice@IP 'python check_setup.py'` gets the system
Python. Logging in normally is unaffected. Use the full path when you want a
one-shot remote command:

```bash
ssh alice@IP '/opt/workshop-venv/bin/python ~/ai-agents-weekend/check_setup.py'
```
