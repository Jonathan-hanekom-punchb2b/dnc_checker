import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import queue
import os
from core_logic import process_dnc_check, CONFIG
from typing import Dict, Any

class DNCCheckerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("DNC Checker")
        self.root.geometry("600x700")
        self.root.resizable(True, True)
        
        # Initialize variables
        self.contacts_file = tk.StringVar()
        self.exclusions_file = tk.StringVar()
        self.output_file = tk.StringVar(value=CONFIG["output_file"])
        self.processing = False
        
        # Create queue for thread communication
        self.progress_queue = queue.Queue()
        
        # Create the GUI
        self.create_widgets()
        
        # Start queue monitoring
        self.check_queue()
    
    def create_widgets(self):
        """Create and layout all GUI widgets"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="DNC Checker", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # File selection section
        file_frame = ttk.LabelFrame(main_frame, text="File Selection", padding="10")
        file_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        file_frame.columnconfigure(1, weight=1)
        
        # Sourced Accounts File
        ttk.Label(file_frame, text="Sourced Accounts File:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        ttk.Entry(file_frame, textvariable=self.contacts_file, state="readonly").grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 5), pady=(0, 5))
        ttk.Button(file_frame, text="Browse...", command=self.browse_contacts_file).grid(row=0, column=2, pady=(0, 5))
        
        # Exclusions File
        ttk.Label(file_frame, text="Exclusions File:").grid(row=1, column=0, sticky=tk.W, pady=(0, 5))
        ttk.Entry(file_frame, textvariable=self.exclusions_file, state="readonly").grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(5, 5), pady=(0, 5))
        ttk.Button(file_frame, text="Browse...", command=self.browse_exclusions_file).grid(row=1, column=2, pady=(0, 5))
        
        # Output File
        ttk.Label(file_frame, text="Output File:").grid(row=2, column=0, sticky=tk.W)
        ttk.Entry(file_frame, textvariable=self.output_file).grid(row=2, column=1, sticky=(tk.W, tk.E), padx=(5, 5))
        ttk.Button(file_frame, text="Browse...", command=self.browse_output_file).grid(row=2, column=2)
        
        # Process button
        self.process_button = ttk.Button(main_frame, text="Check Files", command=self.start_processing, style="Accent.TButton")
        self.process_button.grid(row=2, column=0, columnspan=3, pady=10)
        
        # Progress section
        progress_frame = ttk.LabelFrame(main_frame, text="Progress", padding="10")
        progress_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        progress_frame.columnconfigure(0, weight=1)
        
        # Status label
        self.status_label = ttk.Label(progress_frame, text="Ready")
        self.status_label.grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.progress_bar.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Progress text area
        self.progress_text = scrolledtext.ScrolledText(progress_frame, height=8, state='disabled')
        self.progress_text.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Results section
        results_frame = ttk.LabelFrame(main_frame, text="Results", padding="10")
        results_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        results_frame.columnconfigure(0, weight=1)
        
        # Results text
        self.results_text = scrolledtext.ScrolledText(results_frame, height=6, state='disabled')
        self.results_text.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # Configure grid weights for resizing
        main_frame.rowconfigure(3, weight=1)
        main_frame.rowconfigure(4, weight=1)
        progress_frame.rowconfigure(2, weight=1)
        results_frame.rowconfigure(0, weight=1)
    
    def browse_contacts_file(self):
        """Browse for contacts CSV file"""
        filename = filedialog.askopenfilename(
            title="Select Sourced Accounts File",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if filename:
            self.contacts_file.set(filename)
    
    def browse_exclusions_file(self):
        """Browse for exclusions CSV file"""
        filename = filedialog.askopenfilename(
            title="Select Exclusions File",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if filename:
            self.exclusions_file.set(filename)
    
    def browse_output_file(self):
        """Browse for output CSV file location"""
        filename = filedialog.asksaveasfilename(
            title="Save Output File As",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if filename:
            self.output_file.set(filename)
    
    def validate_files(self):
        """Validate that required files are selected"""
        if not self.contacts_file.get():
            messagebox.showerror("Error", "Please select a Sourced Accounts file.")
            return False
        if not self.exclusions_file.get():
            messagebox.showerror("Error", "Please select an Exclusions file.")
            return False
        if not self.output_file.get():
            messagebox.showerror("Error", "Please specify an output file location.")
            return False
        
        # Check if files exist
        if not os.path.exists(self.contacts_file.get()):
            messagebox.showerror("Error", f"Contacts file not found: {self.contacts_file.get()}")
            return False
        if not os.path.exists(self.exclusions_file.get()):
            messagebox.showerror("Error", f"Exclusions file not found: {self.exclusions_file.get()}")
            return False
        
        return True
    
    def start_processing(self):
        """Start the DNC checking process in a separate thread"""
        if self.processing:
            return
        
        if not self.validate_files():
            return
        
        # Clear previous results
        self.clear_text_widget(self.progress_text)
        self.clear_text_widget(self.results_text)
        
        # Update UI state
        self.processing = True
        self.process_button.config(state='disabled', text="Processing...")
        self.status_label.config(text="Starting DNC check...")
        self.progress_bar.start()
        
        # Start processing thread
        thread = threading.Thread(target=self.process_files, daemon=True)
        thread.start()
    
    def process_files(self):
        """Process files in background thread"""
        try:
            # Progress callback that puts messages in queue
            def gui_progress_callback(message):
                self.progress_queue.put(('progress', message))
            
            # Process the files
            summary = process_dnc_check(
                contacts_file=self.contacts_file.get(),
                exclusions_file=self.exclusions_file.get(),
                output_file=self.output_file.get(),
                config=CONFIG,
                progress_callback=gui_progress_callback,
                use_tqdm=False  # Disable tqdm for GUI mode
            )
            
            # Put success result in queue
            self.progress_queue.put(('success', summary))
            
        except FileNotFoundError as e:
            self.progress_queue.put(('error', f"File Error: {str(e)}"))
        except Exception as e:
            self.progress_queue.put(('error', f"Processing Error: {str(e)}"))
    
    def check_queue(self):
        """Check for messages from the processing thread"""
        try:
            while True:
                message_type, data = self.progress_queue.get_nowait()
                
                if message_type == 'progress':
                    self.update_progress(data)
                elif message_type == 'success':
                    self.processing_complete(data)
                elif message_type == 'error':
                    self.processing_error(data)
                    
        except queue.Empty:
            pass
        
        # Schedule next check
        self.root.after(100, self.check_queue)
    
    def update_progress(self, message):
        """Update progress display with new message"""
        self.append_to_text_widget(self.progress_text, message + "\n")
        self.status_label.config(text="Processing...")
    
    def processing_complete(self, summary):
        """Handle successful completion"""
        self.processing = False
        self.process_button.config(state='normal', text="Check Files")
        self.progress_bar.stop()
        self.status_label.config(text="Complete!")
        
        # Display results
        results_message = f"""✅ Done! Output saved to '{self.output_file.get()}'

