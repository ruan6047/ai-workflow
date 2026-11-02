"""離線發布契約；所有遠端寫入使用替身。"""
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('release', Path(__file__).with_name('release.py'))
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)


class Versions(unittest.TestCase):
    def test_tag_format(self):
        self.assertEqual(r.tag_version('refs/tags/vnext-v1.2.3'), '1.2.3')
        for ref in ['refs/heads/main', 'refs/tags/vnext-v01.2.3', 'refs/tags/vnext-v1.2.3rc1']:
            with self.subTest(ref=ref), self.assertRaises(r.ReleaseError):
                r.tag_version(ref)

    def test_readme_three_references(self):
        import tomllib
        root = Path(__file__).resolve().parents[2]
        version = tomllib.loads((root / 'vnext/cli/pyproject.toml').read_text())['project']['version']
        wrong = '999.0.0' if version != '999.0.0' else '998.0.0'
        text = (root / 'README.md').read_text()
        r.check_readme(text, version)
        for old in [f'版本 `{version}`', f'/vnext-v{version}/', f'vnext-{version}-py3']:
            with self.subTest(old=old), self.assertRaises(r.ReleaseError):
                r.check_readme(text.replace(old, old.replace(version, wrong)), version)
        with self.assertRaises(r.ReleaseError):
            r.check_readme(text, wrong)


