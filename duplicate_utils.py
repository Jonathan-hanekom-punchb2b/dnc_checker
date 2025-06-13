"""
Utility functions for duplicate detection that leverage existing dnc_checker functionality.
This module imports and extends the cleaning functions from the existing codebase.
"""

import re
import pandas as pd
from rapidfuzz import fuzz
from collections import defaultdict
from typing import List, Dict, Tuple, Set
import urllib.parse

# Try to import existing functions from dnc_checker
try:
    from dnc_checker import clean_company_name, clean_domain
    print("✅ Successfully imported existing cleaning functions from dnc_checker")
except ImportError:
    print("⚠️  Could not import from dnc_checker, using fallback functions")
    
    # Fallback implementations based on dnc_checker patterns
    def clean_company_name(name: str) -> str:
        """Clean company name by removing punctuation and common suffixes."""
        if pd.isna(name) or not isinstance(name, str):
            return ""
        
        # Convert to lowercase
        cleaned = name.lower().strip()
        
        # Remove punctuation
        cleaned = re.sub(r'[^\w\s]', ' ', cleaned)
        
        # Remove common company suffixes
        suffixes = ['inc', 'ltd', 'llc', 'corp', 'pty', 'company', 'co', 'the']
        for suffix in suffixes:
            cleaned = re.sub(rf'\b{suffix}\b', '', cleaned)
        
        # Normalize whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        return cleaned
    
    def clean_domain(domain: str) -> str:
        """Clean domain by normalizing format."""
        if pd.isna(domain) or not isinstance(domain, str):
            return ""
        
        # Convert to lowercase and strip
        cleaned = domain.lower().strip()
        
        # Remove protocol if present
        cleaned = re.sub(r'^https?://', '', cleaned)
        
        # Remove www prefix
        cleaned = re.sub(r'^www\.', '', cleaned)
        
        # Remove trailing slash
        cleaned = cleaned.rstrip('/')
        
        return cleaned


def extract_base_domain(domain: str) -> str:
    """
    Extract the base domain, handling country-specific TLDs and subdomains.
    Examples: 
        'bbc.com' -> 'bbc'
        'bbc.co.uk' -> 'bbc'   
        'shop.apple.com' -> 'apple'
    """
    if not domain:
        return ""
    
    cleaned = clean_domain(domain)
    
    # Handle common country-specific TLDs
    country_tlds = [
        '.co.uk', '.co.za', '.com.au', '.co.in', '.co.jp',
        '.com.br', '.com.mx', '.co.kr', '.com.sg', '.co.nz'
    ]
    
    # Remove country-specific TLDs first
    for tld in country_tlds:
        if cleaned.endswith(tld):
            cleaned = cleaned[:-len(tld)]
            break
    else:
        # Remove standard TLD (.com, .org, .net, etc.)
        if '.' in cleaned:
            cleaned = cleaned.rsplit('.', 1)[0]
    
    # Handle subdomains - take the last part before TLD
    # This block ensures that 'shop.apple' becomes 'apple'
    if '.' in cleaned:
        parts = cleaned.split('.')
        if len(parts) >= 2:
            cleaned = parts[-1]
    
    return cleaned


def calculate_domain_similarity(domain1: str, domain2: str) -> Tuple[int, str]:
    """
    Calculate similarity between two domains with specific logic for domain variations.
    Returns (similarity_score, reason)
    """
    if not domain1 or not domain2:
        return 0, "Empty domain"
    
    # These domains are already cleaned by preprocess_data
    # So we don't need to call clean_domain here again, but we use the input directly.
    # The input to this function should be the cleaned domains from the DataFrame.
    
    # Exact match
    if domain1 == domain2: # Use the already cleaned inputs
        return 100, "Exact domain match"
    
    # Extract base domains
    base1 = extract_base_domain(domain1)
    base2 = extract_base_domain(domain2)
    
    # Base domain exact match (handles bbc.com vs bbc.co.uk)
    if base1 == base2 and base1:
        return 95, f"Same base domain: {base1}"
    
    # Fuzzy match on full domains
    domain_similarity = fuzz.ratio(domain1, domain2) # Use the already cleaned inputs
    if domain_similarity >= 85:
        return domain_similarity, f"Similar domains ({domain_similarity}%)"
    
    # Fuzzy match on base domains
    if base1 and base2:
        base_similarity = fuzz.ratio(base1, base2)
        if base_similarity >= 90:
            return base_similarity - 5, f"Similar base domains ({base_similarity}%)"
    
    return 0, "No significant domain similarity"


def calculate_name_similarity(name1: str, name2: str) -> Tuple[int, str]:
    """
    Calculate similarity between company names using existing fuzzy matching logic.
    Returns (similarity_score, reason)
    """
    if not name1 or not name2:
        return 0, "Empty name"
    
    # These names are already cleaned by preprocess_data
    # So we don't need to call clean_company_name here again, but we use the input directly.
    # The input to this function should be the cleaned names from the DataFrame.
    
    # Exact match
    if name1 == name2: # Use the already cleaned inputs
        return 100, "Exact name match"
    
    # Use token sort ratio (same as dnc_checker)
    similarity = fuzz.token_sort_ratio(name1, name2) # Use the already cleaned inputs
    
    if similarity >= 95:
        return similarity, f"Very similar names ({similarity}%)"
    elif similarity >= 85:
        return similarity, f"Similar names ({similarity}%)"
    elif similarity >= 70:
        return similarity, f"Moderately similar names ({similarity}%)"
    else:
        return similarity, f"Low name similarity ({similarity}%)"


