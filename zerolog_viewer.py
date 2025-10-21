#!/usr/bin/env python3
"""
ZeroLog Viewer - A cross-platform GUI application for viewing JSONL logs.
"""

import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
from typing import List, Dict, Any, Optional
import os


class ZeroLogViewer:
    """Main application class for the ZeroLog Viewer."""
    
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
    
    def __init__(self, root: tk.Tk):
        """Initialize the ZeroLog Viewer application."""
        self.root = root
        self.root.title("ZeroLog Viewer")
        self.root.geometry("1200x700")
        
        self.logs: List[Dict[str, Any]] = []
        self.filtered_logs: List[Dict[str, Any]] = []
        self.columns: List[str] = []
        self.sort_column: Optional[str] = None
        self.sort_reverse: bool = False
        
        self._create_ui()
        
    def _create_ui(self):
        """Create the user interface."""
        # Menu bar
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open JSONL File", command=self.open_file)
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
        self.search_var.trace('w', lambda *args: self.apply_search())
        search_entry = ttk.Entry(toolbar, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=2)
        
        # Clear search button
        ttk.Button(toolbar, text="Clear", command=self.clear_search).pack(side=tk.LEFT, padx=2)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready. Open a JSONL file to begin.")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Main frame with treeview and scrollbars
        main_frame = ttk.Frame(self.root)
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
        
        # Bind column click for sorting
        self.tree.bind('<Button-1>', self.on_tree_click)
        
        # Configure tags for level colors
        for level, color in self.LEVEL_COLORS.items():
            self.tree.tag_configure(level, foreground=color)
    
    def open_file(self):
        """Open a JSONL file dialog and load the file."""
        filename = filedialog.askopenfilename(
            title="Open JSONL File",
            filetypes=[
                ("JSONL files", "*.jsonl"),
                ("JSON files", "*.json"),
                ("Log files", "*.log"),
                ("All files", "*.*")
            ]
        )
        
        if filename:
            self.load_file(filename)
    
    def load_file(self, filename: str):
        """Load and parse a JSONL file."""
        try:
            self.logs = []
            self.columns = []
            
            self.status_var.set(f"Loading {os.path.basename(filename)}...")
            self.root.update_idletasks()
            
            # Read and parse JSONL file
            with open(filename, 'r', encoding='utf-8') as f:
                line_num = 0
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            log_entry = json.loads(line)
                            self.logs.append(log_entry)
                            
                            # Collect all unique column names
                            for key in log_entry.keys():
                                if key not in self.columns:
                                    self.columns.append(key)
                            
                            line_num += 1
                        except json.JSONDecodeError as e:
                            print(f"Warning: Skipping invalid JSON on line {line_num}: {e}")
            
            if not self.logs:
                messagebox.showwarning("No Data", "No valid log entries found in the file.")
                self.status_var.set("Ready. Open a JSONL file to begin.")
                return
            
            # Sort columns: time first, level second, then others alphabetically
            priority_columns = ['time', 'level', 'message']
            sorted_columns = []
            for col in priority_columns:
                if col in self.columns:
                    sorted_columns.append(col)
                    self.columns.remove(col)
            sorted_columns.extend(sorted(self.columns))
            self.columns = sorted_columns
            
            # Index by time (sort logs by time)
            self.logs.sort(key=lambda x: x.get('time', ''))
            
            # Display the logs
            self.display_logs()
            
            self.status_var.set(f"Loaded {len(self.logs)} log entries from {os.path.basename(filename)}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file: {str(e)}")
            self.status_var.set("Error loading file.")
    
    def display_logs(self):
        """Display logs in the treeview."""
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
            for log in self.logs[:100]:  # Sample first 100 entries for performance
                value = str(log.get(col, ''))
                max_width = max(max_width, len(value) * 7)
            
            # Set width with reasonable limits
            width = min(max(max_width, 80), 400)
            self.tree.column(col, width=width, minwidth=50, stretch=True)
        
        # Use filtered logs if search is active, otherwise use all logs
        logs_to_display = self.filtered_logs if self.search_var.get() else self.logs
        
        # Insert log entries
        for log in logs_to_display:
            values = [log.get(col, '') for col in self.columns]
            level = str(log.get('level', '')).lower()
            tag = level if level in self.LEVEL_COLORS else ''
            self.tree.insert('', tk.END, values=values, tags=(tag,))
    
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
    
    def apply_search(self):
        """Apply search filter to logs."""
        search_text = self.search_var.get().lower()
        
        if not search_text:
            self.filtered_logs = []
            self.display_logs()
            self.status_var.set(f"Showing all {len(self.logs)} log entries")
            return
        
        # Filter logs containing search text in any field
        self.filtered_logs = []
        for log in self.logs:
            for value in log.values():
                if search_text in str(value).lower():
                    self.filtered_logs.append(log)
                    break
        
        self.display_logs()
        self.status_var.set(f"Found {len(self.filtered_logs)} of {len(self.logs)} log entries")
    
    def clear_search(self):
        """Clear the search filter."""
        self.search_var.set('')
    
    def on_tree_click(self, event):
        """Handle clicks on the treeview."""
        region = self.tree.identify_region(event.x, event.y)
        if region == "heading":
            column = self.tree.identify_column(event.x)
            if column:
                col_index = int(column.replace('#', '')) - 1
                if 0 <= col_index < len(self.columns):
                    self.sort_by_column(self.columns[col_index])


def main():
    """Main entry point for the application."""
    root = tk.Tk()
    app = ZeroLogViewer(root)
    root.mainloop()


if __name__ == "__main__":
    main()
