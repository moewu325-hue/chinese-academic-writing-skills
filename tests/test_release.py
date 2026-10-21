"""发行流程的可复跑完整性验证。"""
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]

class ReleaseTests(unittest.TestCase):
    def test_release_version(self):
        self.assertEqual((ROOT / 'VERSION').read_text().strip(), '2026.10.21')

    def test_builder_archive_is_reproducible_and_installable(self):
        script = ROOT / 'tools/build_release.py'
        self.assertTrue(script.is_file(), '缺少可复跑发行构建器')
        spec = importlib.util.spec_from_file_location('release_builder', script)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            a, b = Path(directory) / 'a.zip', Path(directory) / 'b.zip'
            module.build(ROOT, a)
            module.build(ROOT, b)
            self.assertEqual(a.read_bytes(), b.read_bytes())
            with zipfile.ZipFile(a) as archive:
                names = archive.namelist()
                self.assertEqual(len(names), len(set(names)))
                self.assertEqual(set(names), set(module.release_files(ROOT)) | {'SHA256SUMS'})
                for name in names:
                    self.assertFalse(name.startswith('/') or '..' in Path(name).parts)
                    self.assertFalse(set(Path(name).parts) & {'.git', '__pycache__', '.claude', '.codex', '.gemini', 'build'})
                sums = dict(line.split('  ', 1)[::-1] for line in archive.read('SHA256SUMS').decode().splitlines())
                self.assertEqual(set(sums), set(names) - {'SHA256SUMS'})
                for name, digest in sums.items():
                    self.assertEqual(hashlib.sha256(archive.read(name)).hexdigest(), digest, name)
                archive.extractall(Path(directory) / 'installed')
                for name in ('aigc-down-skill', 'research-writing-skill', 'academic-researcher'):
                    self.assertTrue((Path(directory) / 'installed/skills' / name / 'SKILL.md').is_file())

    def test_ci_runs_both_suites(self):
        path = ROOT / '.github/workflows/tests.yml'
        self.assertTrue(path.is_file(), '缺少CI')
        text = path.read_text()
        self.assertIn('unittest discover -s tests', text)
        self.assertIn('unittest discover -s skills/aigc-down-skill/tests', text)

    def test_manifest_rejects_private_paths_and_missing_files(self):
        script = ROOT / 'tools/build_release.py'
        spec = importlib.util.spec_from_file_location('release_builder', script)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ('../escape', '.env', '.claude/config', 'C:/private', 'missing.md'):
                with self.subTest(name=name):
                    (root / 'RELEASE_FILES').write_text(name + '\n')
                    with self.assertRaises(ValueError):
                        module.build(root, root / 'out.zip')
                    self.assertFalse((root / 'out.zip').exists())

    def test_manifest_text_contains_no_private_paths_or_credentials(self):
        import re
        for name in (ROOT / 'RELEASE_FILES').read_text().splitlines():
            text = (ROOT / name).read_text(encoding='utf-8')
            self.assertIsNone(re.search(r'[A-Za-z]:[\\/](?:Users|桌面)|(?:ghp_|github_pat_)[A-Za-z0-9_]{20,}|-----BEGIN (?:RSA |OPENSSH )?PRIVATE KEY-----', text), name)

    def test_checked_in_versions_execute_without_findings(self):
        import json
        import subprocess
        import sys
        result = subprocess.run([sys.executable, '-I', '-B',
            str(ROOT / 'skills/aigc-down-skill/scripts/check_tells.py'),
            '--check', '--root', str(ROOT / 'skills'), '--json'],
            capture_output=True, text=True, encoding='utf-8', check=True)
        report = json.loads(result.stdout)
        self.assertEqual(report['execution_status'], 'ok')
        self.assertEqual(report['errors'], [])
        self.assertEqual(report['findings'], [])
