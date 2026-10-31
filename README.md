# 🔬 OmniCheck AI
### Multi-Language & Database Practical Evaluation Agent

An AI-powered technical evaluator that acts as an **objective, analytical, and educational** lab assistant for evaluating programming code and SQL queries — without ever handing out answers directly.

> ✅ **No API key required. No internet connection needed. Runs fully offline.**

---

## ✨ Features

| Feature | Detail |
|---|---|
| **Auto Language Detection** | Heuristic detection for Python, C++, Java, PHP, SQL |
| **File Upload Support** | `.py`, `.cpp`, `.java`, `.php`, `.sql`, `.txt`, `.h`, `.hpp` |
| **Rule-based Analysis** | Instant evaluation — no external API calls |
| **Structured Report** | Tabbed breakdown: Logic · Syntax · Performance · Security · Readability |
| **Score Dashboard** | Percentage scores + progress bars for each dimension |
| **Socratic Guidance** | Step-by-step improvement roadmap — zero direct code fixes |
| **JSON Export** | Download full report as structured JSON |
| **Evaluation History** | Per-session history with scores in the sidebar |
| **Quick Examples** | One-click code examples for all 5 supported languages |
| **Dark UI** | Professional dark-mode interface |

---

## 🚀 Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/YOUR_USERNAME/omnicheck-ai.git
cd omnicheck-ai
pip install -r requirements.txt
```

### 2. Run

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser. No configuration needed.

---

## 🗂️ Project Structure

```
omnicheck-ai/
├── app.py                  # Main application (rule-based engine + UI)
├── requirements.txt        # Python dependencies (streamlit only)
├── .streamlit/
│   └── config.toml         # Dark theme configuration
└── README.md
```

---

## 📦 Dependencies

```
streamlit>=1.35.0
```

Only **one dependency**. All other modules (`re`, `os`, `json`, `textwrap`, `dataclasses`, `datetime`) are Python standard library — no external API, no paid service, no network required.

---

## 📊 Evaluation Dimensions

| Dimension | What It Measures |
|---|---|
| **Logic Correctness** | Algorithmic correctness, edge cases, control flow |
| **Syntax Quality** | Language-specific syntax, style, coding standards |
| **Performance** | Time/space complexity, bottlenecks, anti-patterns |
| **Security** | Injection risks, memory safety, auth weaknesses |
| **Readability** | Naming conventions, documentation, code structure |

---

## 🌐 Supported Languages & Focus Areas

### 🐍 Python
PEP 8 compliance, mutable default arguments, bare `except`, `eval()`/`exec()`, nested loops, O(n) list lookups, `shell=True` subprocess

### ⚙️ C++
Memory leaks (`new`/`delete` imbalance), raw pointer returns, missing virtual destructor, `printf(var)` format string vulnerability, `using namespace std`

### ☕ Java
String `==` vs `.equals()`, raw `ArrayList` without generics, broad `Exception` catch, resource leaks without try-with-resources

### 🐘 PHP
SQL injection via `$_GET`/`$_POST`, XSS via unescaped echo, deprecated `mysql_*` functions, `eval()`, session fixation

### 🗄️ SQL
`SELECT *`, missing `WHERE` clause (full table scan), leading `%` wildcard, excessive JOINs, correlated subqueries, SQL injection via string concatenation

---

## 🔒 Philosophy

> **OmniCheck AI never gives you corrected code.**
>
> Instead, it asks Socratic guiding questions and provides conceptual hints that help you discover the fix yourself — building deeper understanding, not dependency.

---

## 🛠️ Configuration

| Setting | Location | Default |
|---|---|---|
| Language Override | Sidebar dropdown | `Auto-Detect` |

No other configuration required.

---

## 📄 License

MIT License — free for educational and personal use.
