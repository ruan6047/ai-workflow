"""CodeGraph 專用伴隨入口；由內容角色明確呼叫，不是模組載入器。"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys

from wfx.core.context import ConfigError, load_config

SUPPORTED_CODEGRAPH_VERSION = '1.6.2'


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description=f'CodeGraph {SUPPORTED_CODEGRAPH_VERSION} 專用 query/explore 入口。',
        epilog='共用指南：wfx/docs/CODEGRAPH.md；不可用時回原有 rg/read，僅停止本工具。',
        allow_abbrev=False,
    )
    parser.add_argument('--project-root', required=True, help='含 .wf/config.json 的根目錄')
    parser.add_argument('--path', required=True, help='具有自身 .codegraph/ 的工作樹根目錄')
    parser.add_argument('command', choices=('query', 'explore'))
    parser.add_argument('text', help='單一查詢文字；前導 dash 請用 query -- "-文字"')
    args = parser.parse_args(argv)

    try:
        project = Path(args.project_root).resolve(strict=True)
        root = Path(args.path).resolve(strict=True)
        if not project.is_dir() or not root.is_dir():
            raise ValueError('--project-root 與 --path 須為既存目錄')
        config = load_config(project)
        binary = Path(os.environ.get('WFX_CODEGRAPH_BIN', Path.home() / '.local/bin/codegraph'))
        if not binary.is_absolute():
            raise ValueError('WFX_CODEGRAPH_BIN 須為絕對可執行路徑')
    except (ConfigError, OSError, ValueError, RuntimeError) as exc:
        print(f'CodeGraph 用法／設定錯誤：{exc}', file=sys.stderr)
        return 2

    if 'codegraph' not in (config['modules'] or []):
        print('CodeGraph 未啟用：modules 須包含 codegraph；回原有 rg/read。', file=sys.stderr)
        return 1
    index = root / '.codegraph'
    if index.is_symlink() or not index.is_dir():
        print('CodeGraph 不可用：--path 須有自身 .codegraph/，不可為符號連結；回原有 rg/read。',
              file=sys.stderr)
        return 1
    if not binary.is_file() or not os.access(binary, os.X_OK):
        print(f'CodeGraph 不可用：找不到可執行檔 {binary}；回原有 rg/read。', file=sys.stderr)
        return 1

    env = dict(os.environ, DO_NOT_TRACK='1', CODEGRAPH_TELEMETRY='0',
               CODEGRAPH_NO_UPDATE_CHECK='1', CODEGRAPH_NO_DOWNLOAD='1',
               NODE_DISABLE_COMPILE_CACHE='1', CODEGRAPH_DIR='.codegraph')
    try:
        version = subprocess.run([str(binary), '--version'], cwd=root, env=env,
                                 shell=False, capture_output=True)
        if version.returncode != 0 or version.stdout.strip() != SUPPORTED_CODEGRAPH_VERSION.encode():
            print(f'CodeGraph 不可用：--version 須成功且精確為 {SUPPORTED_CODEGRAPH_VERSION}；'
                  '回原有 rg/read。', file=sys.stderr)
            return 1
        # 原生選項固定放在 -- 前，讓前導 dash 的文字也只成為位置參數。
        command = [str(binary), args.command, '--path', str(root)]
        if args.command == 'query':
            command.append('--json')
        command += ['--', args.text]
        return subprocess.run(command, cwd=root, env=env, shell=False).returncode
    except OSError as exc:
        print(f'CodeGraph 不可用：{exc}；回原有 rg/read。', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