def calculate_combined_confidence(domain_score: int, name_score: int, 
                                  domain_reason: str, name_reason: str) -> Tuple[int, str, str]:
    """
    Calculate overall confidence score and priority level for duplicate detection.
    Returns (confidence_score, priority_level, combined_reason)
    """
    # Weight domain similarity higher for duplicate detection
    domain_weight = 0.6
    name_weight = 0.4
    
    combined_score = int((domain_score * domain_weight) + (name_score * name_weight))
    combined_reason = f"{domain_reason} + {name_reason}"
    
    # Determine priority level
    if combined_score >= 90:
        priority = "High"
    elif combined_score >= 70:
        priority = "Medium"
    elif combined_score >= 50: # Keep minimum threshold of 50 for consideration
        priority = "Low"
    else:
        priority = "No Match"
    
    # Special cases for high confidence
    if domain_score >= 95 and name_score >= 85:
        combined_score = max(combined_score, 95)
        priority = "High"
    elif domain_score == 100:  # Exact domain match
        combined_score = max(combined_score, 90)
        priority = "High"
    
    return combined_score, priority, combined_reason


def find_potential_duplicates(df: pd.DataFrame) -> List[Dict]:
    """
    Find potential duplicate pairs in the dataframe.
    Returns list of potential duplicate matches with scores and reasons.
    """
    potential_duplicates = []
    
    # Convert to list for easier iteration
    # IMPORTANT: Ensure the DataFrame passed here includes '_cleaned_name' and '_cleaned_domain'
    companies = df.to_dict('records')
    
    print(f"🔍 Analyzing {len(companies)} companies for duplicates...")
    
    # Compare each company with every other company
    for i in range(len(companies)):
        for j in range(i + 1, len(companies)):
            company1 = companies[i]
            company2 = companies[j]
            
            # --- DEBUG FIX: Use cleaned data for comparisons ---
            cleaned_name1 = company1.get('_cleaned_name', '')
            cleaned_domain1 = company1.get('_cleaned_domain', '')
            cleaned_name2 = company2.get('_cleaned_name', '')
            cleaned_domain2 = company2.get('_cleaned_domain', '')

            # Skip if essential cleaned data is missing or empty
            if not cleaned_name1 or not cleaned_domain1 or \
               not cleaned_name2 or not cleaned_domain2:
                continue
            # --- END FIX ---
            
            # Calculate similarities using the *cleaned* names and domains
            domain_score, domain_reason = calculate_domain_similarity(
                cleaned_domain1, 
                cleaned_domain2
            )
            
            name_score, name_reason = calculate_name_similarity(
                cleaned_name1, 
                cleaned_name2
            )
            
            # Calculate combined confidence
            confidence, priority, combined_reason = calculate_combined_confidence(
                domain_score, name_score, domain_reason, name_reason
            )
            
            # Only keep matches above threshold
            if confidence >= 50:  # Minimum threshold for consideration
                potential_duplicates.append({
                    'index1': i,
                    'index2': j,
                    'company1_name': company1['Company name'], # Keep original for output
                    'company1_domain': company1['Company Domain Name'], # Keep original for output
                    'company2_name': company2['Company name'], 
                    'company2_domain': company2['Company Domain Name'],
                    'confidence_score': confidence,
                    'priority': priority,
                    'domain_score': domain_score,
                    'name_score': name_score,
                    'match_reason': combined_reason
                })
    
    print(f"✅ Found {len(potential_duplicates)} potential duplicate pairs")
    return potential_duplicates


def create_duplicate_clusters(matches: List[Dict]) -> Dict[int, Set[int]]:
    """
    Group related duplicates into clusters.
    Returns dictionary mapping cluster_id to set of company indices.
    """
    clusters = defaultdict(set)
    index_to_cluster = {}
    cluster_counter = 0
    
    for match in matches:
        idx1, idx2 = match['index1'], match['index2']
        
        # Check if either index is already in a cluster
        cluster1 = index_to_cluster.get(idx1)
        cluster2 = index_to_cluster.get(idx2)
        
        if cluster1 is not None and cluster2 is not None:
            # Both are in clusters - merge if different
            if cluster1 != cluster2:
                # Merge cluster2 into cluster1
                clusters[cluster1].update(clusters[cluster2])
                # Update all indices in cluster2 to point to cluster1
                for idx in clusters[cluster2]:
                    index_to_cluster[idx] = cluster1
                del clusters[cluster2]
        elif cluster1 is not None:
            # idx1 is in a cluster, add idx2
            clusters[cluster1].add(idx2)
            index_to_cluster[idx2] = cluster1
        elif cluster2 is not None:
            # idx2 is in a cluster, add idx1
            clusters[cluster2].add(idx1)
            index_to_cluster[idx1] = cluster2
        else:
            # Neither is in a cluster, create new one
            clusters[cluster_counter] = {idx1, idx2}
            index_to_cluster[idx1] = cluster_counter
            index_to_cluster[idx2] = cluster_counter
            cluster_counter += 1
    
    print(f"📊 Created {len(clusters)} duplicate clusters")
    return dict(clusters)


def format_potential_matches(company_idx: int, matches: List[Dict], 
                             companies: List[Dict]) -> str:
    """
    Format the potential matches for a given company into a readable string.
    """
    related_matches = [m for m in matches if company_idx in [m['index1'], m['index2']]]
    
    if not related_matches:
        return ""
    
    match_strings = []
    for match in related_matches:
        other_idx = match['index2'] if match['index1'] == company_idx else match['index1']
        other_company = companies[other_idx]
        match_strings.append(
            f"{other_company['Company name']} ({other_company['Company Domain Name']}) " # Use original names for display
            f"[{match['confidence_score']}%]"
        )
    
    return "; ".join(match_strings)