Summary: {summary['do_not_contact_count']} contacts flagged as 'Do Not Contact'.
         {summary['needs_review_count']} contacts flagged as 'Needs Review'.

🗑️  Remember to delete all contact data from your personal computer and clear out your recycle bin!
"""
        
        self.append_to_text_widget(self.results_text, results_message)
        
        # Show success message
        messagebox.showinfo("Success", f"Processing complete!\n\n{summary['do_not_contact_count']} contacts flagged as 'Do Not Contact'\n{summary['needs_review_count']} contacts flagged as 'Needs Review'")
    
    def processing_error(self, error_message):
        """Handle processing errors"""
        self.processing = False
        self.process_button.config(state='normal', text="Check Files")
        self.progress_bar.stop()
        self.status_label.config(text="Error occurred")
        
        # Display error in results
        self.append_to_text_widget(self.results_text, f"❌ Error: {error_message}\n")
        
        # Show error message
        messagebox.showerror("Error", error_message)
    
    def clear_text_widget(self, widget):
        """Clear text widget content"""
        widget.config(state='normal')
        widget.delete(1.0, tk.END)
        widget.config(state='disabled')
    
    def append_to_text_widget(self, widget, text):
        """Append text to widget and scroll to bottom"""
        widget.config(state='normal')
        widget.insert(tk.END, text)
        widget.see(tk.END)
        widget.config(state='disabled')

def main():
    """Main function to run the GUI"""
    root = tk.Tk()
    
    # Set up styling
    style = ttk.Style()
    
    # Try to use a modern theme if available
    available_themes = style.theme_names()
    if 'clam' in available_themes:
        style.theme_use('clam')
    elif 'alt' in available_themes:
        style.theme_use('alt')
    
    # Create and run the application
    app = DNCCheckerGUI(root)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
        root.quit()

if __name__ == "__main__":
    main()