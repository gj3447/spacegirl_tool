"""WE_FLYING_UP Phase 1 — recursive scan + diagnosis + erased catalog."""

from __future__ import annotations

from pathlib import Path

from spacegirl import cli, ssb, wall

PY = "def calculate_total(items):\n    return sum(items)\n"


def test_scan_file_clear(tmp_path: Path):
    f = tmp_path / "clean.py"
    f.write_text(PY)
    rep = wall.scan_file(f)
    assert rep.verdict == "CLEAR"
    assert rep.reversible is False
    assert rep.sidecar is None


def test_scan_file_locked_with_sidecar_catalog(tmp_path: Path):
    f = tmp_path / "m.py"
    f.write_text(PY)
    locked = tmp_path / "locked.py"
    r = ssb.lock(PY, key="k", salt="s")
    locked.write_text(r.text)
    sc = locked.with_suffix(locked.suffix + ".ssb.json")
    sc.write_text(
        __import__("json").dumps({"mapping": r.mapping, "meta": r.meta}, ensure_ascii=False)
    )

    rep = wall.scan_file(locked)
    assert rep.verdict in ("LOCKED", "AMBIGUOUS")
    assert rep.reversible is True
    assert rep.sidecar and rep.sidecar.endswith(".ssb.json")
    assert "calculate_total" in rep.erased_ids
    assert "sek1_sex" in rep.tiers or rep.taboo_hits >= 1


def test_scan_tree_maps_sexvoid(tmp_path: Path):
    sub = tmp_path / "pkg"
    sub.mkdir()
    clean = sub / "clean.py"
    clean.write_text(PY)
    locked = sub / "locked.py"
    r = ssb.lock(PY, key="k", salt="tree", banner=True)
    locked.write_text(r.text)
    sc = locked.with_suffix(locked.suffix + ".ssb.json")
    sc.write_text(
        __import__("json").dumps({"mapping": r.mapping, "meta": r.meta}, ensure_ascii=False)
    )
    # skip dir
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "x.js").write_text("const a = 1;\n")

    tree = wall.scan_tree(tmp_path)
    paths = {Path(f.path).name for f in tree.files}
    assert "clean.py" in paths
    assert "locked.py" in paths
    assert "x.js" not in paths  # node_modules pruned
    assert tree.locked >= 1
    assert tree.reversible >= 1
    cat = wall.catalog_erased(tree)
    assert any("calculate_total" in ids for ids in cat.values())


def test_cli_scan_dir_json(tmp_path: Path, capsys):
    f = tmp_path / "a.py"
    f.write_text(PY)
    locked = tmp_path / "b.py"
    r = ssb.lock(PY, key="k", salt="cli")
    locked.write_text(r.text)
    (locked.with_suffix(locked.suffix + ".ssb.json")).write_text(
        __import__("json").dumps({"mapping": r.mapping, "meta": r.meta})
    )
    rc = cli.main(["scan", str(tmp_path), "--json", "--catalog"])
    assert rc in (0, 2)
    out = capsys.readouterr().out
    assert "sexvoid" not in out  # json shape
    assert '"summary"' in out
    assert "erased_catalog" in out


def test_cli_scan_file_json_catalog(tmp_path: Path, capsys):
    f = tmp_path / "m.py"
    f.write_text(PY)
    locked = tmp_path / "locked.py"
    assert cli.main(["lock", str(f), "--key", "k", "-o", str(locked)]) == 0
    capsys.readouterr()  # drop lock stdout
    rc = cli.main(["scan", str(locked), "--json", "--catalog"])
    assert rc == 2  # LOCKED
    data = __import__("json").loads(capsys.readouterr().out)
    assert data["verdict"] == "LOCKED"
    assert data["reversible"] is True
    assert "calculate_total" in data["erased_ids"]
