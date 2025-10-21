#!/usr/bin/env python3
"""
ZeroLog Viewer - A cross-platform GUI application for viewing JSONL logs.
"""

import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    HAS_DND = True
except ImportError:
    print("Warning: tkinterdnd2 not found. Drag-and-drop functionality will be disabled.")
    print("Install with: pip install tkinterdnd2")
    HAS_DND = False
    DND_FILES = None
    TkinterDnD = None
from datetime import datetime
from typing import List, Dict, Any, Optional, Set
import os
import threading
import platform
from pathlib import Path


class ConfigManager:
    """Manages configuration settings for the application."""
    
    @staticmethod
    def get_config_dir() -> Path:
        """Get the configuration directory based on the platform."""
        system = platform.system()
        if system == "Windows":
            base_dir = Path(os.environ.get('APPDATA', Path.home()))
        elif system == "Darwin":  # macOS
            base_dir = Path.home() / "Library" / "Application Support"
        else:  # Linux and others
            base_dir = Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / ".config"))
        
        config_dir = base_dir / "zerolog_viewer"
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir
    
    @staticmethod
    def get_config_file() -> Path:
        """Get the configuration file path."""
        return ConfigManager.get_config_dir() / "config.json"
    
    @staticmethod
    def get_default_config() -> Dict[str, Any]:
        """Get the default configuration."""
        return {
            "visible_columns": ["time", "level", "message", "url"],
            "window_geometry": "1200x700",
            "level_colors": {
                "debug": "#000000",
                "info": "#000000",
                "warn": "#000000",
                "warning": "#000000",
                "error": "#000000",
                "fatal": "#000000",
                "panic": "#000000"
            }
        }
    
    @staticmethod
    def load_config() -> Dict[str, Any]:
        """Load configuration from file."""
        config_file = ConfigManager.get_config_file()
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Failed to load config: {e}")
        
        # Return default configuration
        return ConfigManager.get_default_config()
    
    @staticmethod
    def save_config(config: Dict[str, Any]):
        """Save configuration to file."""
        try:
            config_file = ConfigManager.get_config_file()
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to save config: {e}")


