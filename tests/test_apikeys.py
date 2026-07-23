"""API keys: root-only management, key login, and per-key permission enforcement."""
import pytest
from fastapi.testclient import TestClient

import app as filepeek


def make_key(auth_client, **perms):
    """Log in as root, create a key with the given permissions, log out again.
    Returns the created key record."""
    auth_client.post("/login", data={"password": "secret123"})
    r = auth_client.post("/api/keys", json={"label": "test", "permissions": perms})
    assert r.status_code == 200, r.text
    auth_client.post("/logout")
    return r.json()


def key_login(auth_client, key):
    r = auth_client.post("/login", data={"apikey": key}, follow_redirects=False)
    assert r.status_code == 303
    return r


# --- key format & management ------------------------------------------------

def test_generated_key_is_10_char_alnum(auth_client):
    rec = make_key(auth_client, view=True)
    assert len(rec["key"]) == 10 and rec["key"].isalnum()


def test_key_management_requires_root(auth_client):
    rec = make_key(auth_client, view=True)
    key_login(auth_client, rec["key"])
    assert auth_client.get("/api/keys").status_code == 403
    assert auth_client.post("/api/keys", json={}).status_code == 403
    assert auth_client.delete(f"/api/keys?id={rec['id']}").status_code == 403
    assert auth_client.put("/api/keys", json={"id": rec["id"]}).status_code == 403


def test_key_list_update_delete(auth_client):
    auth_client.post("/login", data={"password": "secret123"})
    rec = auth_client.post("/api/keys", json={"label": "one", "permissions": {"view": True}}).json()
    keys = auth_client.get("/api/keys").json()["keys"]
    assert [k["id"] for k in keys] == [rec["id"]]

    upd = auth_client.put("/api/keys", json={
        "id": rec["id"], "label": "renamed",
        "permissions": {"view": True, "read": True},
    })
    assert upd.status_code == 200
    assert upd.json()["label"] == "renamed"
    assert upd.json()["permissions"]["read"] is True

    assert auth_client.delete(f"/api/keys?id={rec['id']}").status_code == 200
    assert auth_client.get("/api/keys").json()["keys"] == []
    assert auth_client.delete(f"/api/keys?id={rec['id']}").status_code == 404


def test_backup_is_root_only_for_key_users(auth_client):
    rec = make_key(auth_client, view=True, read=True, write=True,
                   delete_folders=True, delete_files=True)
    key_login(auth_client, rec["key"])
    assert auth_client.get("/api/backup/config").status_code == 403
    assert auth_client.post("/api/backup/run", json={}).status_code == 403


# --- login ------------------------------------------------------------------

def test_key_login_and_me(auth_client):
    rec = make_key(auth_client, view=True, read=True)
    key_login(auth_client, rec["key"])
    me = auth_client.get("/api/me").json()
    assert me["role"] == "key"
    assert me["permissions"]["read"] is True
    assert me["permissions"]["write"] is False


def test_root_login_me(auth_client):
    auth_client.post("/login", data={"password": "secret123"})
    me = auth_client.get("/api/me").json()
    assert me["role"] == "root"
    assert all(me["permissions"].values())


def test_wrong_key_rejected_and_counts_toward_lockout(auth_client):
    r = auth_client.post("/login", data={"apikey": "AAAAAAAAAA"})
    assert r.status_code == 401
    assert "Unknown API key" in r.text


def test_key_as_bearer_token(auth_client):
    rec = make_key(auth_client, view=True)
    hdr = {"Authorization": f"Bearer {rec['key']}"}
    assert auth_client.get("/api/tree", headers=hdr).status_code == 200
    assert auth_client.get("/api/file?path=readme.md", headers=hdr).status_code == 403


def test_deleted_key_session_stops_working(auth_client):
    rec = make_key(auth_client, view=True)
    key_login(auth_client, rec["key"])
    assert auth_client.get("/api/tree").status_code == 200
    session = auth_client.cookies.get(filepeek.SESSION_COOKIE)
    auth_client.cookies.clear()
    auth_client.post("/login", data={"password": "secret123"})
    auth_client.delete(f"/api/keys?id={rec['id']}")
    auth_client.cookies.clear()
    auth_client.cookies.set(filepeek.SESSION_COOKIE, session)
    assert auth_client.get("/api/tree").status_code == 401


# --- permission enforcement -------------------------------------------------

def test_view_only_key(auth_client):
    rec = make_key(auth_client, view=True)
    key_login(auth_client, rec["key"])
    assert auth_client.get("/api/tree").status_code == 200
    assert auth_client.get("/api/search/filename?q=notes").status_code == 200
    assert auth_client.get("/api/file?path=readme.md").status_code == 403
    assert auth_client.get("/api/download?path=readme.md").status_code == 403
    assert auth_client.get("/api/search/content?q=needle").status_code == 403
    assert auth_client.post("/api/create", json={"path": "sub dir/x.txt"}).status_code == 403
    assert auth_client.delete("/api/delete?path=notes.txt").status_code == 403


