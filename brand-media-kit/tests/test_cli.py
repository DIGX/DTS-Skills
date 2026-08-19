"""The five stages as an operator actually runs them.

SKILL.md routes on `python bmk/<stage>.py`. Every module below has a unit
test proving its function is correct; these prove the commands exist, wire to
each other, and leave the files the next stage expects to find. Without them a
module can be perfect and the documented pipeline still do nothing.
"""

import ast
import json
import pathlib
import subprocess
import sys

import pytest
from PIL import Image

SKILL = pathlib.Path(__file__).resolve().parents[1]

BRAND = {
    "name": "DTS",
    "palette": {"primary": "#2271b1", "primary_dark": "#135e96", "ink": "#0a1e3c", "paper": "#ffffff"},
    "fonts": {"display": "BebasNeue-Regular.ttf", "body": "BebasNeue-Regular.ttf", "mono": "BebasNeue-Regular.ttf"},
    "geometry": {"master": [1920, 1080], "margin": 96, "column": 517, "subject_band_pct": [28, 72]},
    "budget_bytes": 90000,
}

ASSETS = {
    "subjects": [
        {"slug": "invoicing", "title": "INVOICING", "tagline": "Compliant invoices", "art": "an invoice"},
        {"slug": "shipping", "title": "SHIPPING", "tagline": "Track every parcel", "art": "a parcel"},
    ],
    "targets": ["plugins/invoicing/images", "plugins/shipping/images"],
}


@pytest.fixture
def project(tmp_path, font_path):
    """A minimal adopting project: config, fonts, and nothing else yet."""
    brandkit = tmp_path / ".brandkit"
    (brandkit / "fonts").mkdir(parents=True)
    (brandkit / "brand.json").write_text(json.dumps(BRAND), encoding="utf-8")
    (brandkit / "assets.json").write_text(json.dumps(ASSETS), encoding="utf-8")
    (brandkit / "fonts" / "BebasNeue-Regular.ttf").write_bytes(font_path.read_bytes())
    return tmp_path


def stage(name, *args, project=None):
    cmd = [sys.executable, str(SKILL / "bmk" / "{}.py".format(name))]
    if project is not None:
        cmd += ["--project", str(project)]
    return subprocess.run(cmd + list(args), capture_output=True, text=True)


def put_art(project, size=(1920, 1080)):
    art = project / ".brandkit" / "art"
    art.mkdir(parents=True, exist_ok=True)
    for i, subject in enumerate(ASSETS["subjects"]):
        Image.new("RGB", size, (8, 12 + i * 30, 40)).save(art / "{}.png".format(subject["slug"]))
    return art


def test_verify_imports_no_bmk_module_at_import_time():
    # The fence must not share code with what it checks. Its CLI needs the
    # config and the format table, so those imports live inside main() - and
    # this test is what stops one drifting back up to module scope.
    tree = ast.parse((SKILL / "bmk" / "verify.py").read_text(encoding="utf-8"))
    for node in tree.body:
        names = []
        if isinstance(node, ast.Import):
            names = [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [node.module or ""]
        assert not any(n.split(".")[0] == "bmk" for n in names), names


def test_generate_handoff_writes_prompts_for_every_subject(project):
    result = stage("generate", "--handoff", project=project)
    assert result.returncode == 0, result.stderr
    prompts = (project / ".brandkit" / "art" / "PROMPTS.md").read_text(encoding="utf-8")
    for subject in ASSETS["subjects"]:
        assert subject["art"] in prompts


def test_generate_check_fails_while_art_is_missing(project):
    result = stage("generate", "--check", project=project)
    assert result.returncode != 0
    assert "invoicing" in result.stdout + result.stderr


def test_generate_check_passes_once_art_is_there(project):
    put_art(project)
    result = stage("generate", "--check", project=project)
    assert result.returncode == 0, result.stderr


def test_composite_writes_a_master_per_subject(project):
    put_art(project)
    result = stage("composite", project=project)
    assert result.returncode == 0, result.stderr
    for subject in ASSETS["subjects"]:
        master = project / ".brandkit" / "build" / subject["slug"] / "master.png"
        assert Image.open(master).size == (1920, 1080)


def test_composite_fails_when_art_is_missing(project):
    result = stage("composite", project=project)
    assert result.returncode != 0
    assert "invoicing" in result.stdout + result.stderr


def test_derive_writes_every_format_per_subject(project):
    put_art(project)
    assert stage("composite", project=project).returncode == 0
    result = stage("derive", project=project)
    assert result.returncode == 0, result.stderr

    from bmk.derive import FORMATS

    for subject in ASSETS["subjects"]:
        for key, size in FORMATS.items():
            path = project / ".brandkit" / "build" / subject["slug"] / "{}.png".format(key)
            assert Image.open(path).size == size


def test_deploy_puts_every_file_in_every_target(project):
    put_art(project)
    assert stage("composite", project=project).returncode == 0
    assert stage("derive", project=project).returncode == 0
    result = stage("deploy", project=project)
    assert result.returncode == 0, result.stderr

    from bmk.derive import FORMATS

    for target in ASSETS["targets"]:
        root = project / target
        for subject in ASSETS["subjects"]:
            for key in FORMATS:
                path = root / "{}-{}.webp".format(subject["slug"], key)
                assert path.is_file(), path
                assert path.stat().st_size <= BRAND["budget_bytes"]


def test_verify_passes_after_a_full_run(project):
    put_art(project)
    for name in ("composite", "derive", "deploy"):
        assert stage(name, project=project).returncode == 0, name
    result = stage("verify", project=project)
    assert result.returncode == 0, result.stdout + result.stderr


def test_verify_fails_when_a_deployed_file_is_removed(project):
    put_art(project)
    for name in ("composite", "derive", "deploy"):
        assert stage(name, project=project).returncode == 0, name
    (project / ASSETS["targets"][0] / "invoicing-card.webp").unlink()

    result = stage("verify", project=project)
    assert result.returncode != 0
    assert "invoicing-card.webp" in result.stdout + result.stderr


def test_verify_fails_before_anything_is_deployed(project):
    result = stage("verify", project=project)
    assert result.returncode != 0


def test_every_stage_reports_a_missing_project_instead_of_a_traceback(tmp_path):
    for name in ("generate", "composite", "derive", "deploy", "verify"):
        result = stage(name, project=tmp_path)
        assert result.returncode != 0, name
        assert "Traceback" not in result.stderr, (name, result.stderr)
        assert ".brandkit" in result.stdout + result.stderr, name
