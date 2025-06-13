#!/usr/bin/env python3
"""
HubSpot Duplicate Company Detector

This script identifies potential duplicate companies in HubSpot exports by analyzing
Company names and domains using fuzzy matching and domain similarity algorithms.

Usage:
    python duplicate_detector.py

Expected CSV columns:
    - Company name
    - Company Domain Name

Output:
    - Original CSV with additional columns for duplicate detection results
    - Summary report of findings
"""

import pandas as pd
import sys
import os
from datetime import datetime
from typing import Dict, List, Optional
import argparse

# Import our utility functions
from duplicate_utils import (
    find_potential_duplicates,
    create_duplicate_clusters,
    format_potential_matches,
    clean_company_name,
    clean_domain
)


def load_hubspot_data(file_path: str) -> pd.DataFrame:
    """
    Load HubSpot export CSV and validate required columns.
    """
    try:
        print(f"📁 Loading data from: {file_path}")
        df = pd.read_csv(file_path)
        
        # Validate required columns
        required_columns = ['Company name', 'Company Domain Name']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            print(f"❌ Missing required columns: {missing_columns}")
            print(f"Available columns: {list(df.columns)}")
            sys.exit(1)
        
        print(f"✅ Loaded {len(df)} companies")
        print(f"📊 Columns: {list(df.columns)}")
        
        return df
        
    except FileNotFoundError:
        print(f"❌ File not found: {file_path}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error loading file: {str(e)}")
        sys.exit(1)


def preprocess_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and preprocess the data before duplicate detection.
    """
    print("🧹 Preprocessing data...")
    
    # Create a copy to avoid modifying original
    processed_df = df.copy()
    
    # Add cleaned versions for analysis (but keep originals for output)
    processed_df['_cleaned_name'] = processed_df['Company name'].apply(clean_company_name)
    processed_df['_cleaned_domain'] = processed_df['Company Domain Name'].apply(clean_domain)
    
    # Remove rows with empty essential data
    initial_count = len(processed_df)
    processed_df = processed_df.dropna(subset=['Company name', 'Company Domain Name'])
    processed_df = processed_df[
        (processed_df['Company name'].str.strip() != '') & 
        (processed_df['Company Domain Name'].str.strip() != '')
    ]
    
    removed_count = initial_count - len(processed_df)
    if removed_count > 0:
        print(f"⚠️  Removed {removed_count} rows with missing essential data")
    
    print(f"✅ Preprocessed {len(processed_df)} companies")
    return processed_df


def detect_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Main duplicate detection logic.
    """
    print("\n🔍 Starting duplicate detection...")
    
    # Find potential duplicates
    matches = find_potential_duplicates(df)
    
    if not matches:
        print("✅ No potential duplicates found!")
        # Still add the columns for consistency
        df['duplicate_flag'] = 'No'
        df['confidence_score'] = 0
        df['cluster_id'] = ''
        df['potential_matches'] = ''
        df['match_reason'] = ''
        df['review_priority'] = 'None'
        return df
    
    # Create clusters of related duplicates
    clusters = create_duplicate_clusters(matches)
    
    # Prepare output columns
    df['duplicate_flag'] = 'No'
    df['confidence_score'] = 0
    df['cluster_id'] = ''
    df['potential_matches'] = ''
    df['match_reason'] = ''
    df['review_priority'] = 'None'
    
    # Convert dataframe to list for easier access
    companies = df.to_dict('records')
    
    # Map each company to its highest confidence match
    company_max_confidence = {}
    company_matches = {}
    
    for match in matches:
        for idx in [match['index1'], match['index2']]:
            if idx not in company_max_confidence or match['confidence_score'] > company_max_confidence[idx]:
                company_max_confidence[idx] = match['confidence_score']
                company_matches[idx] = match
    
    # Update dataframe with duplicate information
    for cluster_id, indices in clusters.items():
        for idx in indices:
            df.loc[idx, 'duplicate_flag'] = 'Yes'
            df.loc[idx, 'cluster_id'] = f"CLUSTER_{cluster_id:03d}"
            
            # Get the best match for this company
            if idx in company_matches:
                match = company_matches[idx]
                df.loc[idx, 'confidence_score'] = match['confidence_score']
                df.loc[idx, 'match_reason'] = match['match_reason']
                df.loc[idx, 'review_priority'] = match['priority']
            
            # Format potential matches
            potential_matches = format_potential_matches(idx, matches, companies)
            df.loc[idx, 'potential_matches'] = potential_matches
    
    # Generate summary statistics
    total_duplicates = len(df[df['duplicate_flag'] == 'Yes'])
    high_priority = len(df[df['review_priority'] == 'High'])
    medium_priority = len(df[df['review_priority'] == 'Medium'])
    low_priority = len(df[df['review_priority'] == 'Low'])
    
    print(f"\n📊 Duplicate Detection Results:")
    print(f"   Total companies analyzed: {len(df)}")
    print(f"   Companies flagged as duplicates: {total_duplicates}")
    print(f"   High priority matches: {high_priority}")
    print(f"   Medium priority matches: {medium_priority}")
    print(f"   Low priority matches: {low_priority}")
    print(f"   Duplicate clusters found: {len(clusters)}")
    
    return df


