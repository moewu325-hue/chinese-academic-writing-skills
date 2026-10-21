"""从审核过的文件清单生成确定性ZIP；仅使用Python标准库。"""
import argparse
import hashlib
from pathlib import Path, PurePosixPath
import zipfile

FORBIDDEN = {'.git', '.claude', '.codex', '.cursor', '.gemini', '.opencode',
             '.windsurf', '__pycache__', 'node_modules', 'session-memory'}

def release_files(root):
    root = Path(root).resolve()
    names = (root / 'RELEASE_FILES').read_text(encoding='utf-8').splitlines()
    if len(names) != len(set(names)):
        raise ValueError('发行清单有重复项')
    for name in names:
        path = PurePosixPath(name)
        if (not name or path.is_absolute() or '..' in path.parts or
                '\\' in name or ':' in name or set(path.parts) & FORBIDDEN or
                any(part.startswith('.env') for part in path.parts) or name == 'SHA256SUMS'):
            raise ValueError(f'发行清单路径无效: {name}')
        resolved = (root / name).resolve()
        if not resolved.is_relative_to(root) or not resolved.is_file():
            raise ValueError(f'发行清单文件缺失或越界: {name}')
    return sorted(names)

def checksums(root, names):
    return ''.join(f'{hashlib.sha256((root / name).read_bytes()).hexdigest()}  {name}\n'
                   for name in names).encode('utf-8')

def build(root, output):
    root, output = Path(root).resolve(), Path(output).resolve()
    names = release_files(root)
    if output in [(root / name).resolve() for name in names] or output == root / 'SHA256SUMS':
        raise ValueError('输出不能覆盖发行输入')
    payload = {name: (root / name).read_bytes() for name in names}
    payload['SHA256SUMS'] = checksums(root, names)
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name in sorted(payload):
            info = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            info.create_system = 3
            archive.writestr(info, payload[name], compresslevel=9)
    return output

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    names = release_files(root)
    (root / 'SHA256SUMS').write_bytes(checksums(root, names))
    path = build(root, args.output)
    print(f'{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}')

if __name__ == '__main__':
    main()
