#!/usr/bin/env python3
"""固定 tag 的兩檔交付。只用標準庫；遠端不明即停，絕不自動恢復寫入。"""
from __future__ import annotations

import argparse
import configparser
from email.parser import BytesParser
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tarfile
import tempfile
import tomllib
from urllib.request import Request, urlopen
import zipfile


class ReleaseError(Exception):
    pass


def require(ok, message):
    if not ok:
        raise ReleaseError(message)


def command(args, cwd=None):
    result = subprocess.run(args, cwd=cwd, capture_output=True, check=False)
    if result.returncode:
        raise ReleaseError(f'{args[0:3]} rc={result.returncode}: {result.stderr.decode().strip()}')
    return result.stdout


def git(root, *args):
    return command(['git', *args], root).decode().strip()


def tag_version(ref):
    match = re.fullmatch(r'refs/tags/vnext-v((?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*))', ref)
    require(match, '不適用或不合法的版本 tag ref')
    return match[1]


def source(root, ref, event_sha, expected=None):
    tag_version(ref)
    require(re.fullmatch('[0-9a-f]{40}', event_sha) and set(event_sha) != {'0'}, '事件 SHA 無效')
    # 明確 refspec／完整歷史；不能用 checkout 時的舊 tag 或 main 代替遠端現值。
    shallow = git(root, 'rev-parse', '--is-shallow-repository') == 'true'
    args = ['fetch', '--no-tags'] + (['--unshallow'] if shallow else [])
    git(root, *args, 'origin', '+refs/heads/main:refs/release-check/main',
        f'+{ref}:refs/release-check/tag')
    sha = git(root, 'rev-parse', f'{event_sha}^{{commit}}')
    require(sha == git(root, 'rev-parse', 'HEAD^{commit}') ==
            git(root, 'rev-parse', 'refs/release-check/tag^{commit}'), 'HEAD／事件／遠端 tag 不一致')
    require(expected is None or expected == sha, 'tag 已移動')
    git(root, 'merge-base', '--is-ancestor', sha, 'refs/release-check/main')
    main = git(root, 'rev-parse', 'refs/release-check/main^{commit}')
    print(f'source={sha} main={main}')
    return sha


def clean_source(root, sha, target):
    data = command(['git', 'archive', sha], root)
    with tarfile.open(fileobj=io.BytesIO(data)) as archive:
        archive.extractall(target, filter='data')


def check_readme(text, version):
    display = re.findall(r'版本 `([^`]+)`（唯一居所＝`vnext/cli/pyproject.toml`）', text)
    urls = re.findall(r'https://github.com/ruan6047/ai-workflow/releases/download/(vnext-v[^/\s]+)/([^\s]+\.whl)', text)
    require(display == [version], 'README 顯示版本缺席／歧義／錯配')
    require(urls == [(f'vnext-v{version}', wheel_name(version))], 'README tag／wheel URL 缺席／歧義／錯配')


def wheel_name(version):
    return f'ai_workflow_vnext-{version}-py3-none-any.whl'


def declaration(root, version):
    project = tomllib.loads((root / 'vnext/cli/pyproject.toml').read_text())['project']
    require(project['version'] == version, 'tag 與 pyproject 版本錯配')
    check_readme((root / 'README.md').read_text(), version)
    return project


def digest(data):
    return hashlib.sha256(data).hexdigest()


