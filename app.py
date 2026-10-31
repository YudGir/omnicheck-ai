"""
OmniCheck AI — Multi-Language & Database Practical Evaluation Agent
====================================================================
Rule-based static analysis engine. No external API required.
Supports: Python · C++ · Java · PHP · SQL
"""

import re
import os
import json
import textwrap
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import streamlit as st

# ──────────────────────────────────────────────────────────────────────────────
# Page config
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="OmniCheck AI",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────────────────────────────────────
# Styles
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
html, body, [class*="css"] { font-family: 'Segoe UI', system-ui, sans-serif; }
.block-container { padding-top: 1.4rem; }

.omni-header {
    background: #0d1b2a;
    border: 1px solid #2d3748;
    border-radius: 12px;
    padding: 26px 32px;
    margin-bottom: 20px;
    text-align: center;
}
.omni-header h1 { color: #63b3ed; font-size: 2rem; margin: 0 0 6px; }
.omni-header p  { color: #a0aec0; font-size: 0.9rem; margin: 0; }

.score-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 10px; margin: 16px 0;
}
.score-card {
    background: #1a202c; border: 1px solid #2d3748;
    border-radius: 10px; padding: 14px; text-align: center;
}
.score-card .lbl { color:#a0aec0; font-size:.72rem; text-transform:uppercase; letter-spacing:.06em; margin-bottom:6px; }
.score-card .val { font-size:1.9rem; font-weight:700; line-height:1; }
.val.excellent { color:#68d391; }
.val.good      { color:#63b3ed; }
.val.fair      { color:#f6e05e; }
.val.poor      { color:#fc8181; }

.info-box  { background:#1a2744; border:1px solid #2b4fa0; border-radius:8px; padding:12px 16px; color:#90cdf4; font-size:.87rem; margin:10px 0; }
.warn-box  { background:#2d1f00; border:1px solid #d69e2e; border-radius:8px; padding:12px 16px; color:#f6e05e; font-size:.87rem; margin:10px 0; }
.err-box   { background:#2d1515; border:1px solid #e53e3e; border-radius:8px; padding:12px 16px; color:#fc8181; font-size:.87rem; margin:10px 0; }
.ok-box    { background:#1a2d1a; border:1px solid #38a169; border-radius:8px; padding:12px 16px; color:#68d391; font-size:.87rem; margin:10px 0; }

.sec-title { color:#63b3ed; font-size:.95rem; font-weight:600; border-left:3px solid #63b3ed; padding-left:9px; margin:18px 0 8px; }
.badge { display:inline-block; border-radius:4px; padding:1px 8px; font-size:.72rem; font-weight:600; text-transform:uppercase; }
.badge.critical { background:#2d1515; color:#fc8181; }
.badge.high     { background:#2d1a00; color:#f6ad55; }
.badge.medium   { background:#2d2700; color:#f6e05e; }
.badge.low      { background:#1a2744; color:#90cdf4; }
.badge.warning  { background:#2d2700; color:#f6e05e; }
.badge.info     { background:#1a2744; color:#90cdf4; }

.lang-pill {
    display:inline-block; border-radius:6px; padding:3px 14px;
    font-size:.78rem; font-weight:700; letter-spacing:.05em; margin-bottom:6px;
}
.lang-pill.python { background:#2d5016; color:#9ae6b4; }
.lang-pill.cpp    { background:#3c2369; color:#d6bcfa; }
.lang-pill.java   { background:#744210; color:#fbd38d; }
.lang-pill.php    { background:#1e3a5f; color:#90cdf4; }
.lang-pill.sql    { background:#1a3a2a; color:#68d391; }

.footer { text-align:center; color:#4a5568; font-size:.76rem; margin-top:36px; padding-top:14px; border-top:1px solid #2d3748; }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# Data structures
# ──────────────────────────────────────────────────────────────────────────────

@dataclass
class Issue:
    severity: str          # critical | high | medium | low | warning | info
    category: str          # Logic | Syntax | Performance | Security | Readability
    message: str
    line: Optional[int] = None
    hint: str = ""
    question: str = ""


@dataclass
class EvalReport:
    language: str
    logic_score: int = 0
    syntax_score: int = 0
    performance_score: int = 0
    security_score: int = 0
    readability_score: int = 0
    overall_score: int = 0
    issues: list = field(default_factory=list)
    strengths: list = field(default_factory=list)
    complexity_estimate: str = "N/A"
    summary: str = ""
    study_topics: list = field(default_factory=list)


# ──────────────────────────────────────────────────────────────────────────────
# Language detector
# ──────────────────────────────────────────────────────────────────────────────

LANG_KEYWORDS: dict[str, list[str]] = {
    "Python": ["def ", "import ", "from ", "class ", "elif ", "print(", "lambda ",
               "__init__", "if __name__", "self.", "None", "True", "False"],
    "C++":    ["#include", "std::", "cout", "cin", "int main(", "nullptr",
               "vector<", "->", "::", "endl", "#define", "template<"],
    "Java":   ["public class", "public static void main", "System.out",
               "import java.", "extends ", "implements ", "@Override", "new "],
    "PHP":    ["<?php", "echo ", "$_GET", "$_POST", "$_SESSION", "namespace ",
               "use \\", "->", "array(", "function "],
    "SQL":    ["SELECT ", "INSERT ", "UPDATE ", "DELETE ", "CREATE TABLE",
               "DROP ", "ALTER ", "JOIN ", "WHERE ", "GROUP BY",
               "ORDER BY", "HAVING ", "INDEX ", "TRIGGER"],
}

EXT_MAP: dict[str, str] = {
    ".py": "Python", ".cpp": "C++", ".cc": "C++", ".cxx": "C++",
    ".h": "C++", ".hpp": "C++", ".java": "Java",
    ".php": "PHP", ".sql": "SQL",
}


def detect_language(code: str, filename: str = "") -> str:
    if filename:
        ext = os.path.splitext(filename)[1].lower()
        if ext in EXT_MAP:
            return EXT_MAP[ext]

    upper = code.upper()
    scores = {lang: sum(1 for kw in kws if kw.upper() in upper)
              for lang, kws in LANG_KEYWORDS.items()}
    best = max(scores, key=lambda lang: scores[lang])
    if scores[best] > 0:
        return best
    return "Python"


# ──────────────────────────────────────────────────────────────────────────────
# Helper: find line number of a pattern
# ──────────────────────────────────────────────────────────────────────────────

def find_line(code: str, pattern: str, flags: int = 0) -> Optional[int]:
    for i, line in enumerate(code.splitlines(), 1):
        if re.search(pattern, line, flags):
            return i
    return None


def find_all_lines(code: str, pattern: str, flags: int = 0) -> list[int]:
    return [i for i, ln in enumerate(code.splitlines(), 1)
            if re.search(pattern, ln, flags)]


# ──────────────────────────────────────────────────────────────────────────────
# Score helpers
# ──────────────────────────────────────────────────────────────────────────────

def _deduct(base: int, issues: list[Issue], category: str) -> int:
    """Deduct points per severity for a given category."""
    deduct_map = {"critical": 25, "high": 15, "medium": 8, "low": 4,
                  "warning": 5, "info": 1}
    total = sum(deduct_map.get(i.severity, 0)
                for i in issues if i.category == category)
    return max(0, base - total)


def score_class(v: int) -> str:
    if v >= 85: return "excellent"
    if v >= 65: return "good"
    if v >= 45: return "fair"
    return "poor"


# ──────────────────────────────────────────────────────────────────────────────
# ── PYTHON ANALYZER ──────────────────────────────────────────────────────────
# ──────────────────────────────────────────────────────────────────────────────

def analyze_python(code: str) -> EvalReport:
    issues: list[Issue] = []
    strengths: list[str] = []
    topics: list[str] = []
    lines = code.splitlines()

    # ── Logic ────────────────────────────────────────────────────────────────
    # Mutable default argument
    for ln in find_all_lines(code, r'def\s+\w+\s*\(.*=\s*(\[\]|\{\}|\(\))'):
        issues.append(Issue("high", "Logic",
            "Mutable default argument detected. Default mutable objects are shared across all calls.",
            ln,
            hint="Python evaluates default arguments once at function definition time, not at call time.",
            question="What happens to the default list if you call this function twice without arguments?"))

    # bare except
    for ln in find_all_lines(code, r'^\s*except\s*:'):
        issues.append(Issue("medium", "Logic",
            "Bare `except:` catches all exceptions including SystemExit and KeyboardInterrupt.",
            ln,
            hint="Catch the most specific exception class you expect.",
            question="Which exception types are you actually trying to handle here?"))

    # == None instead of `is None`
    for ln in find_all_lines(code, r'==\s*None|!=\s*None'):
        issues.append(Issue("warning", "Logic",
            "Use `is None` / `is not None` for identity comparison, not `==`.",
            ln,
            hint="`None` is a singleton; identity check (`is`) is correct and faster.",
            question="What is the difference between equality (`==`) and identity (`is`) in Python?"))

    # global variable mutation
    for ln in find_all_lines(code, r'^\s*global\s+\w+'):
        issues.append(Issue("medium", "Logic",
            "Global variable used. This creates hidden state and makes functions hard to test.",
            ln,
            hint="Consider passing the value as a parameter and returning a new value.",
            question="How would you refactor this function to avoid relying on a global variable?"))

    # ── Syntax / Style ───────────────────────────────────────────────────────
    # Lines > 79 chars
    long_lines = [i+1 for i, ln in enumerate(lines) if len(ln) > 79]
    if long_lines:
        issues.append(Issue("info", "Syntax",
            f"PEP 8: {len(long_lines)} line(s) exceed 79 characters (lines {long_lines[:5]}).",
            long_lines[0],
            hint="PEP 8 recommends 79 chars for code, 72 for docstrings.",
            question="Which lines could be broken with a logical continuation or reformatted?"))

    # Missing docstrings on functions
    func_lines = find_all_lines(code, r'^\s*def\s+\w+')
    no_doc_count = 0
    for fl in func_lines:
        found_doc = False
        for nxt in lines[fl:fl+3]:
            if '"""' in nxt or "'''" in nxt:
                found_doc = True
                break
        if not found_doc:
            no_doc_count += 1
    if no_doc_count:
        issues.append(Issue("info", "Readability",
            f"{no_doc_count} function(s) lack docstrings.",
            hint="A good docstring describes what the function does, its parameters, and return value.",
            question="How would you document this function so a colleague could use it without reading the body?"))

    # print() statements (debug artifacts)
    print_lines = find_all_lines(code, r'^\s*print\s*\(')
    if print_lines:
        issues.append(Issue("info", "Readability",
            f"Found {len(print_lines)} `print()` statement(s). Consider using the `logging` module in production code.",
            print_lines[0],
            hint="The `logging` module supports severity levels and can be silenced in production.",
            question="What log level would be appropriate for each of these print statements?"))

    # ── Performance ──────────────────────────────────────────────────────────
    # O(n) lookup in list when set would be better
    for ln in find_all_lines(code, r'\bif\s+\w+\s+in\s+\w+\b'):
        ctx = lines[ln-1].strip()
        if not re.search(r'in\s+\[|in\s+\(', ctx):  # skip list/tuple literals
            issues.append(Issue("medium", "Performance",
                "Membership test (`in`) on a list is O(n). A `set` lookup is O(1).",
                ln,
                hint="If the collection is iterated only for membership checks, a `set` is more efficient.",
                question="What would happen to the runtime if the list had 1 000 000 elements?"))
            break  # report once

    # Nested loops
    nest = re.search(r'for\s+.*:\s*\n(?:\s+.*\n)*?\s+for\s+', code)
    if nest:
        ln = code[:nest.start()].count('\n') + 1
        issues.append(Issue("medium", "Performance",
            "Nested loop detected — possible O(n²) complexity.",
            ln,
            hint="Consider whether an index structure, sort-and-scan, or set can reduce the inner loop.",
            question="Is it possible to achieve the same result with a single pass?"))

    # String concatenation in loop
    for ln in find_all_lines(code, r'\+=\s*["\']|\+=\s*\w+.*str'):
        issues.append(Issue("medium", "Performance",
            "String concatenation with `+=` inside a loop creates O(n²) copies. Use `str.join()` or a list buffer.",
            ln,
            hint="Strings are immutable in Python; every `+=` allocates a new string.",
            question="How could you collect the parts in a list and join them at the end?"))

    # ── Security ─────────────────────────────────────────────────────────────
    # eval / exec
    for pat in [r'\beval\s*\(', r'\bexec\s*\(']:
        ln = find_line(code, pat)
        if ln:
            issues.append(Issue("critical", "Security",
                "`eval()`/`exec()` with untrusted input allows arbitrary code execution.",
                ln,
                hint="If you need dynamic behaviour, use a safe parser or a restricted DSL.",
                question="Can the input to `eval()` be controlled by a user or external source?"))

    # subprocess with shell=True
    ln = find_line(code, r'subprocess.*shell\s*=\s*True')
    if ln:
        issues.append(Issue("high", "Security",
            "`subprocess` with `shell=True` is vulnerable to shell injection.",
            ln,
            hint="Pass a list of arguments and use `shell=False`.",
            question="What if a user-controlled string is part of the command?"))

    # ── Strengths ─────────────────────────────────────────────────────────────
    if re.search(r'^\s*from\s+__future__\s+import', code, re.MULTILINE):
        strengths.append("Uses `from __future__ import` — good forward compatibility practice.")
    if re.search(r'with\s+open\s*\(', code):
        strengths.append("Uses context manager (`with open(...)`) — ensures file handles are closed.")
    if re.search(r'^\s*def\s+\w+.*->.*:', code, re.MULTILINE):
        strengths.append("Type hints present on at least one function — aids IDE support and readability.")
    if re.search(r'if\s+__name__\s*==\s*["\']__main__["\']', code):
        strengths.append("Uses `if __name__ == '__main__'` guard — correct module structure.")
    if re.search(r'@\w+', code):
        strengths.append("Decorators used — good use of Python's higher-order function features.")
    if not strengths:
        strengths.append("Code is syntactically valid Python.")

    topics = ["Python PEP 8 style guide", "Python exception handling best practices",
              "Time complexity and Big-O notation", "Python logging module",
              "Mutable vs immutable default arguments"]

    # Complexity estimate
    complexity = "O(n²)" if any(i.message.startswith("Nested loop") for i in issues) else "O(n)"

    report = EvalReport(language="Python", complexity_estimate=complexity,
                        issues=issues, strengths=strengths, study_topics=topics)
    report.logic_score       = _deduct(95, issues, "Logic")
    report.syntax_score      = _deduct(90, issues, "Syntax")
    report.performance_score = _deduct(90, issues, "Performance")
    report.security_score    = _deduct(100, issues, "Security")
    report.readability_score = _deduct(90, issues, "Readability")
    report.overall_score     = int((report.logic_score + report.syntax_score +
                                    report.performance_score + report.security_score +
                                    report.readability_score) / 5)
    report.summary = _make_summary(report)
    return report


# ──────────────────────────────────────────────────────────────────────────────
# ── SQL ANALYZER ─────────────────────────────────────────────────────────────
# ──────────────────────────────────────────────────────────────────────────────

def analyze_sql(code: str) -> EvalReport:
    issues: list[Issue] = []
    strengths: list[str] = []
    upper = code.upper()

    # ── Performance ──────────────────────────────────────────────────────────
    # SELECT *
    if re.search(r'SELECT\s+\*', upper):
        ln = find_line(code, r'SELECT\s+\*', re.IGNORECASE)
        issues.append(Issue("high", "Performance",
            "`SELECT *` fetches all columns — risk of over-fetching and index skip.",
            ln,
            hint="Specify only the columns you need to reduce I/O and enable covering indexes.",
            question="Which exact columns does your application actually consume?"))

    # No WHERE clause on SELECT/UPDATE/DELETE
    stmts = re.findall(r'(SELECT|UPDATE|DELETE)[^\n;]+', code, re.IGNORECASE)
    for stmt in stmts:
        if not re.search(r'\bWHERE\b', stmt, re.IGNORECASE):
            issues.append(Issue("high", "Performance",
                f"`{stmt.split()[0].upper()}` statement without a WHERE clause — full table scan.",
                hint="A missing WHERE clause on a large table is catastrophic for performance.",
                question="Under what condition should this statement apply? Can you add a WHERE clause?"))

    # LIKE with leading wildcard
    for ln in find_all_lines(code, r"LIKE\s+'%", re.IGNORECASE):
        issues.append(Issue("medium", "Performance",
            "Leading wildcard in LIKE (`'%…'`) prevents index usage — full table scan.",
            ln,
            hint="A leading `%` forces the engine to scan every row.",
            question="Can you redesign the search to use a full-text index or avoid the leading wildcard?"))

    # Excessive JOINs (> 3)
    join_count = len(re.findall(r'\bJOIN\b', upper))
    if join_count > 3:
        issues.append(Issue("medium", "Performance",
            f"Query contains {join_count} JOINs — verify that all are necessary and indexed.",
            hint="Each JOIN multiplies the row set; ensure foreign key columns are indexed.",
            question="Can any of these JOINs be eliminated by denormalizing or using a subquery?"))
    elif join_count > 0:
        strengths.append(f"Uses {join_count} JOIN(s) — verify indexes on join columns.")

    # Subquery in WHERE (correlated)
    if re.search(r'WHERE\s+\w+\s+IN\s*\(\s*SELECT', upper):
        ln = find_line(code, r'WHERE\s+\w+\s+IN\s*\(\s*SELECT', re.IGNORECASE)
        issues.append(Issue("medium", "Performance",
            "Correlated subquery in WHERE … IN (SELECT …) may execute once per row.",
            ln,
            hint="A JOIN or EXISTS is often more efficient than IN (SELECT …).",
            question="Could this be rewritten as a JOIN to let the optimizer choose a better plan?"))

    # ORDER BY on non-indexed columns (heuristic: general warning)
    if re.search(r'ORDER\s+BY', upper) and not re.search(r'(INDEX|KEY)', upper):
        issues.append(Issue("low", "Performance",
            "ORDER BY present — ensure the sort column is indexed to avoid filesort.",
            hint="An index on the ORDER BY column lets the engine skip the sort step.",
            question="Is there an index on the column(s) in your ORDER BY clause?"))

    # ── Security ─────────────────────────────────────────────────────────────
    # Dynamic concatenation (common SQL injection pattern in templates)
    for pat in [r"'\s*\+\s*@?\w+", r"'\s*\|\|\s*\w+", r"CONCAT\s*\(\s*['\"].*\bwhere\b",
                r"N?'%'\s*\+\s*@"]:
        ln = find_line(code, pat, re.IGNORECASE)
        if ln:
            issues.append(Issue("critical", "Security",
                "Possible SQL injection via string concatenation in dynamic query.",
                ln,
                hint="Use parameterized queries / prepared statements — never concatenate user input.",
                question="Where does the concatenated value originate? Can a user influence it?"))
            break

    # Stored password / secret hint
    if re.search(r"password\s*=\s*'[^']+'", code, re.IGNORECASE):
        ln = find_line(code, r"password\s*=\s*'", re.IGNORECASE)
        issues.append(Issue("critical", "Security",
            "Hard-coded password literal detected in SQL.",
            ln,
            hint="Never store plain-text passwords. Use bcrypt/argon2 hashes.",
            question="How would you store and verify a password without keeping it in plain text?"))

    # ── Syntax / Style ───────────────────────────────────────────────────────
    if not re.search(r';\s*$', code.strip()):
        issues.append(Issue("info", "Syntax",
            "Query does not end with a semicolon — required by many SQL clients.",
            hint="Add `;` at the end of each statement.",
            question="Does your target database require explicit statement terminators?"))

    if re.search(r'\bselect\b|\bwhere\b|\bfrom\b', code):  # lowercase keywords
        issues.append(Issue("info", "Readability",
            "SQL keywords in lowercase — convention prefers UPPERCASE for keywords.",
            hint="Capitalize SQL keywords (SELECT, FROM, WHERE…) for readability.",
            question="Does your team have a SQL style guide?"))

    # ── Strengths ─────────────────────────────────────────────────────────────
    if re.search(r'\bEXISTS\b', upper):
        strengths.append("Uses EXISTS — often more efficient than IN for existence checks.")
    if re.search(r'\bINDEX\b|\bCREATE\s+INDEX\b', upper):
        strengths.append("Index definition present — good for query planning.")
    if re.search(r'\bTRANSACTION\b|\bBEGIN\b.*\bCOMMIT\b', upper, re.DOTALL):
        strengths.append("Explicit transaction used — protects data consistency.")
    if not strengths:
        strengths.append("Query is syntactically recognizable SQL.")

    topics = ["SQL query optimization and execution plans", "Indexes: B-Tree vs Hash",
              "Parameterized queries and SQL injection prevention",
              "EXPLAIN / EXPLAIN ANALYZE usage", "JOIN types and when to use each"]

    report = EvalReport(language="SQL", complexity_estimate=f"{join_count} JOIN(s)",
                        issues=issues, strengths=strengths, study_topics=topics)
    report.logic_score       = _deduct(95, issues, "Logic")
    report.syntax_score      = _deduct(90, issues, "Syntax")
    report.performance_score = _deduct(95, issues, "Performance")
    report.security_score    = _deduct(100, issues, "Security")
    report.readability_score = _deduct(90, issues, "Readability")
    report.overall_score     = int((report.logic_score + report.syntax_score +
                                    report.performance_score + report.security_score +
                                    report.readability_score) / 5)
    report.summary = _make_summary(report)
    return report


# ──────────────────────────────────────────────────────────────────────────────
# ── C++ ANALYZER ─────────────────────────────────────────────────────────────
# ──────────────────────────────────────────────────────────────────────────────

def analyze_cpp(code: str) -> EvalReport:
    issues: list[Issue] = []
    strengths: list[str] = []

    # Memory leaks
    new_count = len(re.findall(r'\bnew\b', code))
    del_count = len(re.findall(r'\bdelete\b', code))
    if new_count > del_count:
        issues.append(Issue("critical", "Security",
            f"`new` used {new_count}× but `delete` only {del_count}× — potential memory leak.",
            find_line(code, r'\bnew\b'),
            hint="Prefer `std::unique_ptr` or `std::shared_ptr` over raw `new`/`delete`.",
            question="For each `new` expression, where is the corresponding `delete`?"))

    # Raw pointer return
    if re.search(r'\w+\s*\*\s+\w+\s*\(', code):
        issues.append(Issue("high", "Security",
            "Function returning a raw pointer — ownership semantics are unclear.",
            find_line(code, r'\w+\s*\*\s+\w+\s*\('),
            hint="Return a smart pointer (`unique_ptr<T>`) to make ownership explicit.",
            question="Who is responsible for deleting the returned object?"))

    # Missing virtual destructor
    if re.search(r'class\s+\w+', code) and not re.search(r'virtual\s+~', code):
        if re.search(r'virtual\s+\w+', code):  # has virtual methods but no virtual dtor
            issues.append(Issue("high", "Logic",
                "Class has virtual methods but no virtual destructor — undefined behaviour on polymorphic delete.",
                find_line(code, r'class\s+\w+'),
                hint="Any class with virtual methods should declare `virtual ~ClassName() = default;`.",
                question="What happens when you `delete` a derived object through a base pointer without a virtual destructor?"))

    # printf with user data (format string vuln)
    ln = find_line(code, r'printf\s*\(\s*\w+')
    if ln:
        issues.append(Issue("high", "Security",
            "Possible format-string vulnerability: `printf(variable)` — always use `printf(\"%s\", var)`.",
            ln,
            hint="A user-controlled format string can read/write arbitrary memory.",
            question="Is the first argument to `printf` a string literal or a variable?"))

    # Nested loops
    if re.search(r'for\s*\(.*\)\s*\{[^}]*for\s*\(', code, re.DOTALL):
        issues.append(Issue("medium", "Performance",
            "Nested loops detected — verify O(n²) complexity is acceptable.",
            find_line(code, r'for\s*\('),
            hint="Consider hash maps or sorting to reduce inner loop iterations.",
            question="Can the inner loop be replaced with a constant-time lookup?"))

    # Using namespace std (in header)
    if re.search(r'using\s+namespace\s+std', code):
        issues.append(Issue("warning", "Readability",
            "`using namespace std;` pollutes the global namespace — avoid in headers.",
            find_line(code, r'using\s+namespace\s+std'),
            hint="Use explicit `std::` prefix or a scoped `using` declaration.",
            question="What naming conflicts could arise from `using namespace std` in a large project?"))

    # Strengths
    if re.search(r'std::unique_ptr|std::shared_ptr|std::make_unique', code):
        strengths.append("Smart pointers used — good RAII practice.")
    if re.search(r'const\s+\w+', code):
        strengths.append("Uses `const` — good const-correctness practice.")
    if re.search(r'#pragma once|#ifndef\s+\w+_H', code):
        strengths.append("Include guard or `#pragma once` present.")
    if not strengths:
        strengths.append("Code compiles to recognizable C++ structure.")

    topics = ["RAII and smart pointers in C++", "Rule of Five (copy/move semantics)",
              "Undefined behaviour in C++", "Memory safety tools: Valgrind, AddressSanitizer",
              "Const-correctness"]

    report = EvalReport(language="C++", issues=issues, strengths=strengths, study_topics=topics)
    report.logic_score       = _deduct(95, issues, "Logic")
    report.syntax_score      = _deduct(90, issues, "Syntax")
    report.performance_score = _deduct(90, issues, "Performance")
    report.security_score    = _deduct(100, issues, "Security")
    report.readability_score = _deduct(90, issues, "Readability")
    report.overall_score     = int((report.logic_score + report.syntax_score +
                                    report.performance_score + report.security_score +
                                    report.readability_score) / 5)
    report.summary = _make_summary(report)
    return report


# ──────────────────────────────────────────────────────────────────────────────
# ── JAVA ANALYZER ────────────────────────────────────────────────────────────
# ──────────────────────────────────────────────────────────────────────────────

def analyze_java(code: str) -> EvalReport:
    issues: list[Issue] = []
    strengths: list[str] = []

    # == on String
    for ln in find_all_lines(code, r'".*"\s*==|==\s*"'):
        issues.append(Issue("critical", "Logic",
            "String compared with `==` (reference equality) instead of `.equals()` — logic bug.",
            ln,
            hint="`==` tests if two references point to the same object, not if their contents are equal.",
            question="What is the difference between `==` and `.equals()` for objects in Java?"))

    # Null dereference risk
    for ln in find_all_lines(code, r'\w+\s*=\s*null\s*;'):
        issues.append(Issue("medium", "Logic",
            "Variable explicitly set to `null` — ensure null-check before use to prevent NPE.",
            ln,
            hint="Consider `Optional<T>` to make nullability explicit in the type system.",
            question="Is there a code path where this variable is used without a null-check?"))

    # Catching generic Exception
    for ln in find_all_lines(code, r'catch\s*\(\s*Exception\s'):
        issues.append(Issue("medium", "Logic",
            "Catching `Exception` (too broad) — catch the most specific type.",
            ln,
            hint="Broad catches can swallow unexpected errors, making debugging very hard.",
            question="Which specific exceptions can this block throw?"))

    # Resource leak (stream / connection)
    if re.search(r'new\s+(FileInputStream|FileOutputStream|Connection|Socket)\s*\(', code):
        if not re.search(r'try\s*\(', code):  # no try-with-resources
            issues.append(Issue("high", "Security",
                "Resource opened without try-with-resources — potential resource leak.",
                find_line(code, r'new\s+(FileInputStream|FileOutputStream|Connection|Socket)'),
                hint="Use `try (Resource r = new Resource()) { … }` to ensure automatic closure.",
                question="Where is the `close()` method called for this resource?"))

    # Nested loops
    if re.search(r'for\s*\(.*\)\s*\{[^}]*for\s*\(', code, re.DOTALL):
        issues.append(Issue("medium", "Performance",
            "Nested loop — potential O(n²) complexity.",
            find_line(code, r'for\s*\('),
            hint="Consider a HashMap for O(1) lookups to eliminate the inner loop.",
            question="Is there a data structure that could answer the inner loop's question in O(1)?"))

    # Raw ArrayList without generics
    for ln in find_all_lines(code, r'new\s+ArrayList\s*\(\s*\)'):
        ctx = code.splitlines()[ln-1]
        if '<' not in ctx:
            issues.append(Issue("warning", "Syntax",
                "Raw `ArrayList` without generic type parameter — may produce unchecked warnings.",
                ln,
                hint="Specify the type: `new ArrayList<String>()`.",
                question="What type of objects does this list hold?"))

    # Strengths
    if re.search(r'@Override', code):
        strengths.append("`@Override` annotation used — prevents silent overload mistakes.")
    if re.search(r'try\s*\(', code):
        strengths.append("try-with-resources used — good resource management.")
    if re.search(r'Optional\s*<', code):
        strengths.append("`Optional<T>` used — explicit null-safety in the type system.")
    if re.search(r'private\s+\w+\s+\w+\s*;', code):
        strengths.append("Fields are private — good encapsulation.")
    if not strengths:
        strengths.append("Code follows recognizable Java structure.")

    topics = ["Java String equality: == vs .equals()", "Optional<T> and null safety",
              "Java try-with-resources", "Generics and type safety",
              "Java Collections Framework time complexities"]

    report = EvalReport(language="Java", issues=issues, strengths=strengths, study_topics=topics)
    report.logic_score       = _deduct(95, issues, "Logic")
    report.syntax_score      = _deduct(90, issues, "Syntax")
    report.performance_score = _deduct(90, issues, "Performance")
    report.security_score    = _deduct(100, issues, "Security")
    report.readability_score = _deduct(90, issues, "Readability")
    report.overall_score     = int((report.logic_score + report.syntax_score +
                                    report.performance_score + report.security_score +
                                    report.readability_score) / 5)
    report.summary = _make_summary(report)
    return report


# ──────────────────────────────────────────────────────────────────────────────
# ── PHP ANALYZER ─────────────────────────────────────────────────────────────
# ──────────────────────────────────────────────────────────────────────────────

def analyze_php(code: str) -> EvalReport:
    issues: list[Issue] = []
    strengths: list[str] = []

    # SQL injection
    sqli_pat = r'mysql_query\s*\(\s*["\'].*\$|query\s*\(\s*["\'].*\$|\$_GET|\$_POST.*query'
    ln = find_line(code, sqli_pat, re.IGNORECASE)
    if ln:
        issues.append(Issue("critical", "Security",
            "User input likely injected directly into SQL query — SQL Injection risk.",
            ln,
            hint="Use PDO or MySQLi with prepared statements and bound parameters.",
            question="What would happen if a user submitted `' OR '1'='1` as input here?"))

    # XSS — echo without escaping
    for ln in find_all_lines(code, r'echo\s+\$_(GET|POST|REQUEST|COOKIE)', re.IGNORECASE):
        issues.append(Issue("critical", "Security",
            "Echoing user input (`$_GET`/`$_POST`) without `htmlspecialchars()` — XSS vulnerability.",
            ln,
            hint="Wrap all user-supplied output in `htmlspecialchars($var, ENT_QUOTES, 'UTF-8')`.",
            question="What HTML/JS payload could an attacker inject through this output?"))

    # Deprecated mysql_* functions
    for ln in find_all_lines(code, r'\bmysql_'):
        issues.append(Issue("high", "Security",
            "Deprecated `mysql_*` functions used — removed in PHP 7. Use PDO or MySQLi.",
            ln,
            hint="PDO supports multiple databases; MySQLi is MySQL-specific. Both support prepared statements.",
            question="Which PDO or MySQLi equivalent replaces each `mysql_*` call here?"))

    # display_errors On
    ln = find_line(code, r'display_errors\s*=\s*(On|true|1)', re.IGNORECASE)
    if ln:
        issues.append(Issue("high", "Security",
            "`display_errors = On` in production leaks stack traces and path info to attackers.",
            ln,
            hint="Set `display_errors = Off` and `log_errors = On` in production php.ini.",
            question="What sensitive information could a stack trace reveal to an attacker?"))

    # eval()
    ln = find_line(code, r'\beval\s*\(')
    if ln:
        issues.append(Issue("critical", "Security",
            "`eval()` with dynamic content is a remote code execution risk.",
            ln,
            hint="There is almost never a legitimate need for `eval()` in PHP.",
            question="Can this be replaced with a safer dispatch mechanism?"))

    # Session without regeneration
    if re.search(r'session_start', code, re.IGNORECASE) and \
       not re.search(r'session_regenerate_id', code, re.IGNORECASE):
        issues.append(Issue("medium", "Security",
            "`session_start()` without `session_regenerate_id(true)` after login — session fixation risk.",
            find_line(code, r'session_start', re.IGNORECASE),
            hint="Always regenerate the session ID after a successful login.",
            question="What is a session fixation attack and how does `session_regenerate_id` prevent it?"))

    # Strengths
    if re.search(r'prepare\s*\(', code, re.IGNORECASE):
        strengths.append("Prepared statements used — protects against SQL injection.")
    if re.search(r'htmlspecialchars|htmlentities', code, re.IGNORECASE):
        strengths.append("`htmlspecialchars()` / `htmlentities()` used — XSS mitigation present.")
    if re.search(r'password_hash|password_verify', code, re.IGNORECASE):
        strengths.append("`password_hash()` used — secure password hashing.")
    if not strengths:
        strengths.append("Code is recognizable PHP.")

    topics = ["PHP PDO prepared statements", "OWASP Top 10 vulnerabilities",
              "XSS prevention in PHP", "PHP session security",
              "Content Security Policy (CSP) headers"]

    report = EvalReport(language="PHP", issues=issues, strengths=strengths, study_topics=topics)
    report.logic_score       = _deduct(95, issues, "Logic")
    report.syntax_score      = _deduct(90, issues, "Syntax")
    report.performance_score = _deduct(90, issues, "Performance")
    report.security_score    = _deduct(100, issues, "Security")
    report.readability_score = _deduct(90, issues, "Readability")
    report.overall_score     = int((report.logic_score + report.syntax_score +
                                    report.performance_score + report.security_score +
                                    report.readability_score) / 5)
    report.summary = _make_summary(report)
    return report


# ──────────────────────────────────────────────────────────────────────────────
# Summary generator
# ──────────────────────────────────────────────────────────────────────────────

def _make_summary(r: EvalReport) -> str:
    issue_count = len(r.issues)
    crit = sum(1 for i in r.issues if i.severity == "critical")
    if r.overall_score >= 85:
        verdict = "The submission demonstrates strong quality with minor points for improvement."
    elif r.overall_score >= 65:
        verdict = f"The submission is functional but has {issue_count} issue(s) that deserve attention."
    elif r.overall_score >= 45:
        verdict = f"Notable quality concerns found: {issue_count} issue(s), including {crit} critical."
    else:
        verdict = f"Significant problems detected — {crit} critical issue(s) require immediate attention."
    return f"OmniCheck AI detected {issue_count} issue(s) across all dimensions. {verdict}"


# ──────────────────────────────────────────────────────────────────────────────
# Dispatcher
# ──────────────────────────────────────────────────────────────────────────────

def run_analysis(code: str, language: str) -> EvalReport:
    analyzers = {
        "Python": analyze_python,
        "SQL":    analyze_sql,
        "C++":    analyze_cpp,
        "Java":   analyze_java,
        "PHP":    analyze_php,
    }
    fn = analyzers.get(language, analyze_python)
    return fn(code)


# ──────────────────────────────────────────────────────────────────────────────
# UI rendering helpers
# ──────────────────────────────────────────────────────────────────────────────

def render_score_cards(r: EvalReport):
    items = [
        ("Overall",      r.overall_score),
        ("Logic",        r.logic_score),
        ("Syntax",       r.syntax_score),
        ("Performance",  r.performance_score),
        ("Security",     r.security_score),
        ("Readability",  r.readability_score),
    ]
    html = '<div class="score-grid">'
    for label, val in items:
        cls = score_class(val)
        html += f'<div class="score-card"><div class="lbl">{label}</div>' \
                f'<div class="val {cls}">{val}<span style="font-size:1rem;font-weight:400">%</span></div></div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


def render_progress_bars(r: EvalReport):
    pairs = [
        ("Logic Correctness", r.logic_score),
        ("Syntax Quality",    r.syntax_score),
        ("Performance",       r.performance_score),
        ("Security",          r.security_score),
        ("Readability",       r.readability_score),
    ]
    for label, val in pairs:
        color = "#68d391" if val >= 85 else "#63b3ed" if val >= 65 else "#f6e05e" if val >= 45 else "#fc8181"
        st.markdown(f"""
        <div style="margin-bottom:9px">
          <div style="display:flex;justify-content:space-between;color:#a0aec0;font-size:.8rem;margin-bottom:3px">
            <span>{label}</span><span style="color:{color};font-weight:600">{val}%</span>
          </div>
          <div style="background:#2d3748;border-radius:99px;height:7px;overflow:hidden">
            <div style="width:{val}%;background:{color};height:100%;border-radius:99px"></div>
          </div>
        </div>""", unsafe_allow_html=True)


def badge_html(severity: str) -> str:
    return f'<span class="badge {severity}">{severity}</span>'


def render_report(r: EvalReport):
    # Language pill
    lang_css = r.language.lower().replace("+", "p")
    st.markdown(f'<span class="lang-pill {lang_css}">🔬 {r.language}</span>', unsafe_allow_html=True)

    render_score_cards(r)
    st.markdown("---")
    render_progress_bars(r)

    # Tabs
    t = st.tabs(["📋 Summary", "🧠 Logic & Syntax", "⚡ Performance", "🔒 Security", "📖 Readability", "🗺️ Improvement Plan"])

    cats_for_tab = {
        0: None,                               # summary — special
        1: ["Logic", "Syntax"],
        2: ["Performance"],
        3: ["Security"],
        4: ["Readability"],
        5: None,                               # improvement plan — special
    }

    # ── Tab 0: Summary ───────────────────────────────────────────────────────
    with t[0]:
        st.markdown('<div class="sec-title">Executive Summary</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="info-box">{r.summary}</div>', unsafe_allow_html=True)

        if r.overall_score >= 85:
            st.markdown('<div class="ok-box">✅ <strong>Excellent</strong> — Strong quality across all dimensions.</div>', unsafe_allow_html=True)
        elif r.overall_score >= 65:
            st.markdown('<div class="info-box">🔵 <strong>Good</strong> — Solid work with some areas to address.</div>', unsafe_allow_html=True)
        elif r.overall_score >= 45:
            st.markdown('<div class="warn-box">⚠️ <strong>Fair</strong> — Notable issues that should be resolved.</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="err-box">❌ <strong>Needs Rework</strong> — Significant problems detected.</div>', unsafe_allow_html=True)

        if r.strengths:
            st.markdown('<div class="sec-title">✅ Strengths Identified</div>', unsafe_allow_html=True)
            for s in r.strengths:
                st.markdown(f"- {s}")

        if r.study_topics:
            st.markdown('<div class="sec-title">📚 Recommended Study Topics</div>', unsafe_allow_html=True)
            for topic in r.study_topics:
                st.markdown(f"- {topic}")

    # ── Tabs 1–4: Issues by category ─────────────────────────────────────────
    for tab_idx in range(1, 5):
        with t[tab_idx]:
            cats = cats_for_tab[tab_idx]
            tab_issues = [i for i in r.issues if i.category in cats]
            if not tab_issues:
                st.markdown('<div class="ok-box">✅ No significant issues detected in this category.</div>', unsafe_allow_html=True)
            else:
                for issue in tab_issues:
                    line_ref = f" <small style='color:#718096'>(line {issue.line})</small>" if issue.line else ""
                    box_cls = "err-box" if issue.severity in ("critical", "high") else "warn-box" if issue.severity in ("medium", "warning") else "info-box"
                    st.markdown(
                        f'<div class="{box_cls}">{badge_html(issue.severity)} {issue.message}{line_ref}</div>',
                        unsafe_allow_html=True
                    )

    # ── Tab 5: Improvement Plan ───────────────────────────────────────────────
    with t[5]:
        actionable = [i for i in r.issues if i.question]
        if not actionable:
            st.markdown('<div class="ok-box">✅ No guided improvement steps needed — well done!</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="info-box">💡 These are <strong>Socratic guiding questions</strong> — work through each step independently to build deeper understanding. No direct fixes are provided intentionally.</div>', unsafe_allow_html=True)
            for step, issue in enumerate(actionable, 1):
                with st.expander(f"Step {step}: [{issue.severity.upper()}] {issue.category} — {issue.message[:60]}…"):
                    st.markdown("**🤔 Guiding Question:**")
                    st.markdown(f"> {issue.question}")
                    st.markdown("**💡 Conceptual Hint:**")
                    st.markdown(f'<div class="info-box">{issue.hint}</div>', unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────────────────────
# Sidebar
# ──────────────────────────────────────────────────────────────────────────────

def render_sidebar() -> dict:
    with st.sidebar:
        st.markdown("## ⚙️ Settings")
        st.markdown("---")
        lang_choice = st.selectbox(
            "Language Override",
            ["Auto-Detect", "Python", "C++", "Java", "PHP", "SQL"],
            index=0,
        )
        st.markdown("---")
        st.markdown("### 📊 Session History")
        history = st.session_state.get("history", [])
        if history:
            for h in reversed(history[-6:]):
                color_map = {"excellent": "#68d391", "good": "#63b3ed", "fair": "#f6e05e", "poor": "#fc8181"}
                c = color_map.get(score_class(h["score"]), "#a0aec0")
                st.markdown(
                    f'<div style="background:#1a202c;border:1px solid #2d3748;border-radius:6px;'
                    f'padding:7px 11px;margin-bottom:5px;font-size:.78rem">'
                    f'<span style="color:#a0aec0">{h["ts"]}</span><br>'
                    f'<span style="color:#e2e8f0">{h["lang"]}</span>'
                    f'<span style="float:right;color:{c};font-weight:700">{h["score"]}%</span></div>',
                    unsafe_allow_html=True
                )
        else:
            st.markdown('<span style="color:#4a5568;font-size:.8rem">No evaluations yet.</span>', unsafe_allow_html=True)

        st.markdown("---")
        st.markdown(
            '<div style="color:#4a5568;font-size:.73rem;line-height:1.6">'
            '<strong style="color:#718096">OmniCheck AI</strong><br>'
            'Rule-based static analysis<br>'
            'Python · C++ · Java · PHP · SQL<br>'
            'No external API required'
            '</div>', unsafe_allow_html=True
        )
    return {"lang": lang_choice}


# ──────────────────────────────────────────────────────────────────────────────
# Quick example snippets
# ──────────────────────────────────────────────────────────────────────────────

EXAMPLES = {
    "🐍 Python": textwrap.dedent("""\
        def find_duplicates(lst=[]):
            seen = []
            for item in lst:
                if item in seen:
                    lst.append(item)   # bug: mutating list while iterating
            return seen

        result = find_duplicates([1, 2, 3, 2, 4])
        print(result)
    """),
    "🗄️ SQL": textwrap.dedent("""\
        SELECT * FROM orders o, customers c
        WHERE o.customer_id = c.id
        AND c.name LIKE '%' + @search + '%'
        ORDER BY o.created_at
    """),
    "☕ Java": textwrap.dedent("""\
        public class UserService {
            private List users = new ArrayList();

            public boolean findUser(String name) {
                for (int i = 0; i < users.size(); i++) {
                    if (users.get(i) == name)
                        return true;
                }
                return false;
            }
        }
    """),
    "🐘 PHP": textwrap.dedent("""\
        <?php
        $id = $_GET['id'];
        $result = mysql_query("SELECT * FROM users WHERE id = " . $id);
        while ($row = mysql_fetch_array($result)) {
            echo $row['username'];
        }
    """),
    "⚙️ C++": textwrap.dedent("""\
        #include <iostream>
        using namespace std;

        int* createArray(int size) {
            int* arr = new int[size];
            for (int i = 0; i < size; i++)
                arr[i] = i * 2;
            return arr;
        }

        int main() {
            int* data = createArray(10);
            printf(data[0]);   // format string issue
            return 0;
        }
    """),
}


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────

def main():
    if "history" not in st.session_state:
        st.session_state.history = []
    if "last_report" not in st.session_state:
        st.session_state.last_report = None

    cfg = render_sidebar()

    # Header
    st.markdown("""
    <div class="omni-header">
        <h1>🔬 OmniCheck AI</h1>
        <p>Multi-Language &amp; Database Practical Evaluation Agent<br>
        <span style="color:#4a5568;font-size:.82rem">
            Python · C++ · Java · PHP · SQL &nbsp;·&nbsp;
            Rule-based static analysis &nbsp;·&nbsp; No API key required
        </span></p>
    </div>
    """, unsafe_allow_html=True)

    # ── Input area ────────────────────────────────────────────────────────────
    col_main, col_side = st.columns([3, 1], gap="medium")

    # If a Quick Example was picked, pre-load it into the widget's own key
    # BEFORE the widget is rendered so Streamlit picks it up correctly.
    if "_pending_code" in st.session_state:
        st.session_state["code_area"] = st.session_state.pop("_pending_code")

    with col_main:
        st.markdown("#### 📝 Paste Code or SQL Query")
        paste_tab, file_tab = st.tabs(["✏️ Paste", "📁 Upload File"])

        with paste_tab:
            code_input = st.text_area(
                "code",
                height=300,
                placeholder="Paste your code or SQL here…",
                label_visibility="collapsed",
                key="code_area",
            )

        with file_tab:
            uploaded = st.file_uploader(
                "Upload source file",
                type=["py", "cpp", "cc", "java", "php", "sql", "txt"],
                key="uploader",
            )
            if uploaded:
                content = uploaded.read().decode("utf-8", errors="replace")
                st.code(content[:400] + ("…" if len(content) > 400 else ""), language="text")
                code_input = content
                st.session_state["uploaded_fname"] = uploaded.name
                st.success(f"Loaded `{uploaded.name}` — {len(content)} chars")

    with col_side:
        st.markdown("#### 🎯 Quick Examples")
        for label, snippet in EXAMPLES.items():
            if st.button(label, use_container_width=True):
                st.session_state["_pending_code"] = snippet
                st.rerun()

    # ── Action buttons ────────────────────────────────────────────────────────
    st.markdown("---")
    b1, b2, b3 = st.columns([2, 1, 1])
    with b1:
        run_btn = st.button("🚀 Evaluate Code", type="primary", use_container_width=True)
    with b2:
        clear_btn = st.button("🗑️ Clear", use_container_width=True)
    with b3:
        if st.session_state.last_report:
            r = st.session_state.last_report
            export = {
                "language": r.language, "overall_score": r.overall_score,
                "logic_score": r.logic_score, "syntax_score": r.syntax_score,
                "performance_score": r.performance_score,
                "security_score": r.security_score,
                "readability_score": r.readability_score,
                "summary": r.summary,
                "issues": [{"severity": i.severity, "category": i.category,
                             "message": i.message, "line": i.line} for i in r.issues],
                "strengths": r.strengths,
                "study_topics": r.study_topics,
                "timestamp": datetime.now().isoformat(),
            }
            st.download_button(
                "⬇️ Export JSON",
                data=json.dumps(export, indent=2),
                file_name=f"omnicheck_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True,
            )

    if clear_btn:
        st.session_state.last_report = None
        st.session_state.pop("_pending_code", None)
        st.session_state.pop("code_area", None)
        st.session_state.pop("uploaded_fname", None)
        st.rerun()

    # ── Run evaluation ────────────────────────────────────────────────────────
    final_code = (code_input or "").strip()

    if run_btn:
        if not final_code:
            st.markdown('<div class="warn-box">⚠️ Please paste or upload code to evaluate.</div>', unsafe_allow_html=True)
            st.stop()
        if len(final_code) < 8:
            st.markdown('<div class="warn-box">⚠️ Input is too short for a meaningful evaluation.</div>', unsafe_allow_html=True)
            st.stop()

        fname = st.session_state.get("uploaded_fname", "")
        language = cfg["lang"] if cfg["lang"] != "Auto-Detect" else detect_language(final_code, fname)

        with st.spinner(f"🔬 Analysing {language} code…"):
            report = run_analysis(final_code, language)

        st.session_state.last_report = report
        st.session_state.history.append({
            "ts":    datetime.now().strftime("%H:%M:%S"),
            "lang":  language,
            "score": report.overall_score,
        })

    # ── Render report ─────────────────────────────────────────────────────────
    if st.session_state.last_report:
        st.markdown("---")
        st.markdown("## 📊 Evaluation Report")
        render_report(st.session_state.last_report)

    # Footer
    st.markdown(
        '<div class="footer">OmniCheck AI · Multi-Language &amp; Database Practical Evaluation Agent · '
        'Built with Streamlit · Rule-based static analysis · No API key required</div>',
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
