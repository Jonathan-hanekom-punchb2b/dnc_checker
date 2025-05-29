import pandas as pd
import re
from rapidfuzz import process, fuzz
from tqdm.auto import tqdm # Import tqdm for progress bars


# --- Configuration ---
CONFIG = {
    "contacts_file": "zoominfo_contacts.csv",
    "exclusions_file": "exclusions.csv",
    "output_file": "accounts_checked.csv",
    "fuzzy_threshold_match": 90,
    "fuzzy_threshold_review": 85
}

# --- Pre-compiled Regular Expressions ---
_RE_NON_ALPHANUMERIC = re.compile(r'[^\w\s]')
_RE_MULTIPLE_SPACES = re.compile(r'\s+')
_RE_COMPANY_SUFFIXES = re.compile(r'\b(inc|ltd|llc|corp|pty|company|co|the)\b', re.IGNORECASE)

# --- Cleaning Functions ---
def clean_text(text):
    if pd.isna(text):
        return ""
    text = text.lower()
    text = _RE_NON_ALPHANUMERIC.sub('', text)
    text = _RE_MULTIPLE_SPACES.sub(' ', text)
    return text.strip()

def clean_company_name(name):
    name = _RE_COMPANY_SUFFIXES.sub('', name)
    return clean_text(name)

def clean_domain(domain):
    # Ensure domain is treated as a string before cleaning
    return clean_text(str(domain)).replace("www.", "")

# --- Fuzzy Matching Functions ---
def get_fuzzy_score_and_match(name, name_set):
    """
    Returns the best fuzzy score and the matched string from the name_set.
    """
    if not name or not name_set:
        return 0, None
    match = process.extractOne(name, name_set, scorer=fuzz.token_sort_ratio)
    if match:
        return match[1], match[0] # score, matched_string
    return 0, None

# --- Main Script Logic ---
def main():
    print("--- Starting DNC Check Script ---")

    # Load CSVs with error handling
    try:
        contacts_df = pd.read_csv(CONFIG["contacts_file"])
        do_not_contact_df = pd.read_csv(CONFIG["exclusions_file"])
        print(f"Successfully loaded '{CONFIG['contacts_file']}' containing **{len(contacts_df)}** companies to check and '{CONFIG['exclusions_file']}' with **{len(do_not_contact_df)}** exclusion entries.")
    except FileNotFoundError as e:
        print(f"Error: Required file not found - {e}. Please ensure '{CONFIG['contacts_file']}' and '{CONFIG['exclusions_file']}' are in the same directory.")
        return
    except Exception as e:
        print(f"An unexpected error occurred while loading files: {e}")
        return

    print("\nCleaning contacts data...")
    # Use list comprehensions with tqdm directly for explicit progress bars.
    contacts_df['clean_company'] = [
        clean_company_name(name)
        for name in tqdm(contacts_df['Company Name'], desc="Cleaning Contact Company Names", total=len(contacts_df))
    ]
    contacts_df['clean_domain'] = [
        clean_domain(domain)
        for domain in tqdm(contacts_df['Company Domain'], desc="Cleaning Contact Company Domains", total=len(contacts_df))
    ]


    print("\nCleaning exclusion data...")
    # For the exclusion data, standard apply is fine as it's usually smaller
    do_not_contact_df['clean_company'] = do_not_contact_df['Company Name'].apply(clean_company_name)
    do_not_contact_df['clean_domain'] = do_not_contact_df['Company Domain'].apply(clean_domain)

    # Create sets for faster lookups
    dnc_domains = set(do_not_contact_df['clean_domain'].dropna())
    dnc_companies = set(do_not_contact_df['clean_company'].dropna())
    print(f"Prepared **{len(dnc_domains)}** unique DNC domains and **{len(dnc_companies)}** unique DNC companies for lookup.")

    # --- Match Logic ---
    print("\nApplying exact match logic...")
    contacts_df['is_domain_exact_match_dnc'] = contacts_df['clean_domain'].isin(dnc_domains)
    contacts_df['is_company_exact_match_dnc'] = contacts_df['clean_company'].isin(dnc_companies)

    print("\nApplying fuzzy match logic (this is the most intensive step)...")
    # Using explicit loop with tqdm for fuzzy matching, as it returns multiple values
    fuzzy_results = []
    for name in tqdm(contacts_df['clean_company'], desc="Fuzzy Matching Companies", total=len(contacts_df)):
        fuzzy_results.append(get_fuzzy_score_and_match(name, dnc_companies))

    # Assign results back to DataFrame
    contacts_df['company_fuzzy_score'] = [score for score, _ in fuzzy_results]
    contacts_df['matched_dnc_company_name'] = [matched_name for _, matched_name in fuzzy_results]

    # Create a dictionary for quick lookup of original domain by cleaned company name from DNC list
    # We use 'Company Domain' from the original do_not_contact_df to get the original domain,
    # mapping it to the 'clean_company' name from the DNC list.
    dnc_company_to_domain_map = do_not_contact_df.set_index('clean_company')['Company Domain'].to_dict()

    # Function to get the domain for a matched DNC company name
    def get_matched_domain(matched_company_name, dnc_map):
        # Look up using the cleaned matched name to get the original domain
        if pd.isna(matched_company_name) or matched_company_name not in dnc_map:
            return None
        return dnc_map.get(matched_company_name)

    print("\nRetrieving domains for matched DNC companies...")
    contacts_df['matched_dnc_company_domain'] = [
        get_matched_domain(name, dnc_company_to_domain_map)
        for name in tqdm(contacts_df['matched_dnc_company_name'], desc="Getting Matched DNC Domains", total=len(contacts_df))
    ]


    # Determine fuzzy match status based on threshold
    contacts_df['is_company_fuzzy_match_dnc'] = (
        (contacts_df['company_fuzzy_score'] >= CONFIG["fuzzy_threshold_match"]) &
        (~contacts_df['is_company_exact_match_dnc'])
    )

    # Determine companies that need review
    contacts_df['company_needs_review'] = (
        contacts_df['company_fuzzy_score'].between(CONFIG["fuzzy_threshold_review"], CONFIG["fuzzy_threshold_match"] - 0.001)
    )

    # Final 'do_not_contact' flag
    contacts_df['do_not_contact'] = (
        contacts_df['is_domain_exact_match_dnc'] |
        contacts_df['is_company_exact_match_dnc'] |
        contacts_df['is_company_fuzzy_match_dnc']
    )

    round_fuzzy_match_scores = contacts_df['company_fuzzy_score'].round(2)
    contacts_df['company_fuzzy_score'] = round_fuzzy_match_scores

    # Select and save the relevant columns
    output_columns = [
        'Company Name',
        'Company Domain',
        'matched_dnc_company_name',
        'matched_dnc_company_domain', 
        'is_domain_exact_match_dnc',
        'is_company_exact_match_dnc',
        'is_company_fuzzy_match_dnc',
        'company_fuzzy_score',
        'do_not_contact',
        'company_needs_review'
    ]
    output_df = contacts_df[output_columns]

    output_df.to_csv(CONFIG["output_file"], index=False)
    print("\n----------------------------------------------------------------------------------------------------------")
    print(f"\n✅ Done! Output saved to '{CONFIG['output_file']}'")
    print(f"\nSummary: {output_df['do_not_contact'].sum()} contacts flagged as 'Do Not Contact'.")
    print(f"         {output_df['company_needs_review'].sum()} contacts flagged as 'Needs Review'.")
    print("\n🗑️  Remember to delete all contact data from your personal computer and clear out your recycle bin!")
    print("\n----------------------------------------------------------------------------------------------------------")

if __name__ == "__main__":
    main()
