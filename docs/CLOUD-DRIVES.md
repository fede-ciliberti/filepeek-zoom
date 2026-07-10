# Browsing OneDrive, SharePoint & Google Drive with filepeek

filepeek serves whatever directory `FILEPEEK_ROOT` points at — it doesn't care
whether the files got there by an AI agent, a git clone, or a cloud-drive sync.
So "viewing my OneDrive / SharePoint / Google Drive in filepeek" means one
thing: **make the cloud drive appear as a local folder**, then point filepeek
at it. This guide covers the three ways to do that, from easiest to most
capable.

filepeek itself needs **no configuration** for any of this beyond
`FILEPEEK_ROOT`.

---

## One rule before you start

filepeek's path guard resolves symlinks and refuses anything that lands
outside `FILEPEEK_ROOT` (that's what stops a malicious URL from reading
`/etc/passwd`). A side effect: **a symlink inside your root pointing to a
mount elsewhere will show up but return "Path outside root" when opened.**

Three ways to place the drive correctly, pick one:

1. **Mount or sync directly under your root** — e.g. sync to
   `~/projects/onedrive` when `FILEPEEK_ROOT=~/projects`.
2. **Bind mount** (a real mount, not a symlink — survives path resolution):

   ```bash
   mkdir -p ~/projects/onedrive
   sudo mount --bind ~/OneDrive ~/projects/onedrive
   ```

3. **Raise the root** to a common parent, e.g. `FILEPEEK_ROOT=$HOME`.

---

## Option 1 — Windows sync clients + `/mnt` (WSL2, easiest)

If you run filepeek on WSL2, the sync clients you already have on Windows do
all the work:

