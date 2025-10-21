#!/usr/bin/env python3
"""
ZeroLog Viewer - A cross-platform GUI application for viewing JSONL logs.
"""

import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD
from datetime import datetime
from typing import List, Dict, Any, Optional
import os
import threading


class LogTab:
    """Represents a single tab with log data."""
    
    # Color mapping for different log levels
    LEVEL_COLORS = {
        'debug': '#A0A0A0',  # Gray
        'info': '#4A90E2',   # Blue
        'warn': '#F5A623',   # Orange
        'warning': '#F5A623', # Orange
        'error': '#E74C3C',  # Red
        'fatal': '#8B0000',  # Dark Red
        'panic': '#8B0000',  # Dark Red
    }
    
    def __init__(self, parent_notebook: ttk.Notebook, filename: str, app_instance):
        """Initialize a log tab."""
        self.parent_notebook = parent_notebook
        self.filename = filename
        self.app = app_instance
        self.logs: List[Dict[str, Any]] = []
        self.filtered_logs: List[Dict[str, Any]] = []
        self.all_logs: List[Dict[str, Any]] = []  # Store all logs before date filtering
        self.columns: List[str] = []
        self.sort_column: Optional[str] = None
        self.sort_reverse: bool = False
        self.search_debounce_id: Optional[str] = None
        self.page_size = 1000  # Number of items to display at once
        self.current_page = 0
        
        # Create tab frame
        self.frame = ttk.Frame(parent_notebook)
        parent_notebook.add(self.frame, text=os.path.basename(filename))
        
        self._create_tab_ui()
    
    def _create_tab_ui(self):
        """Create the UI for this tab."""
        # Filter frame at top
        filter_frame = ttk.Frame(self.frame, padding="5")
        filter_frame.pack(side=tk.TOP, fill=tk.X)
        
        # Date range filter
        ttk.Label(filter_frame, text="From:").pack(side=tk.LEFT, padx=2)
        self.date_from_var = tk.StringVar()
        date_from_entry = ttk.Entry(filter_frame, textvariable=self.date_from_var, width=20)
        date_from_entry.pack(side=tk.LEFT, padx=2)
        
        ttk.Label(filter_frame, text="To:").pack(side=tk.LEFT, padx=2)
        self.date_to_var = tk.StringVar()
        date_to_entry = ttk.Entry(filter_frame, textvariable=self.date_to_var, width=20)
        date_to_entry.pack(side=tk.LEFT, padx=2)
        
        ttk.Button(filter_frame, text="Apply Date Filter", command=self.apply_date_filter).pack(side=tk.LEFT, padx=2)
        ttk.Button(filter_frame, text="Clear Date Filter", command=self.clear_date_filter).pack(side=tk.LEFT, padx=2)
        
        # Main frame with treeview and scrollbars
        main_frame = ttk.Frame(self.frame)
        main_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Scrollbars
        vsb = ttk.Scrollbar(main_frame, orient="vertical")
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        
        hsb = ttk.Scrollbar(main_frame, orient="horizontal")
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Treeview for displaying logs
        self.tree = ttk.Treeview(main_frame, yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)
        
        # Bind scrolling for lazy loading
        self.tree.bind('<MouseWheel>', self.on_scroll)
        self.tree.bind('<Button-4>', self.on_scroll)
        self.tree.bind('<Button-5>', self.on_scroll)
        
        # Configure tags for level colors
        for level, color in self.LEVEL_COLORS.items():
            self.tree.tag_configure(level, foreground=color)
        
        # Status label at bottom
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_label = ttk.Label(self.frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_label.pack(side=tk.BOTTOM, fill=tk.X)


class ZeroLogViewer:
    """Main application class for the ZeroLog Viewer."""
    
    def __init__(self, root: TkinterDnD.Tk):
        """Initialize the ZeroLog Viewer application."""
        self.root = root
        self.root.title("ZeroLog Viewer")
        self.root.geometry("1200x700")
        
        self.tabs: List[LogTab] = []
        
        self._create_ui()
        
        # Enable drag and drop
        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind('<<Drop>>', self.on_drop)
        
    def _create_ui(self):
        """Create the user interface."""
        # Menu bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open JSONL File", command=self.open_file)
        file_menu.add_command(label="Close Current Tab", command=self.close_current_tab)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Toolbar frame
        toolbar = ttk.Frame(self.root, padding="5")
        toolbar.pack(side=tk.TOP, fill=tk.X)
        
        # Open button
        ttk.Button(toolbar, text="Open File", command=self.open_file).pack(side=tk.LEFT, padx=2)
        
        # Search frame
        ttk.Label(toolbar, text="Search:").pack(side=tk.LEFT, padx=(10, 2))
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self.debounced_search())
        search_entry = ttk.Entry(toolbar, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=2)
        
        # Clear search button
        ttk.Button(toolbar, text="Clear", command=self.clear_search).pack(side=tk.LEFT, padx=2)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready. Open a JSONL file or drag and drop files here.")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.notebook.bind('<<NotebookTabChanged>>', self.on_tab_changed)
        
        self.search_debounce_id: Optional[str] = None
    
    def on_drop(self, event):
        """Handle drag and drop files."""
        files = self.root.tk.splitlist(event.data)
        for file_path in files:
            # Remove curly braces if present (Windows)
            file_path = file_path.strip('{}')
            if os.path.isfile(file_path):
                self.load_file(file_path)
    
    def on_tab_changed(self, event):
        """Handle tab change event."""
        # Update status bar when switching tabs
        current_tab = self.get_current_tab()
        if current_tab:
            self.status_var.set(current_tab.status_var.get())
    
    def get_current_tab(self) -> Optional[LogTab]:
        """Get the currently active tab."""
        try:
            current_index = self.notebook.index(self.notebook.select())
            if 0 <= current_index < len(self.tabs):
                return self.tabs[current_index]
        except:
            pass
        return None
    
    def close_current_tab(self):
        """Close the currently active tab."""
        current_tab = self.get_current_tab()
        if current_tab:
            tab_index = self.tabs.index(current_tab)
            self.notebook.forget(tab_index)
            self.tabs.remove(current_tab)
            if not self.tabs:
                self.status_var.set("Ready. Open a JSONL file or drag and drop files here.")
    
    def debounced_search(self):
        """Debounce search input to avoid too many updates."""
        if self.search_debounce_id:
            self.root.after_cancel(self.search_debounce_id)
        self.search_debounce_id = self.root.after(300, self.apply_search)  # 300ms debounce
    
    def apply_search(self):
        """Apply search to current tab."""
        current_tab = self.get_current_tab()
        if current_tab:
            current_tab.apply_search(self.search_var.get())
    
    def clear_search(self):
        """Clear the search filter."""
        self.search_var.set('')
    
    def open_file(self):
        """Open a JSONL file dialog and load the file."""
        filenames = filedialog.askopenfilenames(
            title="Open JSONL File(s)",
            filetypes=[
                ("JSONL files", "*.jsonl"),
                ("JSON files", "*.json"),
                ("Log files", "*.log"),
                ("All files", "*.*")
            ]
        )
        
        for filename in filenames:
            if filename:
                self.load_file(filename)
    
    def load_file(self, filename: str):
        """Load and parse a JSONL file in a new tab."""
        # Check if file is already open
        for tab in self.tabs:
            if tab.filename == filename:
                # Switch to existing tab
                tab_index = self.tabs.index(tab)
                self.notebook.select(tab_index)
                return
        
        # Create new tab
        tab = LogTab(self.notebook, filename, self)
        self.tabs.append(tab)
        
        # Load file in background thread
        self.status_var.set(f"Loading {os.path.basename(filename)}...")
        self.root.update_idletasks()
        
        thread = threading.Thread(target=self._load_file_thread, args=(tab, filename))
        thread.daemon = True
        thread.start()
    
    def _load_file_thread(self, tab: LogTab, filename: str):
        """Load file in background thread for better performance."""
        try:
            logs = []
            columns = set()
            
            # Read and parse JSONL file with streaming for large files
            with open(filename, 'r', encoding='utf-8') as f:
                line_num = 0
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            log_entry = json.loads(line)
                            logs.append(log_entry)
                            
                            # Collect all unique column names
                            columns.update(log_entry.keys())
                            
                            line_num += 1
                            
                            # Update status periodically
                            if line_num % 10000 == 0:
                                self.root.after(0, lambda n=line_num: self.status_var.set(
                                    f"Loading {os.path.basename(filename)}... ({n:,} entries)"
                                ))
                        except json.JSONDecodeError as e:
                            print(f"Warning: Skipping invalid JSON on line {line_num}: {e}")
            
            if not logs:
                self.root.after(0, lambda: messagebox.showwarning("No Data", "No valid log entries found in the file."))
                self.root.after(0, lambda: self.close_current_tab())
                return
            
            # Sort columns: time first, level second, then others alphabetically
            priority_columns = ['time', 'level', 'message']
            sorted_columns = []
            for col in priority_columns:
                if col in columns:
                    sorted_columns.append(col)
                    columns.discard(col)
            sorted_columns.extend(sorted(columns))
            
            tab.columns = sorted_columns
            tab.all_logs = logs
            tab.logs = logs.copy()
            
            # Index by time (sort logs by time)
            tab.logs.sort(key=lambda x: x.get('time', ''))
            
            # Display the logs on main thread
            self.root.after(0, lambda: self._finalize_load(tab))
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to load file: {str(e)}"))
            self.root.after(0, lambda: self.close_current_tab())
    
    def _finalize_load(self, tab: LogTab):
        """Finalize loading on the main thread."""
        tab.display_logs()
        tab.status_var.set(f"Loaded {len(tab.logs):,} log entries from {os.path.basename(tab.filename)}")
        self.status_var.set(tab.status_var.get())
    
    def display_logs(self):
        """Display logs in the treeview with pagination for performance."""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Configure columns
        self.tree['columns'] = self.columns
        self.tree['show'] = 'headings'
        
        # Configure column headings and widths
        for col in self.columns:
            self.tree.heading(col, text=col, command=lambda c=col: self.sort_by_column(c))
            
            # Calculate automatic width based on column name and content
            max_width = len(col) * 8  # Start with header width
            sample_logs = (self.filtered_logs if self.filtered_logs else self.logs)[:100]
            for log in sample_logs:  # Sample first 100 entries for performance
                value = str(log.get(col, ''))
                max_width = max(max_width, len(value) * 7)
            
            # Set width with reasonable limits
            width = min(max(max_width, 80), 400)
            self.tree.column(col, width=width, minwidth=50, stretch=True)
        
        # Use filtered logs if search is active, otherwise use all logs
        logs_to_display = self.filtered_logs if self.filtered_logs else self.logs
        
        # Display only first page for performance
        end_index = min(self.page_size, len(logs_to_display))
        for log in logs_to_display[:end_index]:
            values = [log.get(col, '') for col in self.columns]
            level = str(log.get('level', '')).lower()
            tag = level if level in self.LEVEL_COLORS else ''
            self.tree.insert('', tk.END, values=values, tags=(tag,))
        
        # Update status
        total = len(logs_to_display)
        if end_index < total:
            self.status_var.set(f"Showing {end_index:,} of {total:,} log entries (scroll for more)")
        else:
            self.status_var.set(f"Showing all {total:,} log entries")
        self.current_page = 0
    
    def on_scroll(self, event):
        """Load more items when scrolling near bottom."""
        # Check if scrolled near bottom
        if self.tree.yview()[1] > 0.9:  # 90% scrolled
            self.load_more_items()
    
    def load_more_items(self):
        """Load more items into the tree for lazy loading."""
        logs_to_display = self.filtered_logs if self.filtered_logs else self.logs
        current_count = len(self.tree.get_children())
        
        if current_count >= len(logs_to_display):
            return  # All items loaded
        
        # Load next page
        start_index = current_count
        end_index = min(start_index + self.page_size, len(logs_to_display))
        
        for log in logs_to_display[start_index:end_index]:
            values = [log.get(col, '') for col in self.columns]
            level = str(log.get('level', '')).lower()
            tag = level if level in self.LEVEL_COLORS else ''
            self.tree.insert('', tk.END, values=values, tags=(tag,))
        
        # Update status
        total = len(logs_to_display)
        if end_index < total:
            self.status_var.set(f"Showing {end_index:,} of {total:,} log entries (scroll for more)")
        else:
            self.status_var.set(f"Showing all {total:,} log entries")
    
    def sort_by_column(self, column: str):
        """Sort the treeview by the specified column."""
        # Toggle sort direction if same column clicked
        if self.sort_column == column:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_column = column
            self.sort_reverse = False
        
        # Sort the logs
        def sort_key(log):
            value = log.get(column, '')
            # Try to parse as number or date for proper sorting
            if column == 'time':
                try:
                    return datetime.fromisoformat(str(value).replace('Z', '+00:00'))
                except:
                    return value
            try:
                return float(value)
            except:
                return str(value).lower()
        
        self.logs.sort(key=sort_key, reverse=self.sort_reverse)
        
        # Re-display
        self.display_logs()
        
        # Update status
        direction = "descending" if self.sort_reverse else "ascending"
        self.status_var.set(f"Sorted by '{column}' ({direction})")
    
    def apply_search(self, search_text: str):
        """Apply search filter to logs."""
        search_text = search_text.lower()
        
        if not search_text:
            self.filtered_logs = []
            self.display_logs()
            self.status_var.set(f"Showing all {len(self.logs):,} log entries")
            return
        
        # Filter logs containing search text in any field
        self.filtered_logs = []
        for log in self.logs:
            for value in log.values():
                if search_text in str(value).lower():
                    self.filtered_logs.append(log)
                    break
        
        self.display_logs()
        self.status_var.set(f"Found {len(self.filtered_logs):,} of {len(self.logs):,} log entries")
    
    def apply_date_filter(self):
        """Apply date range filter to logs."""
        date_from_str = self.date_from_var.get().strip()
        date_to_str = self.date_to_var.get().strip()
        
        if not date_from_str and not date_to_str:
            messagebox.showinfo("Date Filter", "Please specify at least one date (from or to)")
            return
        
        try:
            date_from = None
            date_to = None
            
            if date_from_str:
                date_from = datetime.fromisoformat(date_from_str.replace('Z', '+00:00'))
            
            if date_to_str:
                date_to = datetime.fromisoformat(date_to_str.replace('Z', '+00:00'))
            
            # Filter logs by date range
            filtered = []
            for log in self.all_logs:
                time_str = log.get('time', '')
                if not time_str:
                    continue
                
                try:
                    log_time = datetime.fromisoformat(str(time_str).replace('Z', '+00:00'))
                    
                    if date_from and log_time < date_from:
                        continue
                    if date_to and log_time > date_to:
                        continue
                    
                    filtered.append(log)
                except:
                    # Include logs with unparseable dates
                    filtered.append(log)
            
            self.logs = filtered
            self.filtered_logs = []
            self.display_logs()
            
            date_range = []
            if date_from:
                date_range.append(f"from {date_from_str}")
            if date_to:
                date_range.append(f"to {date_to_str}")
            
            self.status_var.set(f"Date filtered: {len(self.logs):,} entries {' '.join(date_range)}")
            
        except Exception as e:
            messagebox.showerror("Date Filter Error", f"Invalid date format: {str(e)}\nUse ISO 8601 format (e.g., 2025-10-20T17:19:16Z)")
    
    def clear_date_filter(self):
        """Clear the date range filter."""
        self.date_from_var.set('')
        self.date_to_var.set('')
        self.logs = self.all_logs.copy()
        self.filtered_logs = []
        self.display_logs()
        self.status_var.set(f"Date filter cleared. Showing all {len(self.logs):,} entries")


def main():
    """Main entry point for the application."""
    try:
        root = TkinterDnD.Tk()
    except:
        # Fallback if tkinterdnd2 is not installed
        print("Warning: tkinterdnd2 not installed. Drag and drop will not work.")
        print("Install with: pip install tkinterdnd2")
        root = tk.Tk()
    
    app = ZeroLogViewer(root)
    root.mainloop()


if __name__ == "__main__":
    main()
