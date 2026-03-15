"""
services/chunker.py
Smart code chunker - splits large files into overlapping chunks
for better semantic search coverage.

Strategy:
  - Try to split on natural code boundaries (class/function definitions)
  - Fall back to line-based sliding window with overlap
  - Each chunk preserves file metadata for traceability
"""

import re

CHUNK_SIZE = 80        # lines per chunk
CHUNK_OVERLAP = 15     # lines of overlap between chunks


# Regex patterns for natural split points per language
SPLIT_PATTERNS = {
    'python': re.compile(r'^(class |def )', re.MULTILINE),
    'javascript': re.compile(r'^(class |function |const .+ = \(|export )', re.MULTILINE),
    'typescript': re.compile(r'^(class |function |interface |type |export )', re.MULTILINE),
    'java': re.compile(r'^(public |private |protected |class )', re.MULTILINE),
    'go': re.compile(r'^(func |type |var |const )', re.MULTILINE),
    'rust': re.compile(r'^(fn |impl |struct |enum |trait )', re.MULTILINE),
}


def _sliding_window_chunks(lines: list[str], file_meta: dict) -> list[dict]:
    """Fallback: split by fixed-size sliding window."""
    chunks = []
    total = len(lines)
    start = 0
    chunk_index = 0

    while start < total:
        end = min(start + CHUNK_SIZE, total)
        chunk_text = '\n'.join(lines[start:end])

        chunks.append({
            **file_meta,
            'chunk_index': chunk_index,
            'chunk_text': chunk_text,
            'start_line': start + 1,
            'end_line': end,
            'chunk_id': f"{file_meta['relative_path']}::chunk_{chunk_index}"
        })

        chunk_index += 1
        start += CHUNK_SIZE - CHUNK_OVERLAP  # slide with overlap

    return chunks


def _semantic_chunks(content: str, pattern: re.Pattern, file_meta: dict) -> list[dict]:
    """Split at language-specific boundaries (functions/classes)."""
    splits = list(pattern.finditer(content))
    if len(splits) < 2:
        return []  # Not enough splits, fall back

    chunks = []
    for i, match in enumerate(splits):
        start = match.start()
        end = splits[i + 1].start() if i + 1 < len(splits) else len(content)
        chunk_text = content[start:end].strip()

        if len(chunk_text) < 30:  # skip tiny fragments
            continue

        chunks.append({
            **file_meta,
            'chunk_index': i,
            'chunk_text': chunk_text,
            'start_line': content[:start].count('\n') + 1,
            'end_line': content[:end].count('\n') + 1,
            'chunk_id': f"{file_meta['relative_path']}::semantic_{i}"
        })

    return chunks


def chunk_file(file_data: dict) -> list[dict]:
    """
    Chunk a single parsed file.
    Tries semantic splitting first, falls back to sliding window.
    """
    content = file_data['content']
    language = file_data['language']

    # Build safe metadata (exclude raw content to avoid duplication)
    file_meta = {k: v for k, v in file_data.items() if k != 'content'}

    lines = content.split('\n')

    # If file is small enough, treat as single chunk
    if len(lines) <= CHUNK_SIZE:
        return [{
            **file_meta,
            'chunk_index': 0,
            'chunk_text': content,
            'start_line': 1,
            'end_line': len(lines),
            'chunk_id': f"{file_meta['relative_path']}::chunk_0"
        }]

    # Try semantic splitting if we have a pattern for this language
    if language in SPLIT_PATTERNS:
        semantic = _semantic_chunks(content, SPLIT_PATTERNS[language], file_meta)
        if semantic:
            return semantic

    # Fallback: sliding window
    return _sliding_window_chunks(lines, file_meta)


def chunk_all_files(parsed_files: list[dict]) -> list[dict]:
    """Chunk all parsed files and return flat list of chunks."""
    all_chunks = []
    for file_data in parsed_files:
        chunks = chunk_file(file_data)
        all_chunks.extend(chunks)

    print(f"[Chunker] Created {len(all_chunks)} chunks from {len(parsed_files)} files")
    return all_chunks