| Drive | Setup on Windows | Path in WSL2 |
|---|---|---|
| **OneDrive** | Built in — probably already syncing | `/mnt/c/Users/<you>/OneDrive` |
| **SharePoint** | Open the document library in the browser → **Sync** (or "Add shortcut to OneDrive") | `/mnt/c/Users/<you>/<OrgName>/<Library>` |
| **Google Drive** | Install [Google Drive for Desktop](https://www.google.com/drive/download/) → appears as `G:` | `/mnt/g/My Drive` |

Then:

```bash
FILEPEEK_ROOT="/mnt/c/Users/<you>/OneDrive" .venv/bin/python app.py
```

**Two WSL2 gotchas:**

- **Files On-Demand placeholders.** OneDrive's default keeps files
  cloud-only until opened — and opening them *through WSL* often fails or
  stalls. Right-click the folder in Windows Explorer → **Always keep on this
  device** for anything you want filepeek to browse.
- **Google Drive's `G:` isn't auto-mounted in WSL.** Mount it once with
  `sudo mkdir -p /mnt/g && sudo mount -t drvfs G: /mnt/g`, or add
  `G: /mnt/g drvfs defaults 0 0` to `/etc/fstab`.

Browsing and rendering work fine; note that `/mnt` I/O goes through WSL's 9p
bridge, so **full-text search over a large library will be slow** there.

## Option 2 — rclone mount (any Linux/macOS, all three drives)

[rclone](https://rclone.org) mounts ~70 cloud providers as a FUSE filesystem.
One tool covers OneDrive, SharePoint, *and* Google Drive — and it's the way to
go on a cloud VM running filepeek's remote install.

```bash
sudo apt install rclone     # or https://rclone.org/install/ for the latest
rclone config               # interactive; opens a browser for OAuth
```

During `rclone config`:

- **OneDrive** → backend `onedrive`, pick *OneDrive Personal or Business*.
- **SharePoint** → same `onedrive` backend, pick *Search for a SharePoint
  site*, then choose the document library. A SharePoint library is just
  another remote.
- **Google Drive** → backend `drive`. Strongly consider [creating your own
  OAuth client ID](https://rclone.org/drive/#making-your-own-client-id) —
  rclone's shared default is heavily rate-limited.

Then mount it under your filepeek root:

```bash
mkdir -p ~/projects/onedrive
rclone mount onedrive: ~/projects/onedrive --vfs-cache-mode full --daemon
```

`--vfs-cache-mode full` matters: filepeek can **edit and upload** files, and
without the cache, random-access writes through FUSE fail.

Make it survive reboots with a systemd user service:

```bash
mkdir -p ~/.config/systemd/user
cat > ~/.config/systemd/user/rclone-onedrive.service <<'EOF'
[Unit]
Description=rclone mount: onedrive
After=network-online.target

[Service]
ExecStart=/usr/bin/rclone mount onedrive: %h/projects/onedrive --vfs-cache-mode full
ExecStop=/bin/fusermount -uz %h/projects/onedrive
Restart=on-failure

[Install]
WantedBy=default.target
EOF
systemctl --user enable --now rclone-onedrive
```

(On WSL2 this needs systemd enabled — default on current WSL versions.)

It's a live network filesystem: browsing is snappy after the first listing,
but **full-text search hits the provider's API file by file** — fine for
hundreds of files, sluggish for tens of thousands.

## Option 3 — dedicated sync client (real local files, fastest)

Two-way sync to a real local directory: fastest browsing and search, works
offline, and edits made in filepeek sync back automatically.

**OneDrive & SharePoint** — the [abraunegg onedrive
client](https://github.com/abraunegg/onedrive) is the mature Linux option:

```bash
sudo apt install onedrive
onedrive                              # first run: OAuth in the browser
mkdir -p ~/.config/onedrive
echo 'sync_dir = "/home/<you>/projects/onedrive"' >> ~/.config/onedrive/config
onedrive --sync                       # one-shot sync
onedrive --monitor                    # or: keep watching for changes
```

For a SharePoint document library, find its drive ID with
`onedrive --get-sharepoint-drive-id '<site name>'` and put the printed
`drive_id = "..."` in the config. `--monitor` runs nicely as a systemd user
service too (the package ships one: `systemctl --user enable --now onedrive`).

**Google Drive** — there's no official Linux client. Closest equivalents:
`rclone bisync gdrive: ~/projects/gdrive` on a cron/systemd timer, or
[google-drive-ocamlfuse](https://github.com/astrada/google-drive-ocamlfuse)
as a FUSE mount (same characteristics as Option 2).

---

## Running filepeek in Docker?

Do the mount or sync **on the host**, then pass the folder in as a volume:

```bash
docker run -v ~/projects/onedrive:/data/onedrive ... ghcr.io/thrinz/filepeek
```

Running FUSE *inside* the container needs `--device /dev/fuse
--cap-add SYS_ADMIN` and mount-propagation flags — possible, not worth it.

## Which option should I pick?

| Your setup | Recommendation |
|---|---|
| WSL2, OneDrive/SharePoint | **Option 1** — the sync client is already running; just point `FILEPEEK_ROOT` at `/mnt/c/...` |
| WSL2, Google Drive | Option 1 (Drive for Desktop + `drvfs`) or Option 2 |
| Linux desktop/server, OneDrive/SharePoint | **Option 3** (abraunegg) for speed, Option 2 (rclone) for simplicity |
| Linux desktop/server, Google Drive | **Option 2** — rclone mount |
| Cloud VM (filepeek remote install) | **Option 2** — rclone mount as a system service, mounted under `FILEPEEK_ROOT_DIR` |
| Filepeek in Docker | Any of the above **on the host**, bind-mounted into the container |

## Caveats worth knowing

- **Edits write back.** filepeek's inline editor, uploads, and Track boards
  write to the folder — through a mount or sync client, that reaches the
  cloud. Great for editing a shared doc; be deliberate near shared team
  libraries. (Mirror-mode backup of a cloud mount deserves the same care.)
- **Search speed follows storage speed.** Synced folders (Options 1 & 3 on
  the Linux filesystem) search fast; FUSE mounts and `/mnt/c` are slower.
- **Don't point backup at the same remote.** Backing up a mounted cloud
  drive to that same cloud is a loop with no benefit — back it up to a
  *different* target, or let the provider's own versioning cover it.
