"""验证发行包资源可达、路径可迁移，防止夹带私人状态和旧入口。"""
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
NAMES = ('aigc-down-skill', 'research-writing-skill', 'academic-researcher')


class DistributionTests(unittest.TestCase):
    def test_required_entrypoints_and_distribution_docs(self):
        for name in ('README.md', 'LICENSE', 'NOTICE.md', 'VERSION'):
            self.assertTrue((ROOT / name).is_file(), name)
        actual = {p.relative_to(ROOT).as_posix() for p in (ROOT / 'skills').rglob('SKILL.md')}
        self.assertEqual(actual, {f'skills/{name}/SKILL.md' for name in NAMES})
        for name in NAMES:
            text = (ROOT / 'skills' / name / 'SKILL.md').read_text(encoding='utf-8')
            self.assertTrue(text.startswith('---\n'))
            self.assertRegex(text, rf'(?m)^name: {re.escape(name)}$')
            self.assertRegex(text, r'(?m)^description: .+')

    def test_relative_markdown_resources_resolve(self):
        paths = list((ROOT / 'skills').rglob('*.md')) + [ROOT / 'README.md', ROOT / 'NOTICE.md']
        for path in paths:
            text = path.read_text(encoding='utf-8')
            for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)', text):
                if re.match(r'[a-zA-Z][a-zA-Z0-9+.-]*:', target) or target.startswith('#'):
                    continue
                resolved = (path.parent / target.split('#')[0]).resolve()
                self.assertTrue(resolved.is_relative_to(ROOT), (path, target))
                self.assertTrue(resolved.exists(), (path, target))

    def test_runtime_resources_are_portable(self):
        patterns = (r'[CD]:[\\/]', r'\.agent-shared', r'local-paths\.md',
                    r'skill-index\.md', r'Academic revision legacy state root', r'共享workflow')
        for path in (ROOT / 'skills').rglob('*.md'):
            text = path.read_text(encoding='utf-8')
            for pattern in patterns:
                self.assertIsNone(re.search(pattern, text), (path, pattern))

    def test_no_private_state_or_replicating_installers(self):
        forbidden = {'.claude', '.codex', '.cursor', '.opencode', '.windsurf', '.agent',
                     'session-memory', '__pycache__', 'node_modules', '.env'}
        for path in ROOT.rglob('*'):
            self.assertFalse(set(path.relative_to(ROOT).parts) & forbidden, path)
        for name in ('install-skill.js', 'uninstall-skill.js', 'sync-platform-skills.js'):
            self.assertEqual(list(ROOT.rglob(name)), [], name)
        self.assertTrue((ROOT / 'skills/academic-researcher/LICENSE').is_file())


if __name__ == '__main__':
    unittest.main()
