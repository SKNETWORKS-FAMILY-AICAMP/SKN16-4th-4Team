"""프로젝트 정리 도구
- 중복 README, .bat/.sh 파일, 대형 미디어/로그 등을 찾아 `archive/`로 제안 이동
- --apply 옵션을 주면 실제로 이동함

사용:
  python tools\cleanup.py           # 제안만 출력
  python tools\cleanup.py --apply   # 실행(파일 이동)
"""

import os
import shutil
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ARCHIVE_DIR = ROOT / 'archive'

PATTERNS = [
    'README*',
    '*_완전가이드*.md',
    '*.bak',
    '*.old',
    '*.tmp',
    '*.log',
    '*~',
]

EXT_GROUPS = {
    'scripts': ['*.sh', '*.bat', '*.ps1'],
    'docs': ['*.md', '*.rst', '*.txt'],
}

EXCLUDE_DIRS = ['.git', '__pycache__', 'venv', 'archive']


def should_exclude(path: Path):
    for part in path.parts:
        if part in EXCLUDE_DIRS:
            return True
    return False


def find_candidates():
    candidates = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        pdir = Path(dirpath)
        if should_exclude(pdir):
            continue
        for fname in filenames:
            fpath = pdir / fname
            # large files (>5MB) propose archive
            try:
                size = fpath.stat().st_size
            except Exception:
                continue
            if size > 5 * 1024 * 1024:
                candidates.append((fpath, 'large'))
                continue
            # pattern matches
            for pat in PATTERNS:
                if fpath.match(pat):
                    candidates.append((fpath, 'pattern'))
                    break
            else:
                for grp, exts in EXT_GROUPS.items():
                    for ext in exts:
                        if fpath.match(ext):
                            candidates.append((fpath, grp))
                            break
    return candidates


def apply_archive(candidates):
    ARCHIVE_DIR.mkdir(exist_ok=True)
    moved = []
    for fpath, reason in candidates:
        rel = fpath.relative_to(ROOT)
        target = ARCHIVE_DIR / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(fpath), str(target))
        moved.append((fpath, target, reason))
    return moved


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true', help='실제 파일을 archive로 이동')
    args = parser.parse_args()

    candidates = find_candidates()
    if not candidates:
        print('정리 후보 파일이 없습니다.')
        return

    print('정리 후보 목록:')
    for fpath, reason in candidates:
        print(f' - {fpath}  ({reason})')

    if args.apply:
        print('\n--apply 옵션이 지정되어 실제로 파일을 이동합니다...')
        moved = apply_archive(candidates)
        for src, dst, reason in moved:
            print(f'MOVED: {src} -> {dst} ({reason})')
        print('이동 완료')
    else:
        print('\n안내: 위 파일들을 검토하시고 --apply 옵션으로 실제 이동할 수 있습니다.')

if __name__ == '__main__':
    main()
