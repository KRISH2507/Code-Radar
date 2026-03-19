"""
Static Code Analyzer

Scans files for code quality issues without an AST.
Uses regex + line-counting heuristics valid across all languages.

Rules implemented:
  CRITICAL  hardcoded_secret   – password/key/token = "literal"
  HIGH      long_file          – >1000 lines
  HIGH      empty_catch        – bare except / catch() {}
  MEDIUM    long_file          – 501-1000 lines
  MEDIUM    deep_nesting       – indentation depth >6
  MEDIUM    high_complexity    – high branch-keyword density
  LOW       long_function      – function body >80 lines
  LOW       debug_code         – leftover print / console.log / debugger
  INFO      todo_comment       – TODO / FIXME / HACK
"""

import os
import re
from typing import List, Dict, Optional
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class CodeIssue:
    severity: str       # critical / high / medium / low / info
    issue_type: str
    file_path: str
    line_number: Optional[int]
    message: str
    rule: str


@dataclass
class FileAnalysisResult:
    file_path: str
    language: str
    total_lines: int
    code_lines: int
    blank_lines: int
    comment_lines: int
    complexity_score: float
    issues: List[CodeIssue] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Compiled patterns (compiled once at import time)
# ---------------------------------------------------------------------------

_RE_SECRET = re.compile(
    r'(?i)(password|passwd|pwd|secret|api_?key|auth_?token|access_?token|'
    r'private_?key|client_?secret)\s*=\s*["\'][^"\']{4,}["\']'
)
_RE_EMPTY_EXCEPT_PY   = re.compile(r'^\s*except\s*[:\(]?\s*$|^\s*except\s+\w+\s*:\s*pass\s*$')
_RE_EMPTY_CATCH_JS    = re.compile(r'catch\s*\([^)]*\)\s*\{\s*\}')
_RE_DEBUG_PY          = re.compile(r'^\s*(print|pprint)\s*\(')
_RE_DEBUG_JS          = re.compile(r'^\s*console\.(log|warn|error|debug|info)\s*\(|^\s*debugger\s*;?$')
_RE_TODO              = re.compile(r'#|//|/\*|\*').pattern   # start of comment token
_RE_TODO_CONTENT      = re.compile(r'\b(TODO|FIXME|HACK|XXX|BUG|WORKAROUND)\b')
_RE_BRANCH_KEYWORDS   = re.compile(r'\b(if|elif|else|for|while|switch|case|catch|except|and|or|&&|\|\|)\b')

_COMMENT_PREFIXES = ('#', '//', '*', '/*', '"""', "'''")

_BINARY_EXTS = {
    '.pyc', '.pyo', '.pyd', '.so', '.dll', '.dylib', '.exe', '.bin',
    '.jpg', '.jpeg', '.png', '.gif', '.svg', '.ico', '.webp', '.pdf',
    '.zip', '.tar', '.gz', '.rar', '.7z', '.mp4', '.mp3', '.wav',
    '.woff', '.woff2', '.ttf', '.eot', '.otf', '.class', '.jar',
}
_EXCLUDED_DIRS = {
    '.git', 'node_modules', '__pycache__', '.next', 'dist', 'build',
    'venv', '.venv', 'env', 'target', 'bin', 'obj', '.idea', '.vscode',
    'coverage', '.pytest_cache', '.mypy_cache',
}

