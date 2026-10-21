"""只用标准库验证差异提示工具；测试数据为独立构造的小样本。"""
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'check_tells.py'


class CheckerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = None
        if not SCRIPT.is_file():
            return
        spec = importlib.util.spec_from_file_location('check_tells', SCRIPT)
        cls.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.module)

    def setUp(self):
        if self.module is None and self._testMethodName != 'test_script_exists':
            self.skipTest('等待实现文件')

    def test_script_exists(self):
        self.assertTrue(SCRIPT.is_file(), '缺少要求实现的 scripts/check_tells.py')

    def compare(self, original, revised, **kwargs):
        result = self.module.compare_texts(original, revised, **kwargs)
        self.assertEqual(result['execution_status'], 'ok')
        for key in ('mode', 'summaries', 'findings', 'errors'):
            self.assertIn(key, result)
        for finding in result['findings']:
            loc = finding['location']
            self.assertGreaterEqual(loc['line'], 1)
            self.assertGreaterEqual(loc['column'], 1)
            self.assertTrue(loc['file'])
            self.assertTrue(loc['snippet'])
            self.assertTrue(finding['question'])
        return result

    def categories(self, result):
        return [f['category'] for f in result['findings']]

    def cli(self, *args):
        completed = subprocess.run([sys.executable, str(SCRIPT), *map(str, args)],
                                   capture_output=True, encoding='utf-8')
        self.assertEqual(completed.returncode, 0, completed.stderr)
        return json.loads(completed.stdout)

    def test_zero_change_has_no_semantic_verdict(self):
        result = self.compare('甲的平均值为3 mg，见[1]，公式为$x=2$。',
                              '甲的平均值为3 mg，见[1]，公式为$x=2$。')
        self.assertEqual(result['findings'], [])
        rendered = json.dumps(result, ensure_ascii=False)
        for forbidden in ('PASS', 'FAIL', 'score', 'semantic_pass', '句长CV'):
            self.assertNotIn(forbidden, rendered)

    def test_numbers_units_and_scientific_notation(self):
        result = self.compare('值为1.2e-3 mg及20%。', '值为1.3e-3 mg及20 kg。')
        self.assertEqual(result['summaries']['numbers']['original'],
                         {'1.2e-3 mg': 1, '20%': 1})
        self.assertEqual(self.categories(result).count('number'), 4)

    def test_formula_and_chinese_citation_not_duplicate_numbers(self):
        result = self.compare('甲[1–3]，$x=2$。', '甲[2–4]，$x=3$。')
        self.assertEqual(self.categories(result).count('citation'), 2)
        self.assertEqual(self.categories(result).count('math'), 2)
        self.assertNotIn('number', self.categories(result))

    def test_math_delimiters_and_environments(self):
        original = r'$$x=2$$ \(y=3\) \[z=4\] \begin{align}a=5\end{align}'
        result = self.compare(original, '')
        self.assertEqual(self.categories(result).count('math'), 4)
        self.assertNotIn('number', self.categories(result))

    def test_tex_and_author_year_citations(self):
        original = r'见\citep[页2]{a,b}、Smith et al. (2020)、张三（2021）。'
        result = self.compare(original, '')
        self.assertEqual(self.categories(result).count('citation'), 3)
        self.assertNotIn('number', self.categories(result))

    def test_unpaired_math_delimiter_is_located(self):
        result = self.compare('第一行\n甲$x=2。', '第一行\n甲$x=2。', orig_path='a.txt')
        findings = [f for f in result['findings'] if f['category'] == 'math_delimiter']
        self.assertTrue(findings)
        self.assertEqual(findings[0]['location']['line'], 2)
        self.assertEqual(findings[0]['location']['column'], 2)
        self.assertEqual(findings[0]['location']['file'], 'a.txt')

    def test_counter_preserves_duplicate_occurrences(self):
        result = self.compare('甲3 mg，乙3 mg，丙3 mg。', '甲3 mg。')
        numbers = [f for f in result['findings'] if f['category'] == 'number']
        self.assertEqual(len(numbers), 2)
        self.assertEqual([f['location']['column'] for f in numbers], [8, 14])

    def test_duplicate_location_is_a_counter_candidate(self):
        result = self.compare('甲为3，乙为3。', '乙为3。')
        finding = next(f for f in result['findings'] if f['category'] == 'number')
        self.assertEqual(finding['location_basis'], 'counter_candidate')
        self.assertIn('计数候选', finding['question'])

    def test_duplicate_citations_and_math(self):
        result = self.compare('[1]、[1]、$x=2$、$x=2$', '[1]、$x=2$')
        self.assertEqual(self.categories(result).count('citation'), 1)
        self.assertEqual(self.categories(result).count('math'), 1)

    def test_raw_locations_after_markup(self):
        result = self.compare('**甲**\n乙的值3 mg。', '**甲**\n乙的值4 mg。',
                              orig_path='before.md', rev_path='after.md')
        found = next(f for f in result['findings'] if f['category'] == 'number')
        self.assertEqual(found['location'],
                         {'file': 'before.md', 'line': 2, 'column': 4, 'snippet': '3 mg'})

    def test_body_length_excludes_formats_code_math_metadata(self):
        text = '**正文**\n```python\n123\n```\n$x=2$\\label{sec:1}\\ref{sec:1}\\cite{a}\\textbf{甲}'
        result = self.compare(text, text)
        self.assertEqual(result['summaries']['body_length']['original'], 3)

    def test_empty_original_ratio_undefined(self):
        result = self.compare('', '新增正文')
        self.assertIsNone(result['summaries']['body_length']['ratio'])
        self.assertIn('length', self.categories(result))

    def test_empty_both_has_no_findings(self):
        self.assertEqual(self.compare('', '')['findings'], [])

    def test_length_threshold_boundaries(self):
        for length in (92, 108):
            self.assertNotIn('length', self.categories(self.compare('甲' * 100, '甲' * length)))
        for length in (91, 109):
            self.assertIn('length', self.categories(self.compare('甲' * 100, '甲' * length)))
        self.assertNotIn('possible_omission', self.categories(self.compare('甲' * 100, '甲' * 90)))
        self.assertIn('possible_omission', self.categories(self.compare('甲' * 100, '甲' * 89)))

    def test_non_preserving_mode_suppresses_length_alerts(self):
        result = self.compare('甲' * 100, '甲', preserve_length=False)
        self.assertNotIn('length', self.categories(result))
        self.assertNotIn('possible_omission', self.categories(result))

    def test_multiline_bold(self):
        result = self.compare('原文', '**第一行\n第二行**')
        bold = result['summaries']['style']['bold']
        self.assertEqual((bold['original'], bold['revised'], bold['direction']), (0, 1, 'increased'))
        self.assertIn('bold', self.categories(result))

    def test_longest_nonoverlapping_words(self):
        result = self.compare('', '不仅仅不仅未必不')
        words = result['summaries']['negation']['revised']
        self.assertEqual(words['不仅仅'], 1)
        self.assertEqual(words['不仅'], 1)
        self.assertEqual(words['未必'], 1)
        self.assertEqual(words['不'], 1)

    def test_dashes_colons_and_ternary_lists(self):
        result = self.compare('甲', '甲——乙—丙--丁：戊:己。指标、方法、结果。')
        style = result['summaries']['style']
        self.assertEqual(style['dashes']['revised'], 3)
        self.assertEqual(style['colons']['revised'], 2)
        self.assertEqual(style['enumeration_candidates']['revised'], 1)
        self.assertIn('enumeration_candidates', self.categories(result))

    def test_negation_and_qualifier_count_changes_are_questions(self):
        result = self.compare('甲未增加，通常仅适用于乙。', '甲增加，适用于乙。')
        self.assertIn('negation', self.categories(result))
        self.assertIn('qualifier', self.categories(result))
        self.assertEqual(result['summaries']['negation']['direction'], 'decreased')

    def test_equal_counts_cannot_detect_object_swap(self):
        result = self.compare('甲为3，乙为4；甲未增加，乙增加。',
                              '甲为4，乙为3；甲增加，乙未增加。')
        self.assertEqual(result['summaries']['numbers']['direction'], 'unchanged')
        self.assertEqual(result['summaries']['negation']['direction'], 'unchanged')
        self.assertNotIn('number', self.categories(result))
        self.assertNotIn('negation', self.categories(result))

    def test_missing_file_and_invalid_utf8(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            good = folder / 'good.txt'
            bad = folder / 'bad.txt'
            good.write_text('正文', encoding='utf-8')
            bad.write_bytes(b'\xff')
            for original in (folder / 'missing.txt', bad):
                result = self.cli('--orig', original, '--rev', good, '--json')
                self.assertEqual(result['execution_status'], 'error')
                self.assertTrue(result['errors'])

    def test_argument_errors_have_json_and_zero_exit(self):
        for args in ([], ['--orig', 'x'], ['--check', '--orig', 'x', '--rev', 'y'],
                     ['--wat'], ['--root', 'x'], ['--check', '--non-preserving-length']):
            with self.subTest(args=args):
                result = self.cli(*args, '--json')
                self.assertEqual(result['execution_status'], 'error')
                self.assertTrue(result['errors'])

    def test_public_main_returns_zero_and_cli_does_not_write_inputs(self):
        with tempfile.TemporaryDirectory() as temp:
            orig, rev = Path(temp) / 'a.md', Path(temp) / 'b.md'
            orig.write_text('甲为3。', encoding='utf-8')
            rev.write_text('甲为4。', encoding='utf-8')
            before = [hashlib.sha256(p.read_bytes()).hexdigest() for p in (orig, rev)]
            with contextlib.redirect_stdout(io.StringIO()) as output:
                code = self.module.main(['--orig', str(orig), '--rev', str(rev), '--json',
                                         '--non-preserving-length'])
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(output.getvalue())['execution_status'], 'ok')
            self.assertEqual(before, [hashlib.sha256(p.read_bytes()).hexdigest() for p in (orig, rev)])

    def test_same_file_locates_original_without_comparison(self):
        with tempfile.TemporaryDirectory() as temp:
            original = Path(temp) / 'a.md'
            original.write_text('综上所述，**指标、方法、结果**：通常未增加。', encoding='utf-8')
            result = self.cli('--orig', original, '--rev', original, '--json')
            self.assertEqual(result['mode'], 'locate')
            self.assertFalse(result['comparison_performed'])
            self.assertIn('tells', self.categories(result))
            self.assertIn('bold', self.categories(result))
            self.assertNotIn('revised', result['summaries']['body_length'])
            self.assertTrue(all(f['location']['file'] == str(original) for f in result['findings']))

    def test_different_files_compare_even_if_text_equal(self):
        with tempfile.TemporaryDirectory() as temp:
            original, revised = Path(temp) / 'a.md', Path(temp) / 'b.md'
            for path in (original, revised):
                path.write_text('正文', encoding='utf-8')
            result = self.cli('--orig', original, '--rev', revised, '--json')
            self.assertEqual(result['mode'], 'compare')
            self.assertTrue(result['comparison_performed'])

    def test_cli_keeps_crlf_in_original_snippet(self):
        with tempfile.TemporaryDirectory() as temp:
            original, revised = Path(temp) / 'a.md', Path(temp) / 'b.md'
            original.write_bytes('原文'.encode('utf-8'))
            revised.write_bytes('**甲\r\n乙**'.encode('utf-8'))
            result = self.cli('--orig', original, '--rev', revised, '--json')
            bold = next(f for f in result['findings'] if f['category'] == 'bold')
            self.assertEqual(bold['location']['snippet'], '**甲\r\n乙**')

    def fixture(self, folder):
        for skill, field in (('aigc-down-skill', '执行版本'), ('research-writing-skill', '执行版本'),
                             ('academic-researcher', '职责版本')):
            path = folder / skill / 'SKILL.md'
            path.parent.mkdir(parents=True)
            path.write_text(f'# 标题\n{field} `2026-10-07.3`。\n其它日期2020-01-01\n', encoding='utf-8')
        sources = folder / 'aigc-down-skill' / 'references' / 'sources.md'
        sources.parent.mkdir()
        sources.write_text('执行版本2026-10-07.3。', encoding='utf-8')

    def test_version_mismatch_is_located_and_independent_host_not_compared(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            self.fixture(folder)
            (folder / 'academic-researcher' / 'SKILL.md').write_text('标题\n职责版本2026-10-08.1。', encoding='utf-8')
            (folder / 'research-writing-skill' / 'SKILL.md').write_text('标题\n执行版本2026-10-08.1。', encoding='utf-8')
            index = folder / 'index.md'
            index.write_text('共享规则版本2026-10-07.3。', encoding='utf-8')
            host = folder / 'host'
            for name in ('aigc-down-skill', 'research-writing-skill'):
                path = host / name / 'SKILL.md'
                path.parent.mkdir(parents=True)
                path.write_text('宿主入口版本2099-01-01-host\n共享规则版本2026-10-07.3。', encoding='utf-8')
            result = self.cli('--check', '--root', folder, '--index', index, '--host', host, '--json')
            self.assertEqual(result['execution_status'], 'ok')
            mismatches = [f for f in result['findings'] if f['category'] == 'version_mismatch']
            self.assertEqual(len(mismatches), 1)
            self.assertEqual(mismatches[0]['location']['line'], 2)
            self.assertEqual(mismatches[0]['field'], '执行版本')
            self.assertEqual(len(result['summaries']['host_versions']), 2)
            self.assertEqual(result['summaries']['host_versions'][0]['version'], '2099-01-01-host')

    def test_independent_duty_version_is_reported_without_shared_mismatch(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            self.fixture(folder)
            (folder / 'academic-researcher' / 'SKILL.md').write_text(
                '职责版本2026-10-12.1。', encoding='utf-8')
            result = self.cli('--check', '--root', folder, '--json')
            self.assertEqual(result['execution_status'], 'ok')
            self.assertEqual(result['findings'], [])
            duty = [r for r in result['summaries']['versions'] if r['field'] == '职责版本']
            self.assertEqual(duty[0]['version'], '2026-10-12.1')

    def test_version_missing_duplicate_and_missing_file_reported(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            self.fixture(folder)
            (folder / 'aigc-down-skill' / 'SKILL.md').write_text('执行版本2026-10-07.3\n执行版本2026-10-07.3', encoding='utf-8')
            (folder / 'research-writing-skill' / 'SKILL.md').write_text('无字段', encoding='utf-8')
            (folder / 'academic-researcher' / 'SKILL.md').unlink()
            result = self.cli('--check', '--root', folder, '--json')
            self.assertEqual(result['execution_status'], 'error')
            self.assertEqual(len(result['errors']), 3)
            rendered = json.dumps(result, ensure_ascii=False)
            for word in ('重复', '缺少', 'SKILL.md'):
                self.assertIn(word, rendered)

    def test_optional_version_sources_not_required_when_omitted(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            self.fixture(folder)
            result = self.cli('--check', '--root', folder, '--json')
            self.assertEqual(result['execution_status'], 'ok')
            self.assertEqual(result['findings'], [])

    def test_shared_version_does_not_accept_a_valid_prefix(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            self.fixture(folder)
            path = folder / 'research-writing-skill' / 'SKILL.md'
            for version in ('2026-10-07.3-draft', '2026-10-07.3.2', '2026-10-07.3x'):
                with self.subTest(version=version):
                    path.write_text('执行版本' + version + '。', encoding='utf-8')
                    result = self.cli('--check', '--root', folder, '--json')
                    self.assertEqual(result['execution_status'], 'error')
                    self.assertTrue(any(e.get('file') == str(path) for e in result['errors']))


if __name__ == '__main__':
    unittest.main()
