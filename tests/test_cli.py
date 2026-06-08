"""CLI end-to-end — audit HIGH: cli.py 0% coverage 였고 FPE 침묵손상 버그가 여기로 새어나갔다 (2026-06-08)."""

from __future__ import annotations

import pytest

pytest.importorskip("cryptography")

from spacegirl import cli  # noqa: E402

PY = "def calculate_total(items):\n    return sum(items)\n"


def test_cli_obscene_roundtrip(tmp_path):
    f = tmp_path / "m.py"
    f.write_text(PY)
    locked = tmp_path / "locked.py"
    assert cli.main(["lock", str(f), "--key", "k", "-o", str(locked)]) == 0
    assert "calculate_total" not in locked.read_text()
    restored = tmp_path / "out.py"
    assert cli.main(["unlock", str(locked), "-o", str(restored)]) == 0
    assert restored.read_text() == PY


def test_cli_fpe_roundtrip_with_sidecar(tmp_path):
    f = tmp_path / "m.py"
    f.write_text(PY)
    locked = tmp_path / "locked.py"
    assert cli.main(["lock", str(f), "--key", "K", "--mode", "fpe", "-o", str(locked)]) == 0
    assert "calculate_total" not in locked.read_text()
    restored = tmp_path / "out.py"
    assert cli.main(["unlock", str(locked), "--mode", "fpe", "--key", "K", "-o", str(restored)]) == 0
    assert restored.read_text() == PY


def test_cli_fpe_sidecar_free_requires_salt(tmp_path):
    """사이드카 삭제 후 salt 없는 fpe 복원 = 깔끔한 에러(rc=1, 쓰레기 출력 아님); salt 주면 복원."""
    f = tmp_path / "m.py"
    f.write_text(PY)
    locked = tmp_path / "locked.py"
    cli.main(["lock", str(f), "--key", "K", "--salt", "S", "--mode", "fpe", "-o", str(locked)])
    (tmp_path / "locked.py.ssb.json").unlink()  # 사이드카(=salt) 제거
    out = tmp_path / "out.py"
    assert cli.main(["unlock", str(locked), "--mode", "fpe", "--key", "K", "-o", str(out)]) == 1
    assert cli.main(
        ["unlock", str(locked), "--mode", "fpe", "--key", "K", "--salt", "S", "-o", str(out)]
    ) == 0
    assert out.read_text() == PY


def test_cli_lock_missing_file_clean_error(tmp_path):
    assert cli.main(["lock", str(tmp_path / "nope.py"), "--key", "k"]) == 1


def test_cli_fpe_lock_without_key_clean_error(tmp_path):
    f = tmp_path / "m.py"
    f.write_text(PY)
    assert cli.main(["lock", str(f), "--mode", "fpe"]) == 1


def test_cli_encrypted_sidecar_roundtrip(tmp_path):
    f = tmp_path / "m.py"
    f.write_text(PY)
    locked = tmp_path / "locked.py"
    assert cli.main(
        ["lock", str(f), "--key", "k", "--encrypt-sidecar", "pw", "-o", str(locked)]
    ) == 0
    assert (tmp_path / "locked.py.ssb.json.enc").exists()
    restored = tmp_path / "out.py"
    assert cli.main(["unlock", str(locked), "--sidecar-pass", "pw", "-o", str(restored)]) == 0
    assert restored.read_text() == PY


def test_cli_scan_and_optout(tmp_path, capsys):
    f = tmp_path / "m.py"
    f.write_text(PY)
    assert cli.main(["scan", str(f)]) == 0  # clean python -> CLEAR
    assert cli.main(["optout", "robots"]) == 0