class Source(unittest.TestCase):
    def test_fixed_annotated_tag_main_ancestry_move_and_missing(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            r.git(root, 'init', '-q', '-b', 'main')
            r.git(root, 'config', 'user.email', 'fixture@example.invalid')
            r.git(root, 'config', 'user.name', 'fixture')
            r.git(root, 'commit', '-q', '--allow-empty', '-m', 'base')
            sha = r.git(root, 'rev-parse', 'HEAD')
            r.git(root, 'tag', '-a', 'vnext-v1.2.3', '-m', 'annotated')
            tag_sha = r.git(root, 'rev-parse', 'refs/tags/vnext-v1.2.3')
            r.git(root, 'remote', 'add', 'origin', str(root))
            self.assertEqual(r.source(root, 'refs/tags/vnext-v1.2.3', tag_sha), sha)
            r.git(root, 'commit', '-q', '--allow-empty', '-m', 'forward')
            newer = r.git(root, 'rev-parse', 'HEAD')
            r.git(root, 'checkout', '-q', '--detach', sha)
            self.assertEqual(r.source(root, 'refs/tags/vnext-v1.2.3', sha), sha)
            r.git(root, 'tag', '-f', 'vnext-v1.2.3', newer)
            with self.assertRaises(r.ReleaseError):
                r.source(root, 'refs/tags/vnext-v1.2.3', sha)
            r.git(root, 'tag', '-d', 'vnext-v1.2.3')
            with self.assertRaises(r.ReleaseError):
                r.source(root, 'refs/tags/vnext-v1.2.3', sha)
            r.git(root, 'checkout', '-q', '--orphan', 'outside')
            r.git(root, 'commit', '-q', '--allow-empty', '-m', 'outside')
            outside = r.git(root, 'rev-parse', 'HEAD')
            r.git(root, 'tag', 'vnext-v1.2.3')
            with self.assertRaises(r.ReleaseError):
                r.source(root, 'refs/tags/vnext-v1.2.3', outside)


class FakeGitHub:
    repo = 'ruan6047/ai-workflow'

    def __init__(self, files, fail=None):
        self.files = files
        self.fail = fail
        self.calls = []
        self.release = {'id': 7, 'tag_name': 'vnext-v1.2.3', 'name': 'vNext 1.2.3',
                        'draft': True, 'prerelease': True, 'assets': []}

    def absent(self, tag):
        self.calls.append('query')
        if self.fail in ['draft', 'partial', 'complete', '403', 'network']:
            raise r.ReleaseError(self.fail)

    def create(self, *args):
        self.calls.append('create')
        from unittest.mock import patch
        def command(args):
            if args[:3] == ['gh', 'release', 'create']:
                return b''
            if args[:3] == ['gh', 'release', 'view']:
                if self.fail == 'view':
                    raise r.ReleaseError('draft lookup failed')
                return b'{"databaseId": 7}'
            raise AssertionError(args)
        with patch.object(r, 'command', side_effect=command):
            return r.GitHub.create(self, *args)

    def upload(self, tag, paths):
        self.calls.append('upload')
        if self.fail == 'upload':
            raise r.ReleaseError('upload failed')
        self.release['assets'] = [{'id': i, 'name': name, 'state': 'uploaded', 'size': len(data)}
                                  for i, (name, data) in enumerate(self.files.items())]

    def api(self, endpoint, payload=None):
        # 官方 tag REST 端點只承諾 published release，不能回讀新草稿。
        if endpoint.startswith('releases/tags/') and self.release['draft']:
            raise r.ReleaseError('GET release by tag: 404')
        if endpoint != 'releases/7':
            raise AssertionError(endpoint)
        if payload is not None:
            self.calls.append(('publish', payload))
            self.release['draft'] = False
        elif not self.release['draft'] and self.fail == 'readback':
            raise r.ReleaseError('readback failed')
        return self.release

    def download(self, asset, authenticated):
        self.calls.append('authenticated' if authenticated else 'anonymous')
        name = asset['name'] if authenticated else asset['url'].rsplit('/', 1)[1]
        return self.files[name]


class Publication(unittest.TestCase):
    def exercise(self, fail=None):
        import tempfile
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            name = r.wheel_name('1.2.3')
            files = {name: b'candidate', name + '.sha256': b'checksum'}
            for filename, data in files.items():
                (directory / filename).write_bytes(data)
            api = FakeGitHub(files, fail)
            with patch.object(r, 'source', return_value='a' * 40), \
                 patch.object(r, 'clean_source'), patch.object(r, 'verify_wheel'), \
                 patch.object(r, 'summary') as summary:
                if fail:
                    with self.assertRaises(r.ReleaseError):
                        r.publish(directory, directory, 'refs/tags/vnext-v1.2.3', 'a' * 40,
                                  'a' * 40, 'b' * 64, api, 'https://example.invalid/run')
                    self.assertIn('失敗／遠端可能已部分成功', summary.call_args[0][0])
                else:
                    r.publish(directory, directory, 'refs/tags/vnext-v1.2.3', 'a' * 40,
                              'a' * 40, 'b' * 64, api, 'https://example.invalid/run')
                    self.assertIn('發布完成', summary.call_args[0][0])
            return api.calls

    def test_success_draft_bytes_before_publish_anonymous_after(self):
        calls = self.exercise()
        publication = ('publish', {'draft': False, 'prerelease': True, 'make_latest': 'false'})
        self.assertEqual(calls, ['query', 'create', 'upload', 'authenticated', 'authenticated',
                                 publication, 'anonymous', 'anonymous'])

    def test_existing_or_unknown_never_writes(self):
        for fail in ['draft', 'partial', 'complete', '403', 'network']:
            with self.subTest(fail=fail):
                self.assertEqual(self.exercise(fail), ['query'])

    def test_failure_never_recovers_or_claims_success(self):
        self.assertEqual(self.exercise('view'), ['query', 'create'])
        self.assertEqual(self.exercise('upload'), ['query', 'create', 'upload'])
        calls = self.exercise('readback')
        self.assertNotIn('anonymous', calls)
        self.assertEqual(sum(isinstance(x, tuple) for x in calls), 1)


class RemoteBoundaries(unittest.TestCase):
    def test_authenticated_query_all_pages_and_fail_closed(self):
        from unittest.mock import patch
        api = r.GitHub('ruan6047/ai-workflow')
        for state in ['draft', 'partial', 'complete']:
            existing = {'tag_name': 'vnext-v1.2.3', 'state': state}
            with self.subTest(state=state), patch.object(api, 'api', return_value=[existing]), \
                 self.assertRaises(r.ReleaseError):
                api.absent('vnext-v1.2.3')
        with patch.object(api, 'api', side_effect=[[{'tag_name': 'other'}] * 100, []]) as call:
            api.absent('vnext-v1.2.3')
            self.assertEqual(call.call_count, 2)
        for error in [r.ReleaseError('403'), OSError('network')]:
            with patch.object(api, 'api', side_effect=error), self.assertRaises(type(error)):
                api.absent('vnext-v1.2.3')

    def test_gh_commands_and_anonymous_headers(self):
        from unittest.mock import patch, MagicMock
        api = r.GitHub('ruan6047/ai-workflow')
        with patch.object(r, 'command', side_effect=[b'', b'{"databaseId": 7}',
                                                   b'{"id": 7}', b'']) as call:
            self.assertEqual(api.create('vnext-v1.2.3', '1.2.3', 'a' * 40, 'run'), {'id': 7})
            args = call.call_args_list[0].args[0]
            for flag in ['--verify-tag', '--draft', '--prerelease', '--latest=false']:
                self.assertIn(flag, args)
            self.assertEqual(call.call_args_list[1].args[0],
                             ['gh', 'release', 'view', 'vnext-v1.2.3', '--repo', api.repo,
                              '--json', 'databaseId'])
            self.assertEqual(call.call_args_list[2].args[0],
                             ['gh', 'api', f'repos/{api.repo}/releases/7'])
            api.upload('vnext-v1.2.3', [Path('a.whl'), Path('a.whl.sha256')])
            self.assertNotIn('--clobber', call.call_args.args[0])
        response = MagicMock()
        response.__enter__.return_value.read.return_value = b'asset'
        with patch.object(r, 'urlopen', return_value=response) as call:
            self.assertEqual(api.download({'url': 'https://github.com/fixed'}, False), b'asset')
            self.assertFalse(call.call_args.args[0].has_header('Authorization'))

    def test_main_failure_returns_nonzero_and_summary(self):
        from unittest.mock import patch
        with patch.object(r.sys, 'argv', ['release.py', 'publish', '--directory', '/tmp/unused']), \
             patch.object(r, 'command', side_effect=r.ReleaseError('gh failed')), \
             patch.object(r, 'summary') as summary:
            self.assertEqual(r.main(), 1)
            self.assertIn('失敗', summary.call_args.args[0])


class WheelContract(unittest.TestCase):
    def test_exact_content_and_hash_negative_controls(self):
        import tempfile
        import zipfile
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = root / 'vnext/cli/src/wfx/rules'
            package.mkdir(parents=True)
            (package / 'rule.md').write_text('rule')
            (package.parent / '__init__.py').write_text('')
            (root / 'vnext/cli/pyproject.toml').write_text(
                '[project]\nname="ai-workflow-vnext"\nversion="1.2.3"\nrequires-python=">=3.14"\ndependencies=[]\n')
            (root / 'README.md').write_text(
                '版本 `1.2.3`（唯一居所＝`vnext/cli/pyproject.toml`）\n'
                'https://github.com/ruan6047/ai-workflow/releases/download/vnext-v1.2.3/'
                'ai_workflow_vnext-1.2.3-py3-none-any.whl')
            with self.assertRaises(r.ReleaseError):
                r.declaration(root, '1.2.4')
            directory = root / 'dist'
            directory.mkdir()
            wheel = directory / r.wheel_name('1.2.3')
            def write(omit=False):
                with zipfile.ZipFile(wheel, 'w') as z:
                    z.writestr('wfx/__init__.py', '')
                    if not omit:
                        z.writestr('wfx/rules/rule.md', 'rule')
                    prefix = 'ai_workflow_vnext-1.2.3.dist-info/'
                    z.writestr(prefix + 'METADATA',
                               'Name: ai-workflow-vnext\nVersion: 1.2.3\nRequires-Python: >=3.14\n')
                    z.writestr(prefix + 'entry_points.txt', '[console_scripts]\nwfx = wfx.verbs.main:main\n')
            write()
            sha, checksum = r.verify_wheel(root, directory, '1.2.3', with_hash=False)
            (directory / (wheel.name + '.sha256')).write_bytes(checksum)
            self.assertEqual(r.verify_wheel(root, directory, '1.2.3', sha)[0], sha)
            data = bytearray(wheel.read_bytes())
            data[-1] ^= 1
            wheel.write_bytes(data)
            with self.assertRaises(r.ReleaseError):
                r.verify_wheel(root, directory, '1.2.3', sha)
            write(omit=True)
            with self.assertRaises(r.ReleaseError):
                r.verify_wheel(root, directory, '1.2.3', with_hash=False)
            write()
            (directory / 'unexpected').write_text('extra')
            with self.assertRaises(r.ReleaseError):
                r.verify_wheel(root, directory, '1.2.3')


if __name__ == '__main__':
    unittest.main()