def verify_wheel(root, directory, version, expected_hash=None, with_hash=True):
    project = declaration(root, version)
    name = wheel_name(version)
    expected_files = {name, name + '.sha256'} if with_hash else {name}
    require({p.name for p in directory.iterdir()} == expected_files, '交付目錄不是精確檔案集合')
    wheel = directory / name
    sha = digest(wheel.read_bytes())
    require(expected_hash is None or sha == expected_hash, 'wheel hash 不符 build output')
    checksum = f'{sha}  {name}\n'.encode()
    if with_hash:
        require((directory / (name + '.sha256')).read_bytes() == checksum, 'sha256 檔錯配')
    package = root / 'vnext/cli/src'
    expected = {str(p.relative_to(package)): p.read_bytes()
                for pattern in ['wfx/**/*.py', 'wfx/rules/**/*.md', 'wfx/docs/*.md']
                for p in package.glob(pattern) if p.is_file()}
    with zipfile.ZipFile(wheel) as z:
        names = z.namelist()
        require(len(names) == len(set(names)), 'wheel 重複 ZIP member')
        info = f'ai_workflow_vnext-{version}.dist-info/'
        require({n.split('/')[0] for n in names} == {'wfx', info[:-1]}, '非預期套件／dist-info')
        actual = {n: z.read(n) for n in names if n.startswith('wfx/')}
        require(actual == expected, 'wheel 程式／規則／文件集合或 bytes 不符來源')
        metadata = BytesParser().parsebytes(z.read(info + 'METADATA'))
        for key, value in [('Name', project['name']), ('Version', version),
                           ('Requires-Python', project['requires-python'])]:
            require(metadata.get_all(key) == [value], f'METADATA {key} 錯配')
        # setuptools 為 optional dev extra 產生 Requires-Dist；逐項對照宣告。
        dependencies = list(project.get('dependencies', []))
        for extra, values in project.get('optional-dependencies', {}).items():
            dependencies.extend(f'{value}; extra == "{extra}"' for value in values)
        require(sorted(metadata.get_all('Requires-Dist', [])) == sorted(dependencies), 'Requires-Dist 錯配')
        entry = configparser.ConfigParser()
        entry.read_string(z.read(info + 'entry_points.txt').decode())
        require(entry.sections() == ['console_scripts'] and
                dict(entry['console_scripts']) == {'wfx': 'wfx.verbs.main:main'}, 'entry point 錯配')
    return sha, checksum


def output(values):
    if path := os.environ.get('GITHUB_OUTPUT'):
        with open(path, 'a') as stream:
            for key, value in values.items():
                stream.write(f'{key}={value}\n')


def build(root, directory, ref, event_sha):
    version = tag_version(ref)
    sha = source(root, ref, event_sha)
    declaration(root, version)
    require(not directory.exists(), 'build 目錄必須全新')
    directory.mkdir(parents=True)
    with tempfile.TemporaryDirectory() as tmp:
        clean = Path(tmp)
        clean_source(root, sha, clean)
        declaration(clean, version)
        print(command([sys.executable, '-m', 'pip', '--version']).decode())
        print(command([sys.executable, '-m', 'pip', 'wheel', '--no-deps', '--wheel-dir',
                       str(directory), str(clean / 'vnext/cli')]).decode())
        with zipfile.ZipFile(directory / wheel_name(version)) as z:
            wheel_metadata = next(n for n in z.namelist() if n.endswith('.dist-info/WHEEL'))
            print(z.read(wheel_metadata).decode())  # Generator 記錄實際 setuptools 版本。
        sha256, checksum = verify_wheel(clean, directory, version, with_hash=False)
        (directory / (wheel_name(version) + '.sha256')).write_bytes(checksum)
        verify_wheel(clean, directory, version, sha256)
    output({'source': sha, 'version': version, 'hash': sha256})


class GitHub:
    def __init__(self, repo):
        require(re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repo), 'repository 格式無效')
        self.repo = repo

    def api(self, endpoint, payload=None):
        args = ['gh', 'api', f'repos/{self.repo}/{endpoint}']
        if payload is not None:
            # stdin 是明確 JSON；不依賴 gh -f 的布林字串轉換。
            result = subprocess.run(args + ['--method', 'PATCH', '--input', '-'],
                                    input=json.dumps(payload).encode(), capture_output=True)
            if result.returncode:
                raise ReleaseError(f'PATCH {endpoint} rc={result.returncode}: {result.stderr.decode()}')
            return json.loads(result.stdout)
        return json.loads(command(args))

    def absent(self, tag):
        # 認證分頁列表含 draft；只允許成功讀完全部頁才判不存在。
        page = 1
        while True:
            releases = self.api(f'releases?per_page=100&page={page}')
            require(isinstance(releases, list), 'Release 列表格式無效')
            require(not any(x['tag_name'] == tag for x in releases), '同 tag 已有 Release；交人核對')
            if len(releases) < 100:
                return
            page += 1

    def create(self, tag, version, sha, run_url):
        command(['gh', 'release', 'create', tag, '--repo', self.repo, '--verify-tag',
                 '--draft', '--prerelease', '--latest=false', '--title', f'vNext {version}',
                 '--notes', f'Source: {sha}\nRun: {run_url}'])
        # tag REST 端點只回 published；gh view 支援草稿查找，取得 REST 數字 ID。
        release_id = json.loads(command(['gh', 'release', 'view', tag, '--repo', self.repo,
                                         '--json', 'databaseId']))['databaseId']
        return self.api(f'releases/{release_id}')

    def upload(self, tag, files):
        command(['gh', 'release', 'upload', tag, '--repo', self.repo, *map(str, files)])

    def download(self, asset, authenticated):
        if authenticated:
            return command(['gh', 'api', f'repos/{self.repo}/releases/assets/{asset["id"]}',
                            '-H', 'Accept: application/octet-stream'])
        # 不讀 GH_TOKEN／Authorization；固定 github.com URL，redirect 也不附認證。
        request = Request(asset['url'], headers={'User-Agent': 'wfx-release-verifier'})
        with urlopen(request, timeout=60) as response:
            return response.read()


