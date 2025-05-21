
# 🛑 Do Not Contact (DNC) Checker

This tool helps teams safely and **accurately compare a list of sourced accounts against a "Do Not Contact" (DNC) list**, using both exact and fuzzy matching techniques on company names and domains.

---

## 📁 Project Structure

```
dnc_checker/
├── zoominfo_contacts.csv      # Your list of sourced accounts
├── exclusions.csv             # Master DNC list (company & domain)
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

- Download and install from: https://www.python.org/downloads
- Select the latest version.
- Select the version compatible with your operating system.
- ✅ Ensure you check **“Add Python to PATH”** during installation. (Windows only)

---

### 3. Test Python Installation

On **Windows**:
```powershell
python --version 
```
On **macOS/Linux**:
```bash
python3 --version
```

---

### 4. Install `uv` (Python package & environment manager)

On **Windows**:
```powershell
pip install uv
```
On **macOS/Linux**:
```bash
pip3 install uv
```
Test installation:

```bash
uv --version
```

---
### 5. To allow the Virtual Environment to run without Admin Privileges (Windows only)
```bash
Set-ExecutionPolicy -Scope CurrentUser Bypass
```
---
### 6. Create and Activate the Virtual Environment

```bash
uv venv
```

Then activate it:

- On **Windows**:
  ```powershell
  .venv\Scripts\activate
  ```

- On **macOS/Linux**:
  ```bash
  source .venv/bin/activate
  ```

---

### 7. Install Dependencies

With the environment activated:

```powershell
uv pip install -r pyproject.toml
```

---

### 8. Add Your Data Files

- Place `zoominfo_contacts.csv` and `exclusions.csv` into the project folder.
- `zoominfo_contacts.csv` should be the list of accounts you have sourced contacts from in ZoomInfo.
- `exclusions.csv` should be the client provided list of accounts to exclude. 
- Required columns:

  `zoominfo_contacts.csv`:
  - `company`, `domain`

  `exclusions.csv`:
  - `company`, `domain`
- It is vitally important that the column headers be formatted **exactly** as shown above. 

---

### 9. Run the Script

- On **Windows**:
```powershell
python dnc_checker.py
```

- On **macOS/Linux**:
```bash
python3 dnc_checker.py
```
Output: `accounts_checked.csv` will contain flags for any matches found.

---

### 10. Upload to Google Sheets

- Create a new sheet in your working spreadsheet and import the data. 
- Filter the data by the `do_not_contact` column. 
- Move all the contacts associated with the flagged accounts.

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


