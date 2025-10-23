import pandas as pd
import re
from rapidfuzz import process, fuzz
from tqdm.auto import tqdm
from typing import Callable, Optional, Tuple, Dict, Any

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
    if pd.isna(name):
        return ""
    name = str(name)  # Ensure name is a string
    name = _RE_COMPANY_SUFFIXES.sub('', name)
    return clean_text(name)

def clean_domain(domain):
    if pd.isna(domain):
        return ""
    # Ensure domain is treated as a string before cleaning
    domain_str = str(domain).replace("www.", "")
    return clean_text(domain_str)

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

# --- Core Processing Functions ---
def load_and_validate_files(contacts_file: str, exclusions_file: str, 
                          progress_callback: Optional[Callable[[str], None]] = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load and validate the contacts and exclusions CSV files.
    
    Args:
        contacts_file: Path to the contacts CSV file
        exclusions_file: Path to the exclusions CSV file
        progress_callback: Optional callback function for progress updates
    
    Returns:
        Tuple of (contacts_df, do_not_contact_df)
    
    Raises:
        FileNotFoundError: If required files are not found
        Exception: For other file loading errors
    """
    if progress_callback:
        progress_callback("Loading CSV files...")
    
    try:
        # Read CSV files with utf-8-sig encoding to handle BOM characters from Excel
        contacts_df = pd.read_csv(contacts_file, encoding='utf-8-sig')
        do_not_contact_df = pd.read_csv(exclusions_file, encoding='utf-8-sig')

        # Strip whitespace from column names to handle any padding issues
        contacts_df.columns = contacts_df.columns.str.strip()
        do_not_contact_df.columns = do_not_contact_df.columns.str.strip()

        # Validate required columns exist in contacts file
        required_contacts_columns = ['Company Name', 'Company Domain']
        missing_contacts_columns = [col for col in required_contacts_columns if col not in contacts_df.columns]
        if missing_contacts_columns:
            raise ValueError(
                f"Missing required columns in '{contacts_file}': {missing_contacts_columns}. "
                f"Available columns: {list(contacts_df.columns)}"
            )

        # Validate required columns exist in exclusions file
        required_exclusions_columns = ['Company Name', 'Company Domain']
        missing_exclusions_columns = [col for col in required_exclusions_columns if col not in do_not_contact_df.columns]
        if missing_exclusions_columns:
            raise ValueError(
                f"Missing required columns in '{exclusions_file}': {missing_exclusions_columns}. "
                f"Available columns: {list(do_not_contact_df.columns)}"
            )

        if progress_callback:
            progress_callback(f"Successfully loaded '{contacts_file}' containing **{len(contacts_df)}** companies to check and '{exclusions_file}' with **{len(do_not_contact_df)}** exclusion entries.")

        return contacts_df, do_not_contact_df

    except FileNotFoundError as e:
        error_msg = f"Error: Required file not found - {e.filename if hasattr(e, 'filename') else str(e)}. Please ensure '{contacts_file}' and '{exclusions_file}' exist in the current directory."
        raise FileNotFoundError(error_msg)
    except Exception as e:
        error_msg = f"An unexpected error occurred while loading files: {e}"
        raise Exception(error_msg)

def clean_contacts_data(contacts_df: pd.DataFrame, 
                       progress_callback: Optional[Callable[[str], None]] = None,
                       use_tqdm: bool = True) -> pd.DataFrame:
    """
    Clean the contacts data by normalizing company names and domains.
    
    Args:
        contacts_df: DataFrame containing contacts data
        progress_callback: Optional callback function for progress updates
        use_tqdm: Whether to use tqdm for progress bars (CLI mode)
    
    Returns:
        DataFrame with added clean_company and clean_domain columns
    """
    if progress_callback:
        progress_callback("Cleaning contacts data...")
    
    contacts_df = contacts_df.copy()
    
    if use_tqdm:
        # CLI mode with tqdm progress bars
        contacts_df['clean_company'] = [
            clean_company_name(name)
            for name in tqdm(contacts_df['Company Name'], desc="Cleaning Contact Company Names", total=len(contacts_df))
        ]
        contacts_df['clean_domain'] = [
            clean_domain(domain)
            for domain in tqdm(contacts_df['Company Domain'], desc="Cleaning Contact Company Domains", total=len(contacts_df))
        ]
    else:
        # GUI mode - use list comprehensions for reliability
        if progress_callback:
            progress_callback("Cleaning company names...")
        contacts_df['clean_company'] = [clean_company_name(name) for name in contacts_df['Company Name']]

        if progress_callback:
            progress_callback("Cleaning domains...")
        contacts_df['clean_domain'] = [clean_domain(domain) for domain in contacts_df['Company Domain']]
    
    return contacts_df

def clean_exclusions_data(do_not_contact_df: pd.DataFrame,
                         progress_callback: Optional[Callable[[str], None]] = None) -> pd.DataFrame:
    """
    Clean the exclusions data by normalizing company names and domains.
    
    Args:
        do_not_contact_df: DataFrame containing exclusions data
        progress_callback: Optional callback function for progress updates
    
    Returns:
        DataFrame with added clean_company and clean_domain columns
    """
    if progress_callback:
        progress_callback("Cleaning exclusion data...")
    
    do_not_contact_df = do_not_contact_df.copy()
    # For the exclusion data, standard apply is fine as it's usually smaller
    do_not_contact_df['clean_company'] = do_not_contact_df['Company Name'].apply(clean_company_name)
    do_not_contact_df['clean_domain'] = do_not_contact_df['Company Domain'].apply(clean_domain)
    
    return do_not_contact_df

def apply_exact_matching(contacts_df: pd.DataFrame, dnc_domains: set, dnc_companies: set,
                        progress_callback: Optional[Callable[[str], None]] = None) -> pd.DataFrame:
    """
    Apply exact matching logic for domains and company names.
    
    Args:
        contacts_df: DataFrame containing contacts data
        dnc_domains: Set of DNC domains for lookup
        dnc_companies: Set of DNC companies for lookup
        progress_callback: Optional callback function for progress updates
    
    Returns:
        DataFrame with exact match columns added
    """
    if progress_callback:
        progress_callback("Applying exact match logic...")
    
    contacts_df = contacts_df.copy()
    contacts_df['is_domain_exact_match_dnc'] = contacts_df['clean_domain'].isin(dnc_domains)
    contacts_df['is_company_exact_match_dnc'] = contacts_df['clean_company'].isin(dnc_companies)
    
    return contacts_df

def apply_fuzzy_matching(contacts_df: pd.DataFrame, dnc_companies: set,
                        progress_callback: Optional[Callable[[str], None]] = None,
                        use_tqdm: bool = True) -> pd.DataFrame:
    """
    Apply fuzzy matching logic for company names.
    
    Args:
        contacts_df: DataFrame containing contacts data
        dnc_companies: Set of DNC companies for fuzzy matching
        progress_callback: Optional callback function for progress updates
        use_tqdm: Whether to use tqdm for progress bars (CLI mode)
    
    Returns:
        DataFrame with fuzzy match columns added
    """
    if progress_callback:
        progress_callback("Applying fuzzy match logic (this is the most intensive step)...")
    
    contacts_df = contacts_df.copy()
    
    if use_tqdm:
        # CLI mode with tqdm - using explicit loop with tqdm for fuzzy matching, as it returns multiple values
        fuzzy_results = []
        for name in tqdm(contacts_df['clean_company'], desc="Fuzzy Matching Companies", total=len(contacts_df)):
            fuzzy_results.append(get_fuzzy_score_and_match(name, dnc_companies))
    else:
        # GUI mode - use list comprehension for reliability
        if progress_callback:
            progress_callback("Performing fuzzy matching...")
        fuzzy_results = [get_fuzzy_score_and_match(name, dnc_companies) for name in contacts_df['clean_company']]
    
    # Assign results back to DataFrame
    contacts_df['company_fuzzy_score'] = [score for score, _ in fuzzy_results]
    contacts_df['matched_dnc_company_name'] = [matched_name for _, matched_name in fuzzy_results]
    
    return contacts_df

def add_matched_domains(contacts_df: pd.DataFrame, do_not_contact_df: pd.DataFrame,
                       progress_callback: Optional[Callable[[str], None]] = None,
                       use_tqdm: bool = True) -> pd.DataFrame:
    """
    Add matched domain information for fuzzy-matched companies.
    
    Args:
        contacts_df: DataFrame containing contacts data with fuzzy matches
        do_not_contact_df: DataFrame containing exclusions data
        progress_callback: Optional callback function for progress updates
        use_tqdm: Whether to use tqdm for progress bars (CLI mode)
    
    Returns:
        DataFrame with matched domain column added
    """
    if progress_callback:
        progress_callback("Retrieving domains for matched DNC companies...")
    
    contacts_df = contacts_df.copy()
    
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
    
    if use_tqdm:
        # CLI mode with tqdm
        contacts_df['matched_dnc_company_domain'] = [
            get_matched_domain(name, dnc_company_to_domain_map)
            for name in tqdm(contacts_df['matched_dnc_company_name'], desc="Getting Matched DNC Domains", total=len(contacts_df))
        ]
    else:
        # GUI mode - use list comprehension for reliability
        if progress_callback:
            progress_callback("Getting matched domains...")
        contacts_df['matched_dnc_company_domain'] = [
            get_matched_domain(name, dnc_company_to_domain_map)
            for name in contacts_df['matched_dnc_company_name']
        ]
    
    return contacts_df

def finalize_matching_results(contacts_df: pd.DataFrame, config: Dict[str, Any],
                             progress_callback: Optional[Callable[[str], None]] = None) -> pd.DataFrame:
    """
    Finalize the matching results by applying thresholds and creating final flags.
    
    Args:
        contacts_df: DataFrame containing all matching data
        config: Configuration dictionary with thresholds
        progress_callback: Optional callback function for progress updates
    
    Returns:
        DataFrame with final matching columns
    """
    if progress_callback:
        progress_callback("Finalizing matching results...")
    
    contacts_df = contacts_df.copy()
    
    # Determine fuzzy match status based on threshold
    contacts_df['is_company_fuzzy_match_dnc'] = (
        (contacts_df['company_fuzzy_score'] >= config["fuzzy_threshold_match"]) &
        (~contacts_df['is_company_exact_match_dnc'])
    )
    
    # Determine companies that need review
    contacts_df['company_needs_review'] = (
        contacts_df['company_fuzzy_score'].between(config["fuzzy_threshold_review"], config["fuzzy_threshold_match"] - 0.001)
    )
    
    # Final 'do_not_contact' flag
    contacts_df['do_not_contact'] = (
        contacts_df['is_domain_exact_match_dnc'] |
        contacts_df['is_company_exact_match_dnc'] |
        contacts_df['is_company_fuzzy_match_dnc']
    )
    
    # Round fuzzy match scores
    round_fuzzy_match_scores = contacts_df['company_fuzzy_score'].round(2)
    contacts_df['company_fuzzy_score'] = round_fuzzy_match_scores
    
    return contacts_df

def generate_output(contacts_df: pd.DataFrame, output_file: str,
                   progress_callback: Optional[Callable[[str], None]] = None) -> Dict[str, int]:
    """
    Generate the output CSV file and return summary statistics.
    
    Args:
        contacts_df: DataFrame containing all processed data
        output_file: Path to save the output CSV
        progress_callback: Optional callback function for progress updates
    
    Returns:
        Dictionary containing summary statistics
    """
    if progress_callback:
        progress_callback(f"Saving results to '{output_file}'...")
    
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
    
    output_df.to_csv(output_file, index=False)
    
    # Generate summary statistics
    summary = {
        'total_contacts': len(output_df),
        'do_not_contact_count': output_df['do_not_contact'].sum(),
        'needs_review_count': output_df['company_needs_review'].sum()
    }
    
    return summary

def process_dnc_check(contacts_file: str, exclusions_file: str, output_file: str, 
                     config: Dict[str, Any], progress_callback: Optional[Callable[[str], None]] = None,
                     use_tqdm: bool = True) -> Dict[str, int]:
    """
    Main processing function that orchestrates the entire DNC checking process.
    
    Args:
        contacts_file: Path to the contacts CSV file
        exclusions_file: Path to the exclusions CSV file
        output_file: Path to save the output CSV
        config: Configuration dictionary
        progress_callback: Optional callback function for progress updates
        use_tqdm: Whether to use tqdm for progress bars (CLI mode)
    
    Returns:
        Dictionary containing summary statistics
    
    Raises:
        FileNotFoundError: If required files are not found
        Exception: For other processing errors
    """
    # Load and validate files
    contacts_df, do_not_contact_df = load_and_validate_files(contacts_file, exclusions_file, progress_callback)
    
    # Clean data
    contacts_df = clean_contacts_data(contacts_df, progress_callback, use_tqdm)
    do_not_contact_df = clean_exclusions_data(do_not_contact_df, progress_callback)
    
    # Create sets for faster lookups
    dnc_domains = set(do_not_contact_df['clean_domain'].dropna())
    dnc_companies = set(do_not_contact_df['clean_company'].dropna())
    
    if progress_callback:
        progress_callback(f"Prepared **{len(dnc_domains)}** unique DNC domains and **{len(dnc_companies)}** unique DNC companies for lookup.")
    
    # Apply matching logic
    contacts_df = apply_exact_matching(contacts_df, dnc_domains, dnc_companies, progress_callback)
    contacts_df = apply_fuzzy_matching(contacts_df, dnc_companies, progress_callback, use_tqdm)
    contacts_df = add_matched_domains(contacts_df, do_not_contact_df, progress_callback, use_tqdm)
    contacts_df = finalize_matching_results(contacts_df, config, progress_callback)
    
    # Generate output and return summary
    summary = generate_output(contacts_df, output_file, progress_callback)
    
    return summary