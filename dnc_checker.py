import pandas as pd
import re
from rapidfuzz import process, fuzz

# Cleaning functions
def clean_company_name(name):
    if pd.isna(name):
        return ""
    name = name.lower()
    name = re.sub(r'[^\w\s]', '', name)
    name = re.sub(r'\b(inc|ltd|llc|corp|pty|company|co|the)\b', '', name)
    name = re.sub(r'\s+', ' ', name)
    return name.strip()

def clean_domain(domain):
    if pd.isna(domain):
        return ""
    return domain.lower().replace("www.", "").strip()

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
contacts_df = pd.read_csv("contacts.csv")
do_not_contact_df = pd.read_csv("do_not_contact.csv")

# Clean and prep
contacts_df['clean_company'] = contacts_df['company'].apply(clean_company_name)
contacts_df['clean_domain'] = contacts_df['domain'].apply(clean_domain)
contacts_df['email_domain'] = contacts_df['email'].str.extract(r'@([\w\.-]+)')
contacts_df['email_domain'] = contacts_df['email_domain'].apply(clean_domain)

do_not_contact_df['clean_company'] = do_not_contact_df['company'].apply(clean_company_name)
do_not_contact_df['clean_domain'] = do_not_contact_df['domain'].apply(clean_domain)

dnc_domains = set(do_not_contact_df['clean_domain'].dropna())
dnc_companies = set(do_not_contact_df['clean_company'].dropna())

# Match logic
contacts_df['domain_exact'] = contacts_df['clean_domain'].isin(dnc_domains)
contacts_df['company_exact'] = contacts_df['clean_company'].isin(dnc_companies)
contacts_df['email_domain_flag'] = contacts_df['email_domain'].isin(dnc_domains)

contacts_df['company_fuzzy'] = contacts_df.apply(
    lambda row: fuzzy_check(row['clean_company'], dnc_companies) if not row['company_exact'] else False,
    axis=1
)

contacts_df['fuzzy_score'] = contacts_df['clean_company'].apply(lambda x: fuzzy_score(x, dnc_companies))
contacts_df['needs_review'] = contacts_df['fuzzy_score'].between(80, 89)

contacts_df['do_not_contact'] = (
    contacts_df['domain_exact'] |
    contacts_df['company_exact'] |
    contacts_df['company_fuzzy'] |
    contacts_df['email_domain_flag']
)

# Save the result
contacts_df.to_csv("contacts_checked.csv", index=False)
print("✅ Done! Output saved to 'contacts_checked.csv'")
