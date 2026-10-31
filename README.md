# 🔬 OmniCheck AI
### Multi-Language & Database Practical Evaluation Agent

An AI-powered technical evaluator that acts as an **objective, analytical, and educational** lab assistant for evaluating programming code and SQL queries — without ever handing out answers directly.

---

## ✨ Features

| Feature | Detail |
|---|---|
| **Auto Language Detection** | Heuristic detection for Python, C++, Java, PHP, SQL |
| **File Upload Support** | `.py`, `.cpp`, `.java`, `.php`, `.sql`, `.txt`, `.h`, `.hpp` |
| **Streaming Evaluation** | Real-time token streaming from OpenAI |
| **Structured Report** | Tabbed breakdown: Logic · Syntax · Performance · Security · Readability |
| **Score Dashboard** | Percentage scores + progress bars for each dimension |
| **Socratic Guidance** | Step-by-step improvement roadmap — zero direct code fixes |
| **JSON Export** | Download full report as structured JSON |
| **Evaluation History** | Per-session history with scores in the sidebar |
| **Dark UI** | Professional dark-mode interface |

---

## 🚀 Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/YOUR_USERNAME/omnicheck-ai.git
cd omnicheck-ai
pip install -r requirements.txt
```

### 2. Set your OpenAI API Key

Either enter it directly in the sidebar UI, or set it as an environment variable:

```bash
# Linux / macOS
export OPENAI_API_KEY="sk-..."

# Windows PowerShell
$env:OPENAI_API_KEY = "sk-..."
```

### 3. Run

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## 🗂️ Project Structure

```
omnicheck-ai/
├── app.py                  # Main application
├── requirements.txt        # Python dependencies
├── .streamlit/
│   └── config.toml         # Dark theme configuration
└── README.md
```

---

## 📊 Evaluation Dimensions

| Dimension | What It Measures |
|---|---|
| **Logic Correctness** | Algorithmic correctness, edge cases, control flow |
| **Syntax Quality** | Language-specific syntax, style, PEP 8 / coding standards |
| **Performance** | Time/space complexity, bottlenecks, anti-patterns |
| **Security** | Injection risks, memory safety, auth weaknesses |
| **Readability** | Naming, documentation, code structure |

---

## 🌐 Supported Languages & Focus Areas

### Python
- PEP 8 compliance, Pythonic idioms, mutable defaults, exception handling

### C++
- Memory leaks, undefined behavior, RAII, smart pointers, const-correctness

### Java
- SOLID principles, NPE risks, resource leaks, `equals()`/`hashCode()` contract

### PHP
- SQL injection via unsanitized input, XSS, CSRF, session security

### SQL
- Full table scans, missing indexes, `SELECT *`, N+1 queries, SQL injection in dynamic SQL

---

## 🔒 Philosophy

> **OmniCheck AI never gives you corrected code.**
>
> Instead, it asks Socratic guiding questions and provides conceptual hints that help you discover the fix yourself — building deeper understanding, not dependency.

---

## 📦 Dependencies

```
streamlit>=1.35.0
openai>=1.30.0
```

No additional dependencies required — all other modules (`re`, `os`, `json`, `textwrap`, `datetime`) are Python standard library.

---

## 🛠️ Configuration

| Setting | Location | Default |
|---|---|---|
| OpenAI API Key | Sidebar input or `OPENAI_API_KEY` env var | — |
| Model | Sidebar dropdown | `gpt-4o` |
| Language Override | Sidebar dropdown | `Auto-Detect` |

---

## 📄 License

MIT License — free for educational and personal use.
