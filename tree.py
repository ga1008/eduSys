import os
from pathlib import Path


def print_tree(directory, prefix="", ignore_patterns=None):
    if ignore_patterns is None:
        ignore_patterns = ['.git', '__pycache__', '*.pyc', '.idea', 'venv']

    # 获取目录内容并排序
    path = Path(directory)
    entries = sorted(list(path.iterdir()))

    # 过滤掉不需要显示的文件和目录
    filtered_entries = []
    for entry in entries:
        skip = False
        for pattern in ignore_patterns:
            if pattern.startswith('*'):
                if entry.name.endswith(pattern[1:]):
                    skip = True
                    break
            elif pattern in str(entry):
                skip = True
                break
        if not skip:
            filtered_entries.append(entry)

    # 遍历并打印目录结构
    for i, entry in enumerate(filtered_entries):
        is_last = i == len(filtered_entries) - 1
        current_prefix = "└── " if is_last else "├── "
        print(f"{prefix}{current_prefix}{entry.name}")

        if entry.is_dir():
            next_prefix = prefix + ("    " if is_last else "│   ")
            print_tree(entry, next_prefix, ignore_patterns)


def main():
    # 获取项目根目录
    project_root = os.path.dirname(os.path.abspath(__file__))
    project_name = os.path.basename(project_root)

    print(f"{project_name}/")
    print_tree(project_root)


if __name__ == "__main__":
    main()