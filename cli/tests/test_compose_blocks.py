"""驗證 core/card-schema.md §1、state-machine.md §3、naming.md §5 與 handoff.md 每段首行。"""
import json
from pathlib import Path
import subprocess

import pytest

from wf.compose.blocks import (
    BadJSONError, DuplicateIDError, MissingBlockError, UnknownLabelError,
    load_blocks, read_blocks, require_blocks, source_line,
)
from wf.compose.frontmatter import MissingFrontmatterError, read_frontmatter

ROOT = Path(__file__).resolve().parents[2]
HEADER = "---\nname: sample\nwhen: 讀取：測試\nnon_scope: 無\nlast_confirmed: 2000-01-01\n---\n"


def rule(tmp_path, body, relative="core/example.md", header=HEADER):
    path = tmp_path / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(header + body, encoding="utf-8", newline="")
    return path


def test_repo_inventory():
    catalog = load_blocks(ROOT)
    paths = sorted(ROOT.glob("core/*.md")) + sorted(ROOT.glob("modules/*/module.md"))
    total = 0
    for path in paths:
        result = subprocess.run(["grep", "-c", "^```", str(path)], capture_output=True, text=True)
        assert result.returncode in (0, 1), result.stderr
        count = int(result.stdout)
        assert count % 2 == 0
        total += count
        print(f"FENCES {path.relative_to(ROOT)} {count}")
    for block in catalog.blocks:
        identifier = block.data.get("$id") if isinstance(block.data, dict) else None
        print(f"BLOCK {block.source.path} | {block.label} | {identifier or '無'}")
    schemas = [b for b in catalog.blocks if b.label == "json schema"]
    ids = [b.data["$id"] for b in schemas]
    assert len(ids) == len(set(ids)) == len(catalog.schemas)
    assert set(catalog.schemas) == set(ids)
    assert all(catalog.schemas[b.data["$id"]] is b for b in schemas)
    assert len(catalog.blocks) == total // 2
    print(f"TOTAL files={len(paths)} blocks={len(catalog.blocks)} fences={total}")
    print("SCHEMA_IDS " + json.dumps(sorted(ids), ensure_ascii=False))


@pytest.mark.parametrize("label", ["json schema", "json wf-enums", "json wf-state-machine", "json wf-module-sections", "yaml wf-module"])
def test_supported_labels_and_raw_file_slice(tmp_path, label):
    body = ' \r\n{ "$id": "test", "unicode": "逐字", "$ref": "wf-enums#/stages" }\r\n\r\n'
    path = rule(tmp_path, "## 實際節\r\n```" + label + "\r\n" + body + "```\r\n")
    block, = read_blocks(tmp_path, "core/example.md")
    text = path.read_bytes().decode("utf-8")
    start = text.index("\n", text.index("```")) + 1
    end = text.index("```", start)
    assert block.raw == text[start:end] == body
    assert block.data == json.loads(body)
    assert block.data["$ref"] == "wf-enums#/stages"


@pytest.mark.parametrize("relative,label", [
    ("core/card-schema.md", "json schema"),
    ("core/state-machine.md", "json wf-state-machine"),
    ("modules/research/module.md", "yaml wf-module"),
])
def test_repo_source_location(relative, label):
    path = ROOT / relative
    text = path.read_text(encoding="utf-8")
    block = require_blocks(ROOT, relative, label)[0]
    prefix = text[:text.index("```" + label)]
    section = [line[3:] for line in prefix.splitlines() if line.startswith("## ")][-1]
    header = dict(line.split(": ", 1) for line in text.split("---", 2)[1].strip().splitlines())
    assert block.source.path == relative
    assert block.source.section == section
    assert block.source.name == header["name"]
    assert block.source.when == header["when"]
    assert block.source.last_confirmed == header["last_confirmed"]
    start = text.index("\n", text.index("```" + label)) + 1
    assert block.raw == text[start:text.index("```", start)]
    print(f"SOURCE {relative} #{section} | {header['name']} | {header['last_confirmed']}")


def test_missing_block_negative_control(tmp_path):
    rule(tmp_path, "## 查找節\n散文，不是區塊\n")
    with pytest.raises(MissingBlockError) as caught:
        require_blocks(tmp_path, "core/example.md", "json schema", section="查找節")
    assert "core/example.md#查找節" in str(caught.value)
    print(type(caught.value).__name__, str(caught.value))


