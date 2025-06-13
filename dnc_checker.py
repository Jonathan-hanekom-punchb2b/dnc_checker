import pandas as pd
import re
from rapidfuzz import process, fuzz
from tqdm.auto import tqdm # Import tqdm for progress bars
from core_logic import process_dnc_check, CONFIG

# --- Main Script Logic ---
def main():
    print("--- Starting DNC Check Script ---")

    def cli_progress_callback(message):
        """Progress callback for CLI mode - simply prints messages"""
        print(message)

    try:
        # Process using the core logic with CLI-style progress
        summary = process_dnc_check(
            contacts_file=CONFIG["contacts_file"],
            exclusions_file=CONFIG["exclusions_file"], 
            output_file=CONFIG["output_file"],
            config=CONFIG,
            progress_callback=cli_progress_callback,
            use_tqdm=True  # Enable tqdm progress bars for CLI
        )
        
        # Print final summary
        print("\n----------------------------------------------------------------------------------------------------------")
        print(f"\n✅ Done! Output saved to '{CONFIG['output_file']}'")
        print(f"\nSummary: {summary['do_not_contact_count']} contacts flagged as 'Do Not Contact'.")
        print(f"         {summary['needs_review_count']} contacts flagged as 'Needs Review'.")
        print("\n🗑️  Remember to delete all contact data from your personal computer and clear out your recycle bin!")
        print("\n----------------------------------------------------------------------------------------------------------")
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return

if __name__ == "__main__":
    main()