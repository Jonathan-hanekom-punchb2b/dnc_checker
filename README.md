
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

## 🚀 Getting Started (for New Users)

### 1. Download the Repository


Download the .zip file from Github above (The big green button) or follow this link: https://github.com/jonohanekom/dnc_checker/archive/refs/heads/main.zip


---

### 2. Install Python (if not already installed)

- Download and install from: https://www.python.org/downloads/windows/
- ✅ Ensure you check **“Add Python to PATH”** during installation.

---

### 3. Install `uv` (Python package & environment manager)

```bash
pip install uv
```

Test installation:

```bash
uv --version
```

---

### 4. Create and Activate the Virtual Environment

```bash
uv venv
```

Then activate it:

- On **Windows**:
  ```bash
  .venv\Scripts\activate
  ```

- On **macOS/Linux**:
  ```bash
  source .venv/bin/activate
  ```

---

### 5. Install Dependencies

With the environment activated:

```bash
uv pip install -r pyproject.toml
```

---

### 6. Add Your Data Files

- Place `contacts.csv` and `do_not_contact.csv` into the project folder.
- Required columns:

  `contacts.csv`:
  - `company`, `domain`, `email`

  `do_not_contact.csv`:
  - `company`, `domain`

---

### 7. Run the Script

```bash
python dnc_checker.py
```

Output: `contacts_checked.csv` will contain flags for any matches found.

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