def test_bad_json_negative_control(tmp_path):
    rule(tmp_path, "## 壞資料\n```json schema\n{broken}\n```\n")
    with pytest.raises(BadJSONError) as caught:
        load_blocks(tmp_path)
    assert "core/example.md#壞資料" in str(caught.value)
    assert isinstance(caught.value.__cause__, json.JSONDecodeError)
    print(type(caught.value).__name__, str(caught.value))


def test_duplicate_id_negative_control(tmp_path):
    rule(tmp_path, '## 原件\n```json schema\n{"$id": "same"}\n```\n')
    rule(tmp_path, '## 重複\n```json schema\n{"$id": "same"}\n```\n', "core/second.md")
    with pytest.raises(DuplicateIDError) as caught:
        load_blocks(tmp_path)
    assert "core/example.md#原件" in str(caught.value)
    assert "core/second.md#重複" in str(caught.value)
    print(type(caught.value).__name__, str(caught.value))


def test_unknown_label_negative_control(tmp_path):
    rule(tmp_path, "## 未知\n```json wf-unknown\n{}\n```\n")
    with pytest.raises(UnknownLabelError) as caught:
        load_blocks(tmp_path)
    assert "core/example.md#未知" in str(caught.value)
    print(type(caught.value).__name__, str(caught.value))


@pytest.mark.parametrize("missing", ["name", "when", "non_scope", "last_confirmed"])
def test_missing_frontmatter_reports_exact_field(tmp_path, missing):
    header = "\n".join(line for line in HEADER.split("\n") if not line.startswith(missing + ":"))
    path = rule(tmp_path, "", header=header)
    with pytest.raises(MissingFrontmatterError) as caught:
        read_frontmatter(path)
    assert caught.value.missing == (missing,)
    assert str(path) in str(caught.value)


def test_frontmatter_does_not_read_body_or_guess(tmp_path):
    path = rule(tmp_path, HEADER, header="無檔頭\n")
    with pytest.raises(MissingFrontmatterError) as caught:
        read_frontmatter(path)
    assert caught.value.missing == ("name", "when", "non_scope", "last_confirmed")


def test_source_line_preserves_old_date_and_empty_section(tmp_path):
    rule(tmp_path, '```json schema\n{"$id":"test"}\n```\n')
    block, = read_blocks(tmp_path, "core/example.md")
    assert block.source.section == ""
    assert source_line(block.source) == "[來源: core/example.md# · sample：讀取：測試 · confirmed 2000-01-01]"


def test_empty_file_optional_scan_and_unclosed_fence(tmp_path):
    rule(tmp_path, "## 無區塊\n")
    assert read_blocks(tmp_path, "core/example.md") == []
    rule(tmp_path, "## 未閉合\n```json schema\n{}\n")
    with pytest.raises(MissingBlockError, match="core/example.md#未閉合"):
        read_blocks(tmp_path, "core/example.md")


def test_runtime_reload_and_scope(tmp_path):
    rule(tmp_path, '```json schema\n{"$id":"original"}\n```\n')
    rule(tmp_path, '```json unknown\ninvalid\n```\n', "roles/ignored.md")
    assert set(load_blocks(tmp_path).schemas) == {"original"}
    rule(tmp_path, '```json schema\n{"$id":"changed"}\n```\n')
    assert set(load_blocks(tmp_path).schemas) == {"changed"}


def test_section_filter_and_json_scalar(tmp_path):
    rule(tmp_path, '## 甲\n```json schema\n"raw text"\n```\n## 乙\n```json schema\n{}\n```\n')
    selected = require_blocks(tmp_path, "core/example.md", "json schema", section="乙")
    assert len(selected) == 1 and selected[0].source.section == "乙"
    assert read_blocks(tmp_path, "core/example.md")[0].data == "raw text"


def test_import_inventory_negative_control(tmp_path):
    sample = tmp_path / "imports.py"
    sample.write_text("import subprocess\nfrom urllib import request\nimport socket\nimport requests\n")
    result = subprocess.run(["grep", "-rn", "^import\\|^from", str(sample)], capture_output=True, text=True)
    assert result.returncode == 0
    assert [line.removeprefix(str(sample) + ":") for line in result.stdout.splitlines()] == [
        "1:import subprocess", "2:from urllib import request", "3:import socket", "4:import requests",
    ]
    print("IMPORT_NEGATIVE_CONTROL\n" + result.stdout, end="")