def generate_summary_report(df: pd.DataFrame, output_path: str) -> None:
    """
    Generate a summary report of duplicate detection results.
    """
    report_path = output_path.replace('.csv', '_summary.txt')
    
    with open(report_path, 'w') as f:
        f.write("HUBSPOT DUPLICATE DETECTION SUMMARY REPORT\n")
        f.write("=" * 50 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Overall statistics
        total_companies = len(df)
        duplicate_companies = len(df[df['duplicate_flag'] == 'Yes'])
        unique_clusters = len(df[df['cluster_id'] != '']['cluster_id'].unique())
        
        f.write("OVERALL STATISTICS:\n")
        f.write(f"  Total companies analyzed: {total_companies}\n")
        f.write(f"  Companies flagged as duplicates: {duplicate_companies}\n")
        f.write(f"  Percentage of duplicates: {(duplicate_companies/total_companies)*100:.1f}%\n")
        f.write(f"  Number of duplicate clusters: {unique_clusters}\n\n")
        
        # Priority breakdown
        f.write("PRIORITY BREAKDOWN:\n")
        priority_counts = df['review_priority'].value_counts()
        for priority, count in priority_counts.items():
            if priority != 'None':
                f.write(f"  {priority} priority: {count} companies\n")
        f.write("\n")
        
        # Confidence score distribution
        f.write("CONFIDENCE SCORE DISTRIBUTION:\n")
        duplicates_df = df[df['duplicate_flag'] == 'Yes']
        if len(duplicates_df) > 0:
            f.write(f"  Average confidence score: {duplicates_df['confidence_score'].mean():.1f}%\n")
            f.write(f"  Highest confidence score: {duplicates_df['confidence_score'].max()}%\n")
            f.write(f"  Lowest confidence score: {duplicates_df['confidence_score'].min()}%\n")
        f.write("\n")
        
        # Top clusters by size
        f.write("LARGEST DUPLICATE CLUSTERS:\n")
        if unique_clusters > 0:
            cluster_sizes = df[df['cluster_id'] != '']['cluster_id'].value_counts()
            top_clusters = cluster_sizes.head(10)
            
            for cluster, size in top_clusters.items():
                f.write(f"  {cluster}: {size} companies\n")
                # Show the companies in this cluster
                cluster_companies = df[df['cluster_id'] == cluster][['Company name', 'Company Domain Name', 'confidence_score']]
                for _, company in cluster_companies.iterrows():
                    f.write(f"    - {company['Company name']} ({company['Company Domain Name']}) [{company['confidence_score']}%]\n")
                f.write("\n")
        
        f.write("\nRECOMMENDATIONS:\n")
        f.write("1. Start with HIGH priority matches - these are most likely true duplicates\n")
        f.write("2. Review MEDIUM priority matches carefully - may need manual verification\n")
        f.write("3. LOW priority matches should be spot-checked for false positives\n")
        f.write("4. Use the cluster_id to group related duplicates for efficient merging\n")
        f.write("5. Always verify before merging - check contact data, deal history, etc.\n")
    
    print(f"📄 Summary report saved to: {report_path}")


def save_results(df: pd.DataFrame, output_path: str) -> None:
    """
    Save the results to CSV file.
    """
    try:
        # Remove internal columns used for processing
        output_df = df.drop(columns=[col for col in df.columns if col.startswith('_')])
        
        # Reorder columns to put duplicate detection columns at the end
        original_columns = ['Company name', 'Company Domain Name']
        duplicate_columns = ['duplicate_flag', 'confidence_score', 'cluster_id', 
                           'potential_matches', 'match_reason', 'review_priority']
        
        # Get any other columns that might exist
        other_columns = [col for col in output_df.columns 
                        if col not in original_columns + duplicate_columns]
        
        # Reorder columns
        column_order = original_columns + other_columns + duplicate_columns
        output_df = output_df[[col for col in column_order if col in output_df.columns]]
        
        # Save to CSV
        output_df.to_csv(output_path, index=False)
        print(f"💾 Results saved to: {output_path}")
        
        # Generate summary report
        generate_summary_report(output_df, output_path)
        
    except Exception as e:
        print(f"❌ Error saving results: {str(e)}")
        sys.exit(1)


def main():
    """
    Main execution function.
    """
    parser = argparse.ArgumentParser(description='HubSpot Duplicate Company Detector')
    parser.add_argument('--input', '-i', 
                       help='Input CSV file path (default: hubspot_companies.csv)')
    parser.add_argument('--output', '-o', 
                       help='Output CSV file path (default: hubspot_companies_with_duplicates.csv)')
    
    args = parser.parse_args()
    
    # Set default file paths
    input_file = args.input or 'hubspot_companies.csv'
    output_file = args.output or 'hubspot_companies_with_duplicates.csv'
    
    print("🚀 HubSpot Duplicate Company Detector")
    print("=" * 40)
    print(f"Input file: {input_file}")
    print(f"Output file: {output_file}")
    print()
    
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"❌ Input file not found: {input_file}")
        print("\nPlease ensure you have:")
        print("1. Exported companies from HubSpot as CSV")
        print("2. Named the file 'hubspot_companies.csv' (or use --input flag)")
        print("3. Included columns: 'Company name', 'Company Domain Name'")
        sys.exit(1)
    
    try:
        # Load and preprocess data
        df = load_hubspot_data(input_file)
        df = preprocess_data(df)
        
        # Detect duplicates
        df_with_duplicates = detect_duplicates(df)
        
        # Save results
        save_results(df_with_duplicates, output_file)
        
        print(f"\n✅ Duplicate detection completed successfully!")
        print(f"📋 Next steps:")
        print(f"   1. Upload {output_file} to Google Drive")
        print(f"   2. Open in Google Sheets")
        print(f"   3. Filter by 'duplicate_flag' = 'Yes'")
        print(f"   4. Review flagged companies manually")
        print(f"   5. Merge duplicates in HubSpot UI")
        
    except KeyboardInterrupt:
        print("\n⚠️  Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()