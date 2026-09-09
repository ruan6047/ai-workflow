"""消費 core/enums.md stages、core/naming.md §4 專案層檔、core/verbs.md §3 來源標記。

被測物＝專案層的 `.wf/stages/<階段>.md` 骨架。三個測試一律在 tmp root 的合成樹上跑：
把交付檔當**資料**複製進合成樹再驗，⛔ 不斷言本 repo 缺任何東西、⛔ 不依賴 repo 歷史。
枚舉值在執行期讀合成樹的 `core/enums.md`，⛔ 不重打常數。
"""
from pathlib import Path
import shutil

from wf.compose.blocks import load_blocks
from wf.compose.frontmatter import parse_frontmatter
from wf.verbs.notes import _file_notes

RULES = Path(__file__).resolve().parents[2]
SOURCE = RULES / '.wf/stages'  # 交付檔的所在；測試只讀、⛔ 不寫


def make_root(tmp_path):
    """合成樹＝core/ 的符號連結（給枚舉）＋ 一個 .wf/stages/ 的交付檔複本。"""
    root = tmp_path / 'synth'
    (root / '.wf/stages').mkdir(parents=True)
    (root / 'core').symlink_to(RULES / 'core', target_is_directory=True)
    for path in sorted(SOURCE.glob('*.md')):
        shutil.copy(path, root / '.wf/stages' / path.name)
    return root


def stage_enum(root):
    """執行期讀合成樹的 core/enums.md 的 `json wf-enums` 區塊，⛔ 不重打常數。"""
    enums, = load_blocks(root).by_label('json wf-enums')
    return enums.data['stages']['enum']


def test_skeleton_covers_every_stage_enum_value(tmp_path):
    """A1：合成樹裡的 basename 集合與 stages 枚舉雙向相等（枚舉是封閉集合）。"""
    root = make_root(tmp_path)
    stages = stage_enum(root)
    assert len(stages) == len(set(stages))
    names = {path.stem for path in (root / '.wf/stages').glob('*.md')}
    assert names - set(stages) == set()
    assert set(stages) - names == set()


def test_skeleton_accepts_p_note_line(tmp_path):
    """A2：檔尾補一行條目後，`_file_notes` 每階段恰收 1 條，id／text／mark 逐字相符。

    mark 的逐字比對同時釘 A3 的後半（無 frontmatter ⇒ 只印 `[來源: <來源>/<檔>]`）。
    合成樹缺檔時 `is_file` 斷言先紅，⛔ 不讓 append 自己造出被測物。
    """
    root = make_root(tmp_path)
    stages = stage_enum(root)
    for stage in stages:
        relative = f'.wf/stages/{stage}.md'
        path = root / relative
        assert path.is_file(), relative
        note_id, text = f'P-{stage}-99', f'合成樹用的測試條目 {stage}。'
        with path.open('a', encoding='utf-8') as handle:
            handle.write(f'\n- {note_id}：{text}\n')
        items = _file_notes(root, relative, None, 'project')
        assert len(items) == 1, (stage, items)
        assert items[0].id == note_id
        assert items[0].text == text
        assert items[0].mark == f'[來源: project/{relative}]'


def test_skeleton_has_no_frontmatter_and_stays_empty(tmp_path):
    """A3 前半＋A4a：八檔首行⛔ 不是 `---`、無 frontmatter，且原檔各回 0 條。"""
    root = make_root(tmp_path)
    stages = stage_enum(root)
    for stage in stages:
        relative = f'.wf/stages/{stage}.md'
        path = root / relative
        assert path.is_file(), relative
        content = path.read_text(encoding='utf-8')
        assert content.splitlines()[0] != '---', relative
        assert parse_frontmatter(content, relative, diagnostics=[]).name == ''
        assert _file_notes(root, relative, None, 'project') == []
