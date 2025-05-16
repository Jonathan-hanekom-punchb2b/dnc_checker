
# 🛑 Do Not Contact (DNC) Checker

This tool helps teams safely and **accurately compare a list of sourced contacts against a "Do Not Contact" (DNC) list**, using both exact and fuzzy matching techniques on company names and domains.

---

## 📁 Project Structure

```
dnc_checker/
├── contacts.csv               # Your list of sourced contacts
├── do_not_contact.csv         # Master DNC list (company & domain)
├── dnc_checker.py             # Main Python script
├── pyproject.toml             # Dependencies (pandas + rapidfuzz)
└── README.md                  # This document
```

---

## 🧠 How It Works

1. **Cleans** company names by removing punctuation, common suffixes (e.g., "Inc", "LLC"), and normalizing spaces.
2. **Cleans** domains and email domains for consistent comparison.
3. Performs the following checks:
   - ✅ Exact match on cleaned domain
   - ✅ Exact match on cleaned company name
   - ✅ Fuzzy match on cleaned company name (with score ≥ 90)
   - ✅ Match between email domain and DNC domains
4. Adds a `do_not_contact` column to flag any contact that matched one or more of the above.
5. Optionally flags contacts for manual review if the fuzzy score is borderline (80–89).

---

## ✅ Setup Instructions (Windows)

### 1. Install Python

- Download and install from: https://www.python.org/downloads/windows/
- Make sure to select **“Add Python to PATH”** during installation.

### 2. Install `uv`

```bash
pip install uv
```

### 3. Clone or Create Project Folder

```bash
mkdir dnc_checker
cd dnc_checker
```

### 4. Create Virtual Environment

```bash
uv venv
```

Activate it:

```bash
.venv\Scripts\activate   # Windows
```

### 5. Add Dependencies

Create `pyproject.toml`:

```toml
[project]
name = "dnc-checker"
version = "0.1.0"
dependencies = [
    "pandas",
    "rapidfuzz"
]
```

Then run:

```bash
uv pip install -r pyproject.toml
```

### 6. Add Your Files

- Place `contacts.csv` and `do_not_contact.csv` in the folder.
- Ensure both contain at least:
  - `company`, `domain`, `email` (for `contacts.csv`)
  - `company`, `domain` (for `do_not_contact.csv`)

### 7. Run the Script

```bash
python dnc_checker.py
```

### 8. Review Output

A new file `contacts_checked.csv` will be created with flags and scores.

---

## 🧪 Sample Output Columns

| company         | domain        | email                | do_not_contact |
|------------------|---------------|------------------------|----------------|
| Acme Inc.       | acme.com      | jdoe@acme.com         | TRUE           |
| Example Company | example.org   | jane@example.org      | FALSE          |

---

## 👥 Matching Logic Summary

| Check Type      | Method         | Threshold |
|------------------|----------------|-----------|
| Domain Match     | Exact match    | N/A       |
| Company Match    | Exact match    | N/A       |
| Email Domain     | Exact match    | N/A       |
| Fuzzy Match      | Token Sort     | ≥ 90%     |
| Manual Review    | Token Sort     | 80–89%    |

---

## 🧹 Cleaning Heuristics

- Converts text to lowercase
- Removes:
  - Punctuation
  - Keywords: `inc`, `ltd`, `llc`, `corp`, `pty`, `company`, `co`, `the`
- Normalizes whitespace

---

## 🙋 Need Help?

Let us know if you'd like a downloadable zip with everything ready to go!
