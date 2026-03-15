"""
services/parser.py
Multi-language file parser - extracts code content with metadata
"""

import os
import chardet

# Supported file extensions and their language labels
SUPPORTED_EXTENSIONS = {
    '.py': 'python', '.js': 'javascript', '.ts': 'typescript',
    '.jsx': 'jsx', '.tsx': 'tsx', '.java': 'java',
    '.cpp': 'cpp', '.c': 'c', '.h': 'c_header',
    '.cs': 'csharp', '.go': 'go', '.rb': 'ruby',
    '.php': 'php', '.swift': 'swift', '.kt': 'kotlin',
    '.rs': 'rust', '.html': 'html', '.css': 'css',
    '.json': 'json', '.yaml': 'yaml', '.yml': 'yaml',
    '.md': 'markdown', '.txt': 'text', '.sql': 'sql',
    '.sh': 'shell', '.xml': 'xml'
}

IGNORE_DIRS = {
    'node_modules', '__pycache__', '.git', '.venv', 'venv',
    'dist', 'build', '.next', 'coverage', '.idea', '.vscode'
}

IGNORE_FILES = {'.gitignore', '.DS_Store', 'package-lock.json', 'yarn.lock'}


def parse_file(filepath: str) -> dict | None:
    """
    Parse a single file and return its content + metadata.
    Returns None if the file should be skipped.
    """
    _, ext = os.path.splitext(filepath.lower())
    if ext not in SUPPORTED_EXTENSIONS:
        return None

    filename = os.path.basename(filepath)
    if filename in IGNORE_FILES:
        return None

    try:
        # Detect encoding first
        with open(filepath, 'rb') as f:
            raw = f.read()
        detected = chardet.detect(raw)
        encoding = detected.get('encoding', 'utf-8') or 'utf-8'

        content = raw.decode(encoding, errors='replace')

        return {
            'filepath': filepath,
            'filename': filename,
            'language': SUPPORTED_EXTENSIONS[ext],
            'extension': ext,
            'content': content,
            'size_bytes': len(raw),
            'line_count': content.count('\n') + 1
        }
    except Exception as e:
        print(f"[Parser] Error reading {filepath}: {e}")
        return None


def parse_directory(root_dir: str) -> list[dict]:
    """
    Walk a directory and parse all supported files.
    Returns list of parsed file dicts.
    """
    parsed_files = []

    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Prune ignored directories in-place (modifies walk)
        dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS]

        for filename in filenames:
            full_path = os.path.join(dirpath, filename)
            result = parse_file(full_path)
            if result:
                # Store relative path for cleaner display
                result['relative_path'] = os.path.relpath(full_path, root_dir)
                parsed_files.append(result)

    print(f"[Parser] Parsed {len(parsed_files)} files from {root_dir}")
    return parsed_files