_LANG_MAP = {
    '.py': 'Python', '.js': 'JavaScript', '.jsx': 'JavaScript',
    '.ts': 'TypeScript', '.tsx': 'TypeScript', '.java': 'Java',
    '.cs': 'C#', '.cpp': 'C++', '.c': 'C', '.go': 'Go',
    '.rs': 'Rust', '.rb': 'Ruby', '.php': 'PHP', '.swift': 'Swift',
    '.kt': 'Kotlin', '.scala': 'Scala', '.sh': 'Shell',
    '.sql': 'SQL', '.html': 'HTML', '.css': 'CSS', '.scss': 'SCSS',
    '.json': 'JSON', '.yaml': 'YAML', '.yml': 'YAML', '.md': 'Markdown',
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def analyze_repository(repo_path: str) -> Dict:
    """
    Walk the repository and analyse every code file.

    Returns
    -------
    {
        "total_files": int,
        "total_lines": int,
        "language_stats": {lang: {"files": int, "lines": int}},
        "file_results": [FileAnalysisResult, ...],
        "all_issues": [CodeIssue, ...],
    }
    """
    file_results: List[FileAnalysisResult] = []
    all_issues: List[CodeIssue] = []
    language_stats: Dict[str, Dict] = {}

    for root, dirs, files in os.walk(repo_path):
        # Prune excluded directories in-place
        dirs[:] = [d for d in dirs if d not in _EXCLUDED_DIRS]

        for filename in files:
            ext = os.path.splitext(filename)[1].lower()
            if ext in _BINARY_EXTS:
                continue

            full_path = os.path.join(root, filename)
            rel_path  = os.path.relpath(full_path, repo_path)
            language  = _LANG_MAP.get(ext, 'Other')

            try:
                result = _analyze_file(full_path, rel_path, language)
            except Exception as exc:
                logger.warning("Could not analyse %s: %s", rel_path, exc)
                continue

            file_results.append(result)
            all_issues.extend(result.issues)

            stats = language_stats.setdefault(language, {"files": 0, "lines": 0})
            stats["files"] += 1
            stats["lines"] += result.total_lines

    total_files = len(file_results)
    total_lines = sum(r.total_lines for r in file_results)

    return {
        "total_files": total_files,
        "total_lines": total_lines,
        "language_stats": language_stats,
        "file_results": file_results,
        "all_issues": all_issues,
    }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _analyze_file(full_path: str, rel_path: str, language: str) -> FileAnalysisResult:
    try:
        with open(full_path, "r", encoding="utf-8", errors="ignore") as fh:
            raw_lines = fh.readlines()
    except OSError:
        raw_lines = []

    total_lines   = len(raw_lines)
    blank_lines   = sum(1 for ln in raw_lines if ln.strip() == "")
    comment_lines = sum(1 for ln in raw_lines if ln.strip().startswith(_COMMENT_PREFIXES))
    code_lines    = total_lines - blank_lines - comment_lines

    complexity_score, nesting_issues = _complexity(raw_lines, rel_path)
    issues: List[CodeIssue] = []

    # --- long file ---
    if total_lines > 1000:
        issues.append(CodeIssue(
            severity="high", issue_type="long_file",
            file_path=rel_path, line_number=None,
            message=f"File has {total_lines} lines (threshold: 1000).",
            rule="CR001",
        ))
    elif total_lines > 500:
        issues.append(CodeIssue(
            severity="medium", issue_type="long_file",
            file_path=rel_path, line_number=None,
            message=f"File has {total_lines} lines (threshold: 500).",
            rule="CR001",
        ))

    issues.extend(nesting_issues)

    # --- per-line rules ---
    func_start_line: Optional[int] = None
    func_start_indent: int = 0
    func_body_lines: int = 0

    for lineno, raw in enumerate(raw_lines, start=1):
        line = raw.rstrip("\n")
        stripped = line.lstrip()

        # skip blank
        if not stripped:
            continue

        # --- hardcoded secrets ---
        if _RE_SECRET.search(line):
            issues.append(CodeIssue(
                severity="critical", issue_type="hardcoded_secret",
                file_path=rel_path, line_number=lineno,
                message="Possible hardcoded credential detected.",
                rule="CR002",
            ))

        # --- empty catch / except ---
        if _RE_EMPTY_EXCEPT_PY.match(line) or _RE_EMPTY_CATCH_JS.search(line):
            issues.append(CodeIssue(
                severity="high", issue_type="empty_catch",
                file_path=rel_path, line_number=lineno,
                message="Empty exception handler swallows errors silently.",
                rule="CR003",
            ))

        # --- debug code ---
        if _RE_DEBUG_PY.match(line) or _RE_DEBUG_JS.match(line):
            issues.append(CodeIssue(
                severity="low", issue_type="debug_code",
                file_path=rel_path, line_number=lineno,
                message="Debug statement left in production code.",
                rule="CR004",
            ))

        # --- TODO / FIXME ---
        if _RE_TODO_CONTENT.search(line):
            issues.append(CodeIssue(
                severity="info", issue_type="todo_comment",
                file_path=rel_path, line_number=lineno,
                message=f"Unresolved annotation: {stripped[:80]}",
                rule="CR005",
            ))

        # --- long function heuristic ---
        is_func_def = _is_function_definition(stripped)
        if is_func_def:
            if func_start_line is not None and func_body_lines > 80:
                issues.append(CodeIssue(
                    severity="low", issue_type="long_function",
                    file_path=rel_path, line_number=func_start_line,
                    message=f"Function body is ~{func_body_lines} lines long (threshold: 80).",
                    rule="CR006",
                ))
            func_start_line  = lineno
            func_start_indent = len(line) - len(stripped)
            func_body_lines  = 0
        elif func_start_line is not None:
            current_indent = len(line) - len(stripped)
            if current_indent <= func_start_indent and stripped not in ("", "#"):
                # function ended
                if func_body_lines > 80:
                    issues.append(CodeIssue(
                        severity="low", issue_type="long_function",
                        file_path=rel_path, line_number=func_start_line,
                        message=f"Function body is ~{func_body_lines} lines long (threshold: 80).",
                        rule="CR006",
                    ))
                func_start_line = None
                func_body_lines = 0
            else:
                func_body_lines += 1

    return FileAnalysisResult(
        file_path=rel_path,
        language=language,
        total_lines=total_lines,
        code_lines=code_lines,
        blank_lines=blank_lines,
        comment_lines=comment_lines,
        complexity_score=complexity_score,
        issues=issues,
    )


def _complexity(lines: List[str], rel_path: str):
    """
    Return (complexity_score, [CodeIssue]).
    complexity_score = average branch-keyword density per 10 lines.
    Also detects deep nesting (indent level > 6).
    """
    branch_count = 0
    max_depth    = 0
    nesting_issues: List[CodeIssue] = []
    warned_nesting = False

    for lineno, raw in enumerate(lines, start=1):
        stripped = raw.lstrip()
        if not stripped:
            continue

        indent_level = (len(raw) - len(stripped)) // 4   # assume 4-space indent

        if indent_level > max_depth:
            max_depth = indent_level

        if indent_level > 6 and not warned_nesting:
            nesting_issues.append(CodeIssue(
                severity="medium", issue_type="deep_nesting",
                file_path=rel_path, line_number=lineno,
                message=f"Code nesting depth exceeds 6 levels.",
                rule="CR007",
            ))
            warned_nesting = True

        branch_count += len(_RE_BRANCH_KEYWORDS.findall(raw))

    total = len(lines) or 1
    score = round((branch_count / total) * 10, 2)   # branches per 10 lines

    if score > 4 and total > 50:
        nesting_issues.append(CodeIssue(
            severity="medium", issue_type="high_complexity",
            file_path=rel_path, line_number=None,
            message=f"High branch density ({score:.1f} branches/10 lines).",
            rule="CR008",
        ))

    return score, nesting_issues


def _is_function_definition(stripped: str) -> bool:
    """Detect function/method definitions across common languages."""
    return bool(
        re.match(r'^(async\s+)?def\s+\w+', stripped)           # Python
        or re.match(r'^(async\s+)?function\s+\w+', stripped)   # JS/TS
        or re.match(r'^(public|private|protected|static|async|\s)+'
                    r'(\w+\s+)?\w+\s*\(', stripped)            # Java/C#/Go
    )