def test_no_view_key_cannot_browse(auth_client):
    rec = make_key(auth_client, view=False, read=True)
    key_login(auth_client, rec["key"])
    assert auth_client.get("/api/tree").status_code == 403
    assert auth_client.get("/api/file?path=readme.md").status_code == 200


def test_read_key_can_open_and_download(auth_client):
    rec = make_key(auth_client, view=True, read=True)
    key_login(auth_client, rec["key"])
    assert auth_client.get("/api/file?path=readme.md").status_code == 200
    assert auth_client.get("/api/download?path=readme.md").status_code == 200
    assert auth_client.get("/api/raw?path=readme.md").status_code == 200
    assert auth_client.put("/api/file", json={"path": "readme.md", "content": "x"}).status_code == 403


def test_write_key(auth_client, root):
    rec = make_key(auth_client, view=True, read=True, write=True)
    key_login(auth_client, rec["key"])
    # files anywhere, folders below root: allowed
    assert auth_client.post("/api/create", json={"path": "rootfile.txt"}).status_code == 200
    assert auth_client.post("/api/create",
                            json={"path": "sub dir/newdir", "is_dir": True}).status_code == 200
    assert auth_client.put("/api/file",
                           json={"path": "sub dir/saved.txt", "content": "hi"}).status_code == 200
    # but no deletes
    assert auth_client.delete("/api/delete?path=rootfile.txt").status_code == 403


def test_write_key_cannot_create_root_level_folder(auth_client, root):
    rec = make_key(auth_client, view=True, read=True, write=True)
    key_login(auth_client, rec["key"])
    r = auth_client.post("/api/create", json={"path": "toplevel", "is_dir": True})
    assert r.status_code == 403
    assert "root level" in r.json()["detail"]
    # implicit creation via a nested path is blocked too
    assert auth_client.post("/api/create", json={"path": "newtop/file.txt"}).status_code == 403
    assert auth_client.put("/api/file",
                           json={"path": "newtop/file.txt", "content": "x"}).status_code == 403
    # copying/moving a folder to the root is also a root-level folder creation
    assert auth_client.post("/api/copy",
                            json={"path": "sub dir/deep", "dest_dir": ""}).status_code == 403
    assert auth_client.post("/api/move",
                            json={"path": "sub dir/deep", "dest_dir": ""}).status_code == 403
    # copying a folder deeper down is fine
    assert auth_client.post("/api/copy",
                            json={"path": "sub dir/deep", "dest_dir": "sub dir/newhome"}).status_code == 404
    (root / "sub dir/newhome").mkdir()
    assert auth_client.post("/api/copy",
                            json={"path": "sub dir/deep", "dest_dir": "sub dir/newhome"}).status_code == 200
    # root user is never blocked
    auth_client.post("/logout")
    auth_client.post("/login", data={"password": "secret123"})
    assert auth_client.post("/api/create", json={"path": "toplevel", "is_dir": True}).status_code == 200


def test_delete_files_vs_delete_folders(auth_client, root):
    rec = make_key(auth_client, view=True, read=True, write=True, delete_files=True)
    key_login(auth_client, rec["key"])
    assert auth_client.delete("/api/delete?path=notes.txt").status_code == 200
    r = auth_client.delete("/api/delete?path=sub dir/deep")
    assert r.status_code == 403 and "delete_folders" in r.json()["detail"]

    rec2 = make_key(auth_client, view=True, delete_folders=True)
    key_login(auth_client, rec2["key"])
    assert auth_client.delete("/api/delete?path=sub dir/deep").status_code == 200
    assert auth_client.delete("/api/delete?path=readme.md").status_code == 403


def test_upload_permission(auth_client):
    rec = make_key(auth_client, view=True)
    key_login(auth_client, rec["key"])
    r = auth_client.post("/api/upload", files={"file": ("up.txt", b"data")},
                         data={"target_dir": ""})
    assert r.status_code == 403

    rec2 = make_key(auth_client, view=True, write=True)
    key_login(auth_client, rec2["key"])
    r = auth_client.post("/api/upload", files={"file": ("up.txt", b"data")},
                         data={"target_dir": ""})
    assert r.status_code == 200


def test_keys_file_not_servable(auth_client, root, tmp_path):
    """The apikeys state file must never be reachable through the file API."""
    auth_client.post("/login", data={"password": "secret123"})
    assert auth_client.get("/api/file?path=../state/apikeys.json").status_code in (403, 404)
