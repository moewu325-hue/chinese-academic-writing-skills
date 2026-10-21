"""只读的中文学术文字差异提示，不证明语义等价，也不自动改写。

数字支持阿拉伯数字、小数、常见单位及 e/E、×10^ 科学记数。
数学为启发式：识别未转义的 $、$$、\\(、\\[ 和常见 equation、align、
gather、multline、displaymath、math 环境，不解析 TeX 宏、嵌套语法或数学含义。
作者年份为启发式：识别常见英文作者名或 2—8 字中文作者名后的括号年份；
不涵盖全部引文格式，可能把普通姓名年份认作候选。中文方括号编号和 TeX
cite 系列命令另行提取。数字位于已识别数学或引文内时不重复提示。

可读正文长度：去除识别到的数学、围栏代码、TeX 命令名以及 label/ref/cite
元数据、Markdown 格式标记与链接目标，计剩余非空白字符，含正文标点。
统计仅用于回读，所有位置均基于未经清洗的输入文本，行列从 1 开始。
集合与词频相同无法发现数值归属、否定对象或条件互换。
重复片段按出现顺序抵消；剩余位置是计数候选，不能确认哪一对象处实际增删。
只报告、不打分、不设文本质量通过线、不连接任何检测器、不计算句长 CV。
CLI返回路径的退出码恒为0；执行是否完成须读取 execution_status，不能凭退出码判断。
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re
import sys


NEGATIONS = ('不仅仅', '不仅', '不意味着', '并不', '并非', '不能', '不会', '没有',
             '未必', '尚未', '无法', '无论', '未', '不', '无', '否')
QUALIFIERS = ('在一定程度上', '在此条件下', '通常', '可能', '或许', '一般', '部分',
              '至少', '至多', '仅仅', '仅', '只', '除非', '如果', '当且仅当', '一定')
TELLS = ('值得注意的是', '综上所述', '总而言之', '不仅仅', '不仅', '与此同时',
         '在此基础上', '此外', '首先', '其次', '最后', '总之', '显著', '赋能')
ENV_NAMES = r'(?:equation\*?|align\*?|alignat\*?|gather\*?|multline\*?|displaymath|math|eqnarray\*?)'
MATH_TOKEN = re.compile(r'\$\$|\$|\\[()\[\]]|\\(?:begin|end)\{' + ENV_NAMES + r'\}')
FENCE = re.compile(r'(?m)^[ \t]{0,3}(`{3,}|~{3,})[^\n]*\n')
CITE = re.compile(
    r'\\(?:[Cc]ite[a-zA-Z]*|[Pp]arencite|[Tt]extcite|[Aa]utocite|[Ff]ootcite|[Nn]ocite)'
    r'\*?(?:\s*\[[^\]]*\])*\s*\{[^{}]*\}'
    r'|\[\s*\d+(?:\s*(?:[,，;；]|[-–—])\s*\d+)*\s*\]'
    r'|(?<![A-Za-z])(?:[A-Z][A-Za-z\xC0-\u024f\x27-]+(?:\s+(?:et\s+al\.|and\s+[A-Z][A-Za-z\x27-]+|&\s*[A-Z][A-Za-z\x27-]+))?'
    r'|[\u4e00-\u9fff]{2,8})(?:\s*[（(](?:18|19|20|21)\d{2}[a-z]?(?:\s*[,，;；]\s*(?:18|19|20|21)\d{2}[a-z]?)*[）)])')
METADATA = re.compile(r'\\(?:label|(?:eq|auto|page|c|C)?ref|[Cc]ite[a-zA-Z]*|[Pp]arencite|[Tt]extcite|[Aa]utocite|[Ff]ootcite|[Nn]ocite)\*?(?:\s*\[[^\]]*\])*\s*\{[^{}]*\}')
NUMBER = re.compile(
    r'[+\-−]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?'
    r'(?:[eE][+\-−]?\d+|\s*[×x]\s*10\s*\^\s*\{?[+\-−]?\d+\}?)?'
    r'(?:[ \t]*(?:mmol/L|mol/L|mg/mL|mg/L|kg/m³|kg/m3|m/s|km/h|mmHg|kPa|MPa|GHz|MHz|Hz|'
    r'厘米|毫米|千米|毫克|千克|公斤|小时|分钟|百分点|百分比|万元|亿元|万|亿|年|月|日|天|次|人|个|秒|米|克|'
    r'kg|mg|μg|µg|ug|km|cm|mm|nm|mL|ml|μL|µL|Pa|K|L|g|m|s|h|%|％|‰|℃|°C))?')
BOLD = re.compile(r'\*\*(?=\S)[\s\S]*?\*\*|__(?=\S)[\s\S]*?__')
ENUMERATION = re.compile(r'[^\s、，,。；;：:\n]{1,24}(?:、[^\s、，,。；;：:\n]{1,24}){2,}')


def _result(mode):
    return {'execution_status': 'ok', 'mode': mode, 'comparison_performed': False,
            'summaries': {}, 'findings': [], 'errors': []}


def _location(text, start, end, path):
    return {'file': str(path), 'line': text.count('\n', 0, start) + 1,
            'column': start - text.rfind('\n', 0, start), 'snippet': text[start:end]}


def _finding(category, text, span, path, question, **extra):
    return {'category': category, 'location': _location(text, span[0], span[1], path),
            'question': question, **extra}


def _matches(pattern, text):
    return [(m.start(), m.end(), m.group()) for m in pattern.finditer(text)]


def _mask(text, spans):
    chars = list(text)
    for start, end, *_ in spans:
        for pos in range(start, end):
            if chars[pos] not in '\r\n':
                chars[pos] = ' '
    return ''.join(chars)


def _code_spans(text):
    spans = []
    pos = 0
    while opening := FENCE.search(text, pos):
        fence = opening.group(1)
        closing = re.search(r'(?m)^[ \t]{0,3}' + re.escape(fence[0]) +
                            '{' + str(len(fence)) + r',}[ \t]*\r?$', text[opening.end():])
        end = opening.end() + closing.end() if closing else len(text)
        spans.append((opening.start(), end, text[opening.start():end]))
        pos = end
    return spans


def _escaped(text, pos):
    backslashes = 0
    pos -= 1
    while pos >= 0 and text[pos] == '\\':
        backslashes += 1
        pos -= 1
    return backslashes % 2 == 1


def _math_spans(text):
    tokens = [m for m in MATH_TOKEN.finditer(text) if not _escaped(text, m.start())]
    spans, unmatched = [], []
    i = 0
    while i < len(tokens):
        token = tokens[i]
        value = token.group()
        if value in ('\\)', '\\]') or value.startswith('\\end'):
            unmatched.append((token.start(), token.end(), value))
            i += 1
            continue
        closing = {'\\(': '\\)', '\\[': '\\]'}.get(value, value)
        if value.startswith('\\begin'):
            closing = value.replace('\\begin', '\\end', 1)
        match_index = next((j for j in range(i + 1, len(tokens)) if tokens[j].group() == closing), None)
        if match_index is None:
            unmatched.append((token.start(), token.end(), value))
            i += 1
        else:
            end = tokens[match_index].end()
            spans.append((token.start(), end, text[token.start():end]))
            i = match_index + 1
    return spans, unmatched


def _word_spans(text, words):
    pattern = re.compile('|'.join(re.escape(word) for word in sorted(words, key=len, reverse=True)))
    return _matches(pattern, text)


def _body(text, code, math):
    readable = _mask(text, code + math)
    readable = METADATA.sub('', readable)
    readable = re.sub(r'\\[A-Za-z]+\*?', '', readable)
    readable = re.sub(r'!?\[([^\]\n]+)\]\([^\)\n]+\)', r'\1', readable)
    readable = re.sub(r'(?m)^\s{0,3}(?:#{1,6}\s+|>\s*|[-+*]\s+|\d+[.)]\s+)', '', readable)
    readable = re.sub(r'[*_`~{}]', '', readable)
    return readable


def _extract(text):
    code = _code_spans(text)
    no_code = _mask(text, code)
    math, unmatched = _math_spans(no_code)
    citations = _matches(CITE, _mask(no_code, math))
    prose = _mask(no_code, math + citations + _matches(METADATA, no_code))
    body = _body(text, code, math)
    return {'math': math, 'citation': citations, 'number': _matches(NUMBER, prose),
            'math_delimiter': unmatched, 'tells': _word_spans(prose, TELLS),
            'negation': _word_spans(prose, NEGATIONS), 'qualifier': _word_spans(prose, QUALIFIERS),
            'bold': _matches(BOLD, no_code), 'colons': _matches(re.compile(r'[:：]'), prose),
            'dashes': _matches(re.compile(r'——|—|–|--'), prose),
            'enumeration_candidates': _matches(ENUMERATION, prose),
            'length': sum(not char.isspace() for char in body)}


def _direction(original, revised):
    return 'increased' if revised > original else 'decreased' if revised < original else 'unchanged'


def _counter(spans):
    return Counter(span[2] for span in spans)


def _counter_summary(original, revised):
    a, b = _counter(original), _counter(revised)
    changes = {key: {'original': a[key], 'revised': b[key], 'direction': _direction(a[key], b[key])}
               for key in sorted(a.keys() | b.keys()) if a[key] != b[key]}
    return {'original': dict(a), 'revised': dict(b), 'direction': _direction(sum(a.values()), sum(b.values())),
            'changes': changes}


def _diff_findings(category, a, b, original, revised, orig_path, rev_path, question):
    findings = []
    counts = _counter(a) | _counter(b)
    for spans, other, text, path, change in ((a, b, original, orig_path, 'removed'),
                                            (b, a, revised, rev_path, 'added')):
        available = _counter(other)
        for span in spans:
            if available[span[2]]:
                available[span[2]] -= 1
            else:
                note = '此处为计数候选；同值片段的实际增删位置需回读核对。' if counts[span[2]] > 1 else ''
                findings.append(_finding(category, text, span, path, question + note,
                                         change=change, location_basis='counter_candidate'))
    return findings


def _length_anchor(original, revised, orig_path, rev_path):
    for text, path in ((revised, rev_path), (original, orig_path)):
        match = re.search(r'\S', text)
        if match:
            end = min(len(text), match.start() + 80)
            return text, (match.start(), end), path
    return None


def compare_texts(original, revised, *, orig_path='orig', rev_path='rev', preserve_length=True):
    """返回计数与需人工核对的位置；无 findings 不代表语义正确。"""
    result = _result('compare')
    if not isinstance(original, str) or not isinstance(revised, str):
        result['execution_status'] = 'error'
        result['errors'].append({'message': '原稿和改稿必须是字符串。'})
        return result
    result['comparison_performed'] = True
    a, b = _extract(original), _extract(revised)
    result['summaries']['numbers'] = _counter_summary(a['number'], b['number'])
    result['summaries']['math'] = _counter_summary(a['math'], b['math'])
    result['summaries']['citations'] = _counter_summary(a['citation'], b['citation'])
    questions = {'number': '此处数值或单位的增删是否符合原稿的对象、范围与精度？',
                 'math': '此处数学片段的增删是否保留原式、变量与条件？',
                 'citation': '此处引文的增删是否保留出处及对应主张？',
                 'tells': '此处定位词的变化是否符合段落任务，是否需要保留？',
                 'negation': '此处否定词的增删是否保留否定结果及其对象？词频变化本身不判语义错误。',
                 'qualifier': '此处限定词的增删是否保留范围、条件与主张强度？词频变化本身不判语义错误。'}
    for category, question in questions.items():
        if category in ('tells', 'negation', 'qualifier'):
            result['summaries'][category] = _counter_summary(a[category], b[category])
        result['findings'].extend(_diff_findings(category, a[category], b[category], original, revised,
                                                orig_path, rev_path, question))
    for text, values, path in ((original, a, orig_path), (revised, b, rev_path)):
        for span in values['math_delimiter']:
            result['findings'].append(_finding('math_delimiter', text, span, path,
                                              '此数学分隔符未配对；是否有漏写、转义或未覆盖的数学语法？'))
    ratio = b['length'] / a['length'] if a['length'] else None
    result['summaries']['body_length'] = {'original': a['length'], 'revised': b['length'],
                                         'ratio': ratio, 'preserve_length': preserve_length,
                                         'direction': _direction(a['length'], b['length'])}
    anchor = _length_anchor(original, revised, orig_path, rev_path)
    if preserve_length and anchor:
        text, span, path = anchor
        if (a['length'] and (b['length'] * 100 < a['length'] * 92 or b['length'] * 100 > a['length'] * 108)) or (not a['length'] and b['length']):
            result['findings'].append(_finding('length', text, span, path,
                                              '全文可读正文长度比在92%—108%外或原正文为空；是否仍满足保量任务？此位置为全文回读锚点。'))
        if a['length'] and b['length'] * 100 < a['length'] * 90:
            result['findings'].append(_finding('possible_omission', text, span, path,
                                              '全文可读正文低于原稿90%；是否漏删独立命题、条件或评价？此位置为全文回读锚点。'))
    result['summaries']['style'] = {}
    for category, question in (
            ('bold', '此处加粗的变化是否符合文体，跨行范围是否正确？'),
            ('colons', '此处冒号的变化是否符合后文关系？密度变化本身不判表达错误。'),
            ('dashes', '此处破折号的变化是否保留插入、解释或转折关系？'),
            ('enumeration_candidates', '此处三项以上顿号并列是否为必要清单，或有材料支持的动作关系？')):
        ac, bc = len(a[category]), len(b[category])
        result['summaries']['style'][category] = {
            'original': ac, 'revised': bc, 'direction': _direction(ac, bc),
            'density_original': ac / a['length'] if a['length'] else None,
            'density_revised': bc / b['length'] if b['length'] else None}
        if ac != bc:
            result['findings'].extend(_diff_findings(category, a[category], b[category], original, revised,
                                                    orig_path, rev_path, question))
    return result


def _locate_text(text, path):
    result = _result('locate')
    values = _extract(text)
    summaries = result['summaries']
    summaries['body_length'] = {'original': values['length']}
    for key, category in (('numbers', 'number'), ('math', 'math'), ('citations', 'citation'),
                          ('tells', 'tells'), ('negation', 'negation'), ('qualifier', 'qualifier')):
        summaries[key] = {'original': dict(_counter(values[category]))}
    summaries['style'] = {}
    questions = {
        'tells': '此定位词是否承担实际衔接或评价任务，是否需要保留？',
        'negation': '此否定词对应哪项结果或目的，其对象与范围是否明确？',
        'qualifier': '此限定词对应哪项条件、范围或主张强度，是否完整？',
        'bold': '此处加粗是否符合文体，跨行范围是否正确？',
        'colons': '此冒号后文是否确为解释、定义或必要清单？',
        'dashes': '此破折号是否承担明确的插入、解释或转折关系？',
        'enumeration_candidates': '此三项以上顿号并列是否为必要清单，或有材料支持的动作关系？',
        'math_delimiter': '此数学分隔符未配对；是否有漏写、转义或未覆盖的数学语法？'}
    for category, question in questions.items():
        if category in ('bold', 'colons', 'dashes', 'enumeration_candidates'):
            summaries['style'][category] = {
                'original': len(values[category]),
                'density_original': len(values[category]) / values['length'] if values['length'] else None}
        for span in values[category]:
            result['findings'].append(_finding(category, text, span, path, question))
    return result


def _read(path, result):
    try:
        return Path(path).read_bytes().decode('utf-8')
    except (OSError, UnicodeError, ValueError) as exc:
        result['execution_status'] = 'error'
        result['errors'].append({'file': str(path), 'message': f'无法读取UTF-8文件：{exc}'})
        return None


def _version_records(text, path, field):
    suffix = r'(?:-[A-Za-z][A-Za-z0-9.-]*)?' if field in ('宿主版本', '宿主入口版本') else ''
    pattern = re.compile(re.escape(field) + r'\s*[:：]?\s*[`"\x27]?\s*(\d{4}-\d{2}-\d{2}(?:\.\d+)?' + suffix + r')(?![A-Za-z0-9_.-])')
    return [{'field': field, 'version': m.group(1), 'location': _location(text, m.start(), m.end(), path)}
            for m in pattern.finditer(text)]


def check_versions(root, *, index=None, host=None):
    """只读指定白名单文件；可选源仅在显式传入时核查。"""
    result = _result('check')
    root = Path(root)
    wanted = [(root / 'aigc-down-skill' / 'SKILL.md', '执行版本'),
              (root / 'research-writing-skill' / 'SKILL.md', '执行版本'),
              (root / 'academic-researcher' / 'SKILL.md', '职责版本'),
              (root / 'aigc-down-skill' / 'references' / 'sources.md', '执行版本')]
    if index is not None:
        wanted.append((Path(index), '共享规则版本'))
    host_paths = []
    if host is not None:
        host_paths = [Path(host) / name / 'SKILL.md' for name in ('aigc-down-skill', 'research-writing-skill')]
        wanted.extend((path, '共享规则版本') for path in host_paths)
    records, independent = [], []
    for path, field in wanted:
        text = _read(path, result)
        if text is None:
            continue
        found = _version_records(text, path, field)
        if len(found) != 1:
            result['execution_status'] = 'error'
            result['errors'].append({'file': str(path), 'field': field,
                                     'message': f'{field}重复：找到{len(found)}处。' if found else f'缺少明确的{field}字段。'})
            for record in found:
                result['findings'].append({'category': 'version_duplicate', **record,
                                          'question': f'{field}字段重复；应以哪一处为唯一执行字段？'})
        else:
            records.append(found[0])
        if path in host_paths:
            independent.extend(_version_records(text, path, '宿主入口版本') or
                               _version_records(text, path, '宿主版本'))
    result['summaries'] = {'versions': records, 'host_versions': independent}
    baseline = next((record for record in records if record['location']['file'] == str(wanted[0][0])), None)
    if baseline:
        result['summaries']['reference_version'] = baseline['version']
        for record in records:
            # 职责版本独立演进，仅检查字段完整性。
            if record['field'] != '职责版本' and record['version'] != baseline['version']:
                result['findings'].append({'category': 'version_mismatch', **record,
                                          'reference_version': baseline['version'],
                                          'question': f'此{record["field"]}为{record["version"]}，与共享执行基准{baseline["version"]}不一致；是否需同步规则？'})
    return result


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        raise ValueError(message)


def main(argv=None):
    """工具的正常返回路径均返回0，执行错误由 execution_status 表达。"""
    args = list(sys.argv[1:] if argv is None else argv)
    parser = _Parser(description='只读差异与版本核查，提示不构成语义等价证明。')
    parser.add_argument('--orig')
    parser.add_argument('--rev')
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--root')
    parser.add_argument('--index')
    parser.add_argument('--host')
    parser.add_argument('--json', action='store_true')
    parser.add_argument('--non-preserving-length', action='store_true')
    try:
        options = parser.parse_args(args)
        if options.check:
            if options.orig is not None or options.rev is not None or options.non_preserving_length:
                raise ValueError('--check与稿件对比参数互斥。')
            root = options.root if options.root is not None else Path(__file__).resolve().parents[2]
            result = check_versions(root, index=options.index, host=options.host)
        else:
            if options.orig is None or options.rev is None:
                raise ValueError('对比模式必须同时提供--orig与--rev；版本模式使用--check。')
            if options.root is not None or options.index is not None or options.host is not None:
                raise ValueError('--root、--index、--host仅用于--check。')
            result = _result('compare')
            original, revised = _read(options.orig, result), _read(options.rev, result)
            if original is not None and revised is not None:
                if Path(options.orig).resolve() == Path(options.rev).resolve() or Path(options.orig).samefile(options.rev):
                    result = _locate_text(original, options.orig)
                else:
                    result = compare_texts(original, revised, orig_path=options.orig, rev_path=options.rev,
                                           preserve_length=not options.non_preserving_length)
    except SystemExit:
        return 0
    except (ValueError, OSError) as exc:
        result = _result('arguments')
        result['execution_status'] = 'error'
        result['errors'].append({'message': str(exc)})
    if '--json' in args:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f'执行状态：{result["execution_status"]}；模式：{result["mode"]}')
        print('统计：' + json.dumps(result['summaries'], ensure_ascii=False))
        for finding in result['findings']:
            loc = finding['location']
            print(f'{loc["file"]}:{loc["line"]}:{loc["column"]} {loc["snippet"]!r} {finding["question"]}')
        for error in result['errors']:
            print(f'{error.get("file", "参数")}: {error["message"]}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
