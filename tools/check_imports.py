"""간단한 정적 임포트 검사 도구
- 프로젝트 내 .py 파일의 import 문을 검사하고, 로컬 패키지로 보이는 import가 실제 파일로 존재하는지 확인
- 완전한 의존성 검사는 아니며, 로컬 모듈 누락/경로 오타를 찾아줌

사용:
  python tools\check_imports.py
"""

import ast
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent


def find_py_files(root: Path):
    for p in root.rglob('*.py'):
        # skip virtualenv and archive
        if 'venv' in p.parts or 'archive' in p.parts or p.match('**/__pycache__/**'):
            continue
        yield p


def parse_imports(file_path: Path):
    try:
        tree = ast.parse(file_path.read_text(encoding='utf-8'))
    except Exception as e:
        return [], f'PARSE_ERROR: {e}'
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                imports.append((n.name, file_path))
        elif isinstance(node, ast.ImportFrom):
            module = node.module
            if module:
                imports.append((module, file_path))
    return imports, None


def module_exists_locally(module_name: str, root: Path):
    # module_name like 'chatbot_web.rag_system'
    parts = module_name.split('.')
    # check for package dir with __init__.py or .py file
    for i in range(len(parts), 0, -1):
        candidate = root.joinpath(*parts[:i])
        if candidate.with_suffix('.py').exists() or candidate.joinpath('__init__.py').exists():
            return True
    return False


def main():
    issues = []
    for py in find_py_files(ROOT):
        imports, err = parse_imports(py)
        if err:
            issues.append((py, 'PARSE_ERROR', err))
            continue
        for mod, origin in imports:
            # ignore stdlib and known third-party by simple heuristic: if startswith project name or 'chatbot_web' check local
            if mod.startswith('chatbot_web') or mod.startswith('elderly_rag_chatbot') or mod.startswith('chatbot'):
                exists = module_exists_locally(mod, ROOT)
                if not exists:
                    issues.append((str(origin), mod, 'MISSING_LOCAL_MODULE'))
    if not issues:
        print('명백한 로컬 import 문제를 찾지 못했습니다.')
        return
    print('발견된 문제 목록:')
    for item in issues:
        print(' -', item)

if __name__ == '__main__':
    main()