class LogTab:
    """Represents a single tab with log data."""
    
    def __init__(self, parent_notebook: ttk.Notebook, filename: str, app_instance):
        """Initialize a log tab."""
        self.parent_notebook = parent_notebook
        self.filename = filename
        self.app = app_instance
        self.logs: List[Dict[str, Any]] = []
        self.filtered_logs: List[Dict[str, Any]] = []
        self.all_logs: List[Dict[str, Any]] = []  # Store all logs before date filtering
        self.columns: List[str] = []
        self.all_columns: List[str] = []  # Store all columns including hidden ones
        self.visible_columns: List[str] = []  # Only columns to display
        self.sort_column: Optional[str] = None
        self.sort_reverse: bool = False
        self.search_debounce_id: Optional[str] = None
        self.page_size = 1000  # Number of items to display at once
        self.current_page = 0
        self.sidebar_visible = False
        self.selected_log = None
        
        # Get level colors from config
        self.level_colors = self.app.config.get("level_colors", {
            "debug": "#000000",
            "info": "#000000",
            "warn": "#000000",
            "warning": "#000000",
            "error": "#000000",
            "fatal": "#000000",
            "panic": "#000000"
        })
        
        # Create tab frame
        self.frame = ttk.Frame(parent_notebook)
        parent_notebook.add(self.frame, text=os.path.basename(filename))
        
        self._create_tab_ui()
    
    def _create_tab_ui(self):
        """Create the UI for this tab."""
        # Create main paned window (for log list and sidebar)
        self.paned_window = ttk.PanedWindow(self.frame, orient=tk.HORIZONTAL)
        self.paned_window.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # Left panel for logs
        left_panel = ttk.Frame(self.paned_window)
        self.paned_window.add(left_panel, weight=1)
        
        # Filter frame at top
        filter_frame = ttk.Frame(left_panel, padding="5")
        filter_frame.pack(side=tk.TOP, fill=tk.X)
        
        # Date range filter with date picker buttons
        ttk.Label(filter_frame, text="From:").pack(side=tk.LEFT, padx=2)
        self.date_from_var = tk.StringVar()
        date_from_entry = ttk.Entry(filter_frame, textvariable=self.date_from_var, width=20)
        date_from_entry.pack(side=tk.LEFT, padx=2)
        ttk.Button(filter_frame, text="📅", width=3, command=lambda: self.pick_date('from')).pack(side=tk.LEFT, padx=1)
        
        ttk.Label(filter_frame, text="To:").pack(side=tk.LEFT, padx=2)
        self.date_to_var = tk.StringVar()
        date_to_entry = ttk.Entry(filter_frame, textvariable=self.date_to_var, width=20)
        date_to_entry.pack(side=tk.LEFT, padx=2)
        ttk.Button(filter_frame, text="📅", width=3, command=lambda: self.pick_date('to')).pack(side=tk.LEFT, padx=1)
        
        ttk.Button(filter_frame, text="Apply Date Filter", command=self.apply_date_filter).pack(side=tk.LEFT, padx=2)
        ttk.Button(filter_frame, text="Clear Date Filter", command=self.clear_date_filter).pack(side=tk.LEFT, padx=2)
        
        # Main frame with treeview and scrollbars
        main_frame = ttk.Frame(left_panel)
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
        
        # Bind single click to show metadata in sidebar
        self.tree.bind('<ButtonRelease-1>', self.on_log_click)
        
        # Bind keyboard navigation to update sidebar
        self.tree.bind('<Up>', self.on_key_navigation)
        self.tree.bind('<Down>', self.on_key_navigation)
        self.tree.bind('<Prior>', self.on_key_navigation)  # Page Up
        self.tree.bind('<Next>', self.on_key_navigation)   # Page Down
        self.tree.bind('<Home>', self.on_key_navigation)
        self.tree.bind('<End>', self.on_key_navigation)
        
        # Configure tags for level colors
        for level, color in self.level_colors.items():
            self.tree.tag_configure(level, foreground=color)
        
        # Create sidebar frame (initially hidden)
        self.sidebar_frame = ttk.Frame(self.paned_window, width=300)
        self.sidebar_visible = False
    
    def pick_date(self, field_type: str):
        """Pick a date and populate the date field."""
        # Get earliest and latest dates from logs
        if not self.all_logs:
            messagebox.showinfo("No Data", "Please load a file first.")
            return
        
        dates = []
        for log in self.all_logs:
            time_str = log.get('time', '')
            if time_str:
                try:
                    dt = datetime.fromisoformat(str(time_str).replace('Z', '+00:00'))
                    dates.append(dt)
                except:
                    pass
        
        if not dates:
            messagebox.showinfo("No Dates", "No valid dates found in logs.")
            return
        
        # Create date picker dialog
        dialog = tk.Toplevel(self.app.root)
        dialog.title(f"Select {'From' if field_type == 'from' else 'To'} Date")
        dialog.geometry("350x300")
        dialog.transient(self.app.root)
        dialog.grab_set()
        
        # Get min and max dates from logs
        min_date = min(dates)
        max_date = max(dates)
        
        # Default to min for 'from' and max for 'to'
        default_date = min_date if field_type == 'from' else max_date
        
        # Frame for date/time inputs
        input_frame = ttk.Frame(dialog, padding="20")
        input_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(input_frame, text="Select Date and Time:", font=('TkDefaultFont', 10, 'bold')).pack(pady=(0, 10))
        
        # Date inputs
        date_frame = ttk.Frame(input_frame)
        date_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(date_frame, text="Year:").grid(row=0, column=0, sticky='e', padx=5, pady=2)
        year_var = tk.StringVar(value=str(default_date.year))
        year_entry = ttk.Entry(date_frame, textvariable=year_var, width=8)
        year_entry.grid(row=0, column=1, sticky='w', padx=5, pady=2)
        
        ttk.Label(date_frame, text="Month:").grid(row=1, column=0, sticky='e', padx=5, pady=2)
        month_var = tk.StringVar(value=str(default_date.month).zfill(2))
        month_entry = ttk.Entry(date_frame, textvariable=month_var, width=8)
        month_entry.grid(row=1, column=1, sticky='w', padx=5, pady=2)
        
        ttk.Label(date_frame, text="Day:").grid(row=2, column=0, sticky='e', padx=5, pady=2)
        day_var = tk.StringVar(value=str(default_date.day).zfill(2))
        day_entry = ttk.Entry(date_frame, textvariable=day_var, width=8)
        day_entry.grid(row=2, column=1, sticky='w', padx=5, pady=2)
        
        # Time inputs
        ttk.Label(date_frame, text="Hour:").grid(row=3, column=0, sticky='e', padx=5, pady=2)
        hour_var = tk.StringVar(value=str(default_date.hour).zfill(2))
        hour_entry = ttk.Entry(date_frame, textvariable=hour_var, width=8)
        hour_entry.grid(row=3, column=1, sticky='w', padx=5, pady=2)
        
        ttk.Label(date_frame, text="Minute:").grid(row=4, column=0, sticky='e', padx=5, pady=2)
        minute_var = tk.StringVar(value=str(default_date.minute).zfill(2))
        minute_entry = ttk.Entry(date_frame, textvariable=minute_var, width=8)
        minute_entry.grid(row=4, column=1, sticky='w', padx=5, pady=2)
        
        ttk.Label(date_frame, text="Second:").grid(row=5, column=0, sticky='e', padx=5, pady=2)
        second_var = tk.StringVar(value=str(default_date.second).zfill(2))
        second_entry = ttk.Entry(date_frame, textvariable=second_var, width=8)
        second_entry.grid(row=5, column=1, sticky='w', padx=5, pady=2)
        
        # Info label
        info_label = ttk.Label(input_frame, 
                              text=f"Available range:\n{min_date.strftime('%Y-%m-%d %H:%M:%S')}\n to \n{max_date.strftime('%Y-%m-%d %H:%M:%S')}", 
                              font=('TkDefaultFont', 8))
        info_label.pack(pady=10)
        
        # Button frame
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=20, pady=10)
        
        def apply_date():
            try:
                year = int(year_var.get())
                month = int(month_var.get())
                day = int(day_var.get())
                hour = int(hour_var.get())
                minute = int(minute_var.get())
                second = int(second_var.get())
                
                selected_date = datetime(year, month, day, hour, minute, second)
                date_str = selected_date.strftime('%Y-%m-%dT%H:%M:%S') + 'Z'
                
                if field_type == 'from':
                    self.date_from_var.set(date_str)
                else:
                    self.date_to_var.set(date_str)
                
                dialog.destroy()
            except ValueError as e:
                messagebox.showerror("Invalid Date", f"Please enter valid date/time values: {str(e)}", parent=dialog)
        
        ttk.Button(button_frame, text="Apply", command=apply_date).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def on_log_click(self, event):
        """Show metadata sidebar when a log entry is clicked."""
        # Get selected item
        item = self.tree.selection()
        if not item:
            return
        
        # Get the item index
        item_id = item[0]
        item_index = self.tree.index(item_id)
        
        # Get the log entry
        logs_to_display = self.filtered_logs if self.filtered_logs else self.logs
        if item_index >= len(logs_to_display):
            return
        
        log_entry = logs_to_display[item_index]
        self.selected_log = log_entry
        
        # Show sidebar with metadata
        self.show_sidebar()
    
    def on_key_navigation(self, event):
        """Update sidebar when navigating with keyboard."""
        # Schedule update after key event is processed
        self.tree.after(10, self.update_sidebar_from_selection)
    
    def update_sidebar_from_selection(self):
        """Update sidebar based on current selection."""
        item = self.tree.selection()
        if not item:
            return
        
        # Get the item index
        item_id = item[0]
        item_index = self.tree.index(item_id)
        
        # Get the log entry
        logs_to_display = self.filtered_logs if self.filtered_logs else self.logs
        if item_index >= len(logs_to_display):
            return
        
        log_entry = logs_to_display[item_index]
        self.selected_log = log_entry
        
        # Update sidebar if it's visible
        if self.sidebar_visible:
            self.show_sidebar()
    
    def show_sidebar(self):
        """Show the metadata sidebar."""
        if not self.selected_log:
            return
        
        # Add sidebar to paned window if not already shown
        if not self.sidebar_visible:
            self.paned_window.add(self.sidebar_frame, weight=0)
            self.sidebar_visible = True
        
        # Clear existing sidebar content
        for widget in self.sidebar_frame.winfo_children():
            widget.destroy()
        
        # Create sidebar header
        header_frame = ttk.Frame(self.sidebar_frame)
        header_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        ttk.Label(header_frame, text="Log Details", font=('TkDefaultFont', 10, 'bold')).pack(side=tk.LEFT)
        ttk.Button(header_frame, text="✕", width=3, command=self.hide_sidebar).pack(side=tk.RIGHT)
        
        # Create scrollable frame for metadata
        canvas = tk.Canvas(self.sidebar_frame)
        scrollbar = ttk.Scrollbar(self.sidebar_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add metadata content - show all fields
        # Get system default background color
        default_bg = self.frame.cget('background')
        
        for col in self.all_columns:
            if col in self.selected_log:
                value = self.selected_log[col]
                frame = ttk.Frame(scrollable_frame)
                frame.pack(fill=tk.X, pady=2)
                
                # Use a Text widget for selectable/copyable content
                label_text = tk.Text(frame, height=1, wrap=tk.NONE, relief=tk.FLAT, 
                                    font=('TkDefaultFont', 8, 'bold'), 
                                    bg=default_bg)
                label_text.insert('1.0', f"{col}:")
                label_text.config(state=tk.DISABLED)
                label_text.pack(anchor='w')
                
                # Use a Text widget for the value to make it selectable
                value_text = tk.Text(frame, wrap=tk.WORD, relief=tk.FLAT,
                                    bg=default_bg)
                value_text.insert('1.0', str(value))
                value_text.config(state=tk.DISABLED)
                # Calculate height based on content
                lines = str(value).count('\n') + 1
                value_text.config(height=min(lines, 10))
                value_text.pack(anchor='w', fill=tk.X, padx=(10, 0))
    
    def hide_sidebar(self):
        """Hide the metadata sidebar."""
        if self.sidebar_visible:
            self.paned_window.forget(self.sidebar_frame)
            self.sidebar_visible = False

    def display_logs(self):
        """Display logs in the treeview with pagination for performance."""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Use only visible columns for display
        display_columns = self.visible_columns if self.visible_columns else self.columns
        
        # Configure columns
        self.tree['columns'] = display_columns
        self.tree['show'] = 'headings'
        
        # Configure column headings and widths
        for col in display_columns:
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
            values = [log.get(col, '') for col in display_columns]
            level = str(log.get('level', '')).lower()
            tag = level if level in self.level_colors else ''
            self.tree.insert('', tk.END, values=values, tags=(tag,))
        
        # Update status
        total = len(logs_to_display)
        if end_index < total:
            self.app.status_var.set(f"Showing {end_index:,} of {total:,} log entries (scroll for more)")
        else:
            self.app.status_var.set(f"Showing all {total:,} log entries")
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
        
        display_columns = self.visible_columns if self.visible_columns else self.columns
        
        for log in logs_to_display[start_index:end_index]:
            values = [log.get(col, '') for col in display_columns]
            level = str(log.get('level', '')).lower()
            tag = level if level in self.level_colors else ''
            self.tree.insert('', tk.END, values=values, tags=(tag,))
        
        # Update status
        total = len(logs_to_display)
        if end_index < total:
            self.app.status_var.set(f"Showing {end_index:,} of {total:,} log entries (scroll for more)")
        else:
            self.app.status_var.set(f"Showing all {total:,} log entries")
    
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
        self.app.status_var.set(f"Sorted by '{column}' ({direction})")
    
    def apply_search(self, search_text: str):
        """Apply search filter to logs."""
        search_text = search_text.lower()
        
        if not search_text:
            self.filtered_logs = []
            self.display_logs()
            self.app.status_var.set(f"Showing all {len(self.logs):,} log entries")
            return
        
        # Filter logs containing search text in any field
        self.filtered_logs = []
        for log in self.logs:
            for value in log.values():
                if search_text in str(value).lower():
                    self.filtered_logs.append(log)
                    break
        
        self.display_logs()
        self.app.status_var.set(f"Found {len(self.filtered_logs):,} of {len(self.logs):,} log entries")
    
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
            
            self.app.status_var.set(f"Date filtered: {len(self.logs):,} entries {' '.join(date_range)}")
            
        except Exception as e:
            messagebox.showerror("Date Filter Error", f"Invalid date format: {str(e)}\nUse ISO 8601 format (e.g., 2025-10-20T17:19:16Z)")
    
    def clear_date_filter(self):
        """Clear the date range filter."""
        self.date_from_var.set('')
        self.date_to_var.set('')
        self.logs = self.all_logs.copy()
        self.filtered_logs = []
        self.display_logs()
        self.app.status_var.set(f"Date filter cleared. Showing all {len(self.logs):,} entries")




class ZeroLogViewer:
    """Main application class for the ZeroLog Viewer."""
    
    def __init__(self, root):
        """Initialize the ZeroLog Viewer application."""
        self.root = root
        self.root.title("ZeroLog Viewer")
        
        # Load configuration
        self.config = ConfigManager.load_config()
        self.root.geometry(self.config.get("window_geometry", "1200x700"))
        
        self.tabs: List[LogTab] = []
        
        self._create_ui()
        
        # Enable drag and drop if available
        if HAS_DND:
            self.root.drop_target_register(DND_FILES)
            self.root.dnd_bind('<<Drop>>', self.on_drop)
        
        # Save configuration on window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
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
        
        # Settings menu
        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Settings", menu=settings_menu)
        settings_menu.add_command(label="Configure Visible Columns...", command=self.configure_columns)
        settings_menu.add_command(label="Configure Level Colors...", command=self.configure_colors)
        settings_menu.add_separator()
        settings_menu.add_command(label="Reset to Default Settings", command=self.reset_to_defaults)
        
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
        # Status bar is now centralized - no need to update from tabs
        pass
    
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
    
    def configure_columns(self):
        """Open dialog to configure visible columns."""
        current_tab = self.get_current_tab()
        if not current_tab:
            messagebox.showinfo("No File Open", "Please open a file first to configure columns.")
            return
        
        if not current_tab.all_columns:
            messagebox.showinfo("No Columns", "No columns available to configure.")
            return
        
        # Create dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Configure Visible Columns")
        dialog.geometry("400x500")
        
        # Instructions
        ttk.Label(dialog, text="Select columns to display:", font=('TkDefaultFont', 10, 'bold')).pack(pady=10)
        
        # Frame with scrollbar
        frame = ttk.Frame(dialog)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        scrollbar = ttk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Canvas for checkboxes
        canvas = tk.Canvas(frame, yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=canvas.yview)
        
        checkbox_frame = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=checkbox_frame, anchor='nw')
        
        # Create checkbox variables
        checkbox_vars = {}
        for col in current_tab.all_columns:
            var = tk.BooleanVar(value=col in current_tab.visible_columns)
            checkbox_vars[col] = var
            cb = ttk.Checkbutton(checkbox_frame, text=col, variable=var)
            cb.pack(anchor='w', padx=5, pady=2)
        
        # Update scrollregion
        checkbox_frame.update_idletasks()
        canvas.config(scrollregion=canvas.bbox('all'))
        
        # Button frame
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def apply_changes():
            # Update visible columns
            selected_columns = [col for col, var in checkbox_vars.items() if var.get()]
            if not selected_columns:
                messagebox.showwarning("No Columns Selected", "Please select at least one column to display.")
                return
            
            # Update tab's visible columns
            current_tab.visible_columns = selected_columns
            
            # Save to config
            self.config["visible_columns"] = selected_columns
            ConfigManager.save_config(self.config)
            
            # Refresh display
            current_tab.display_logs()
            
            dialog.destroy()
        
        ttk.Button(button_frame, text="Apply", command=apply_changes).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def configure_colors(self):
        """Open dialog to configure level colors."""
        # Create dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Configure Level Colors")
        dialog.geometry("400x400")
        
        # Instructions
        ttk.Label(dialog, text="Select colors for log levels:", font=('TkDefaultFont', 10, 'bold')).pack(pady=10)
        
        # Frame for color pickers
        color_frame = ttk.Frame(dialog)
        color_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Get current colors
        current_colors = self.config.get("level_colors", {
            "debug": "#000000",
            "info": "#000000",
            "warn": "#000000",
            "warning": "#000000",
            "error": "#000000",
            "fatal": "#000000",
            "panic": "#000000"
        })
        
        # Store color variables
        color_vars = {}
        color_buttons = {}
        
        levels = ["debug", "info", "warn", "warning", "error", "fatal", "panic"]
        
        for i, level in enumerate(levels):
            frame = ttk.Frame(color_frame)
            frame.pack(fill=tk.X, pady=5)
            
            ttk.Label(frame, text=f"{level}:", width=10).pack(side=tk.LEFT, padx=5)
            
            color_var = tk.StringVar(value=current_colors.get(level, "#000000"))
            color_vars[level] = color_var
            
            color_button = tk.Button(frame, text="  ", width=5, 
                                    bg=color_var.get(),
                                    command=lambda l=level: self.pick_color(l, color_vars, color_buttons))
            color_button.pack(side=tk.LEFT, padx=5)
            color_buttons[level] = color_button
            
            ttk.Label(frame, textvariable=color_var).pack(side=tk.LEFT, padx=5)
        
        # Button frame
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def apply_changes():
            # Update colors in config
            new_colors = {level: var.get() for level, var in color_vars.items()}
            self.config["level_colors"] = new_colors
            ConfigManager.save_config(self.config)
            
            # Update all open tabs
            for tab in self.tabs:
                tab.level_colors = new_colors
                # Reconfigure tags
                for level, color in new_colors.items():
                    tab.tree.tag_configure(level, foreground=color)
                # Refresh display
                tab.display_logs()
            
            dialog.destroy()
        
        ttk.Button(button_frame, text="Apply", command=apply_changes).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def pick_color(self, level, color_vars, color_buttons):
        """Pick a color for a level."""
        from tkinter import colorchooser
        color = colorchooser.askcolor(title=f"Choose color for {level}", 
                                       initialcolor=color_vars[level].get())
        if color[1]:  # color[1] is the hex value
            color_vars[level].set(color[1])
            color_buttons[level].config(bg=color[1])
    
    def reset_to_defaults(self):
        """Reset all settings to default values."""
        # Ask for confirmation
        result = messagebox.askyesno(
            "Reset to Default Settings",
            "This will reset all settings to their default values:\n\n"
            "- Visible columns\n"
            "- Level colors\n"
            "- Window geometry\n\n"
            "Do you want to continue?"
        )
        
        if not result:
            return
        
        # Reset to default configuration
        self.config = ConfigManager.get_default_config()
        ConfigManager.save_config(self.config)
        
        # Apply new settings to all open tabs
        for tab in self.tabs:
            # Update level colors
            tab.level_colors = self.config["level_colors"]
            # Reconfigure tags
            for level, color in tab.level_colors.items():
                tab.tree.tag_configure(level, foreground=color)
            
            # Update visible columns if applicable
            default_visible = self.config["visible_columns"]
            tab.visible_columns = [col for col in default_visible if col in tab.all_columns]
            if not tab.visible_columns:
                tab.visible_columns = tab.all_columns.copy()
            
            # Refresh display
            tab.display_logs()
        
        # Reset window geometry
        self.root.geometry(self.config["window_geometry"])
        
        # Show confirmation message
        messagebox.showinfo("Settings Reset", "All settings have been reset to default values.")
        self.status_var.set("Settings reset to defaults")
    
    def on_closing(self):
        """Handle window closing event."""
        # Save window geometry
        self.config["window_geometry"] = self.root.geometry()
        ConfigManager.save_config(self.config)
        self.root.destroy()
    
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
            tab.all_columns = sorted_columns.copy()  # Store all columns
            
            # Set visible columns from config (default to time, level, message, url)
            default_visible = ['time', 'level', 'message', 'url']
            config_visible = self.config.get("visible_columns", default_visible)
            # Only use columns that exist in this file
            tab.visible_columns = [col for col in config_visible if col in tab.all_columns]
            # If no visible columns match, use defaults that exist
            if not tab.visible_columns:
                tab.visible_columns = [col for col in default_visible if col in tab.all_columns]
            # If still empty, show all columns
            if not tab.visible_columns:
                tab.visible_columns = tab.all_columns.copy()
            
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
        self.status_var.set(f"Loaded {len(tab.logs):,} log entries from {os.path.basename(tab.filename)}")
    
def main():
    """Main entry point for the application."""
    if HAS_DND:
        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()
    
    app = ZeroLogViewer(root)
    root.mainloop()


if __name__ == "__main__":
    main()
