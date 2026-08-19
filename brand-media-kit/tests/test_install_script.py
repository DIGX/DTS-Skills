import json
import pathlib
import shutil
import subprocess

import pytest

from bmk.config import load_assets, load_brand

SKILL = pathlib.Path(__file__).resolve().parents[1]
INSTALL = SKILL / "scripts" / "install"

pytestmark = pytest.mark.skipif(shutil.which("bash") is None, reason="bash not on PATH")


def run(*args):
    return subprocess.run(
        ["bash", str(INSTALL)] + list(args), capture_output=True, text=True
    )


def test_it_scaffolds_both_config_files(tmp_path):
    result = run(str(tmp_path))
    assert result.returncode == 0, result.stderr
    assert json.loads((tmp_path / ".brandkit" / "brand.json").read_text(encoding="utf-8"))
    assert json.loads((tmp_path / ".brandkit" / "assets.json").read_text(encoding="utf-8"))


def test_what_it_scaffolds_passes_the_validator(tmp_path):
    # A scaffolder that writes a config the loader rejects sends every new
    # adopter straight into a ConfigError on their first run.
    assert run(str(tmp_path)).returncode == 0
    load_brand(tmp_path / ".brandkit" / "brand.json")
    load_assets(tmp_path / ".brandkit" / "assets.json")


def test_dry_run_writes_nothing(tmp_path):
    result = run("--dry-run", str(tmp_path))
    assert result.returncode == 0, result.stderr
    assert not (tmp_path / ".brandkit").exists()


def test_it_refuses_to_clobber_an_existing_config(tmp_path):
    # An operator re-running install after months of tuning must not lose the
    # roster. Refusing is recoverable; overwriting is not.
    brandkit = tmp_path / ".brandkit"
    brandkit.mkdir()
    (brandkit / "brand.json").write_text('{"mine": true}', encoding="utf-8")

    result = run(str(tmp_path))
    assert result.returncode != 0
    assert "exists" in (result.stderr + result.stdout)
    assert json.loads((brandkit / "brand.json").read_text(encoding="utf-8")) == {"mine": True}


def test_force_overwrites(tmp_path):
    brandkit = tmp_path / ".brandkit"
    brandkit.mkdir()
    (brandkit / "brand.json").write_text('{"mine": true}', encoding="utf-8")

    result = run("--force", str(tmp_path))
    assert result.returncode == 0, result.stderr
    assert "mine" not in (brandkit / "brand.json").read_text(encoding="utf-8")
