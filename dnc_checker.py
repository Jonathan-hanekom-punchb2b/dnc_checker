import pandas as pd
import re
from rapidfuzz import process, fuzz

# Cleaning functions
def clean_text(text):
    if pd.isna(text):
        return ""
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def clean_company_name(name):
    name = re.sub(r'\b(inc|ltd|llc|corp|pty|company|co|the)\b', '', name)
    return clean_text(name)

def clean_domain(domain):
    return clean_text(domain).replace("www.", "")

def fuzzy_check(name, name_set, threshold=90):
    if not name:
        return False
    match = process.extractOne(name, name_set, scorer=fuzz.token_sort_ratio)
    return match and match[1] >= threshold

def fuzzy_score(name, name_set):
    if not name:
        return 0
    match = process.extractOne(name, name_set, scorer=fuzz.token_sort_ratio)
    return match[1] if match else 0

# Load your CSVs
contacts_df = pd.read_csv("zoominfo_contacts.csv")
do_not_contact_df = pd.read_csv("exclusions.csv")

# Clean and prep using the original column names
contacts_df['clean_company'] = contacts_df['Company Name'].apply(clean_company_name)
contacts_df['clean_domain'] = contacts_df['Company Domain'].apply(clean_domain)

do_not_contact_df['clean_company'] = do_not_contact_df['Company Name'].apply(clean_company_name)
do_not_contact_df['clean_domain'] = do_not_contact_df['Company Domain'].apply(clean_domain)

dnc_domains = set(do_not_contact_df['clean_domain'].dropna())
dnc_companies = set(do_not_contact_df['clean_company'].dropna())

# Match logic
contacts_df['domain_exact_match'] = contacts_df['clean_domain'].isin(dnc_domains)
contacts_df['company_exact_match'] = contacts_df['clean_company'].isin(dnc_companies)

contacts_df['company_fuzzy_match'] = contacts_df.apply(
    lambda row: fuzzy_check(row['clean_company'], dnc_companies) if not row['company_exact_match'] else False,
    axis=1
)

contacts_df['company_fuzzy_score'] = contacts_df['clean_company'].apply(lambda x: fuzzy_score(x, dnc_companies))
contacts_df['company_needs_review'] = contacts_df['company_fuzzy_score'].between(80, 89)

contacts_df['do_not_contact'] = (
    contacts_df['domain_exact_match'] |
    contacts_df['company_exact_match'] |
    contacts_df['company_fuzzy_match']
)

# Select and save the relevant columns
output_df = contacts_df[['Company Name', 'Company Domain', 'do_not_contact', 'company_exact_match', 'company_fuzzy_match', 'company_fuzzy_score', 'company_needs_review', 'domain_exact_match']]
output_df.to_csv("accounts_checked.csv", index=False)

print("✅ Done! Output saved to 'accounts_checked.csv'")
print("🗑️ Remember to delete all contact data from you personal computer and clear out your recycle bin")