def check_release(release, release_id, tag, version, files, draft):
    require(release['id'] == release_id and release['tag_name'] == tag and
            release['name'] == f'vNext {version}' and release['draft'] is draft and
            release['prerelease'] is True, 'Release ID／tag／title／flags 錯配')
    assets = release['assets']
    require(len(assets) == 2 and {a['name'] for a in assets} == set(files), 'Release 非精確兩資產')
    for asset in assets:
        require(asset['state'] == 'uploaded' and asset['size'] == len(files[asset['name']]), '資產 state／size 錯配')
    return assets


def summary(message):
    print(message)
    if path := os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(path, 'a') as stream:
            stream.write(message + '\n')


def publish(root, directory, ref, event_sha, expected, expected_hash, api, run_url):
    release_id = None
    step = '驗證來源／artifact'
    try:
        version = tag_version(ref)
        tag = ref.removeprefix('refs/tags/')
        sha = source(root, ref, event_sha, expected)
        with tempfile.TemporaryDirectory() as tmp:
            clean = Path(tmp)
            clean_source(root, sha, clean)
            verify_wheel(clean, directory, version, expected_hash)
        files = {p.name: p.read_bytes() for p in directory.iterdir()}
        step = '同 tag 查詢'
        api.absent(tag)
        source(root, ref, event_sha, expected)
        step = '建立草稿（回應不明時亦可能已建立）'
        created = api.create(tag, version, sha, run_url)
        release_id = created['id']
        require(created['tag_name'] == tag and created['draft'] is True and
                created['prerelease'] is True and created['name'] == f'vNext {version}' and
                created['assets'] == [], '新草稿屬性錯配')
        step = '上傳／核對草稿'
        api.upload(tag, [directory / wheel_name(version), directory / (wheel_name(version) + '.sha256')])
        endpoint = f'releases/{release_id}'
        for asset in check_release(api.api(endpoint), release_id, tag, version, files, True):
            require(api.download(asset, True) == files[asset['name']], '草稿資產 bytes 錯配')
        source(root, ref, event_sha, expected)
        step = '公開（可能已公開）'
        api.api(endpoint, {'draft': False, 'prerelease': True, 'make_latest': 'false'})
        step = '公開回讀／匿名下載（遠端已公開）'
        for asset in check_release(api.api(endpoint), release_id, tag, version, files, False):
            url = f'https://github.com/{api.repo}/releases/download/{tag}/{asset["name"]}'
            require(api.download({'url': url}, False) == files[asset['name']], '匿名下載 bytes 錯配')
        source(root, ref, event_sha, expected)
        summary(f'發布完成：https://github.com/{api.repo}/releases/tag/{tag}\n'
                f'Run: {run_url}\nSource: {sha}\nVersion: {version}\n'
                f'Assets: {", ".join(sorted(files))}\nSHA256: {expected_hash}')
    except Exception as error:
        summary(f'失敗／遠端可能已部分成功；Release ID={release_id}；步驟={step}；{error}')
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['build', 'publish'])
    parser.add_argument('--directory', type=Path, required=True)
    args = parser.parse_args()
    root = Path.cwd()
    try:
        print(sys.version)
        if args.mode == 'build':
            build(root, args.directory.resolve(), os.environ['RELEASE_REF'], os.environ['RELEASE_SHA'])
        else:
            print(command(['gh', '--version']).decode())
            repo = os.environ['GITHUB_REPOSITORY']
            run_url = f'https://github.com/{repo}/actions/runs/{os.environ["GITHUB_RUN_ID"]}'
            publish(root, args.directory.resolve(), os.environ['RELEASE_REF'], os.environ['RELEASE_SHA'],
                    os.environ['EXPECTED_SOURCE'], os.environ['EXPECTED_HASH'], GitHub(repo), run_url)
        return 0
    except Exception as error:
        summary(f'失敗：{args.mode}；遠端可能已部分成功（publish）；{error}')
        return 1


if __name__ == '__main__':
    sys.exit(main())
