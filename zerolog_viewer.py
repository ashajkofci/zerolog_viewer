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
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Set
import os
import threading
import platform
from pathlib import Path
import subprocess
import gzip
import csv
import sys


def get_resource_path(relative_path: str) -> Path:
    """Get absolute path to resource, works for dev and for PyInstaller.
    
    When running as a PyInstaller executable, resources are extracted to a
    temporary directory and the path is stored in sys._MEIPASS.
    In development, resources are in the same directory as this file.
    """
    try:
        # PyInstaller creates a temp folder and stores the path in _MEIPASS
        # This is where bundled data files are extracted at runtime
        base_path = Path(sys._MEIPASS)
    except AttributeError:
        # Running in normal Python environment
        base_path = Path(__file__).parent
    
    return base_path / relative_path


def get_version_info() -> Dict[str, str]:
    """Get version information from VERSION file and git."""
    version_info = {
        'version': 'Unknown',
        'git_version': 'Unknown'
    }
    
    # Try to read VERSION file from bundled resources or source directory
    try:
        version_file = get_resource_path('VERSION')
        if version_file.exists():
            with open(version_file, 'r') as f:
                version_info['version'] = f.read().strip()
    except Exception as e:
        print(f"Warning: Could not read VERSION file: {e}")
    
    # Try to get git version (only works in development, not in packaged app)
    try:
        # Only try git if we're not in a PyInstaller bundle
        if not hasattr(sys, '_MEIPASS'):
            result = subprocess.run(
                ['git', 'describe', '--tags', '--always', '--dirty'],
                capture_output=True,
                text=True,
                timeout=1,
                cwd=Path(__file__).parent
            )
            if result.returncode == 0:
                version_info['git_version'] = result.stdout.strip()
    except Exception:
        pass
    
    return version_info


def get_license_text() -> str:
    """Get the license text from LICENSE file.
    
    Returns the full text of the license file if available,
    otherwise returns a generic fallback message.
    """
    # License type constant for fallback
    LICENSE_TYPE = "BSD 3-Clause License"
    
    try:
        license_file = get_resource_path('LICENSE')
        if license_file.exists():
            with open(license_file, 'r') as f:
                return f.read()
    except Exception as e:
        print(f"Warning: Could not read LICENSE file: {e}")
    
    return f"{LICENSE_TYPE}\n\nLicense file not found. Please visit the project repository for license information."


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
                "debug": "#808080",      # Gray
                "info": "#0066CC",       # Blue
                "warn": "#FF8C00",       # Orange
                "warning": "#FF8C00",    # Orange
                "error": "#CC0000",      # Red
                "fatal": "#8B0000",      # Dark Red
                "panic": "#8B0000"       # Dark Red
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
    
    # Define log level hierarchy for filtering
    LOG_LEVELS = {
        'debug': 0,
        'info': 1,
        'warn': 2,
        'warning': 2,  # Same as warn
        'error': 3,
        'fatal': 4,
        'panic': 4  # Same as fatal
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
        self.all_columns: List[str] = []  # Store all columns including hidden ones
        self.visible_columns: List[str] = []  # Only columns to display
        self.sort_column: Optional[str] = None
        self.sort_reverse: bool = False
        self.search_debounce_id: Optional[str] = None
        self.page_size = 1000  # Number of items to display at once
        self.current_page = 0
        self.sidebar_visible = False
        self.selected_log = None
        self.level_filter = 'all'  # Default to show all logs
        
        # Get level colors from config
        self.level_colors = self.app.config.get("level_colors", {
            "debug": "#808080",      # Gray
            "info": "#0066CC",       # Blue
            "warn": "#FF8C00",       # Orange
            "warning": "#FF8C00",    # Orange
            "error": "#CC0000",      # Red
            "fatal": "#8B0000",      # Dark Red
            "panic": "#8B0000"       # Dark Red
        })
        
        # Create tab frame
        self.frame = ttk.Frame(parent_notebook)
        # Add close button to tab text
        tab_text = f"{os.path.basename(filename)}  ✕"
        parent_notebook.add(self.frame, text=tab_text)
        
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
        
        # Bind right-click context menu
        self.tree.bind('<Button-3>', self.show_context_menu)  # Right-click on Windows/Linux
        self.tree.bind('<Button-2>', self.show_context_menu)  # Right-click on macOS (Control+Click)
        
        # Configure tags for level colors
        for level, color in self.level_colors.items():
            self.tree.tag_configure(level, foreground=color)
        
        # Create sidebar frame (initially hidden)
        # Don't set width here - let the paned window manage it
        self.sidebar_frame = ttk.Frame(self.paned_window)
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
        dialog.transient(self.app.root)
        dialog.grab_set()
        
        # Center dialog over parent window
        dialog.update_idletasks()
        width = 400
        height = 520
        x = self.app.root.winfo_x() + (self.app.root.winfo_width() // 2) - (width // 2)
        y = self.app.root.winfo_y() + (self.app.root.winfo_height() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")
        
        # Get min and max dates from logs
        min_date = min(dates)
        max_date = max(dates)
        
        # Determine default date:
        # 1. If filter field already has a date, use that
        # 2. Otherwise, use first date for 'from' and last date for 'to'
        current_filter = self.date_from_var.get().strip() if field_type == 'from' else self.date_to_var.get().strip()
        if current_filter:
            try:
                default_date = datetime.fromisoformat(current_filter.replace('Z', '+00:00'))
            except:
                default_date = min_date if field_type == 'from' else max_date
        else:
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
        
        # Selected log frame with offset options
        selected_log_frame = ttk.LabelFrame(input_frame, text="Use Selected Log Entry", padding="10")
        selected_log_frame.pack(fill=tk.X, pady=10)
        
        # Time offset selector
        offset_frame = ttk.Frame(selected_log_frame)
        offset_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(offset_frame, text="Time offset:").pack(side=tk.LEFT, padx=5)
        offset_var = tk.StringVar(value="5 seconds")
        offset_combo = ttk.Combobox(offset_frame, textvariable=offset_var, 
                                    values=["5 seconds", "30 seconds", "1 minute", "5 minutes", "15 minutes", "30 minutes", "1 hour"],
                                    width=15, state="readonly")
        offset_combo.pack(side=tk.LEFT, padx=5)
        
        def use_selected_log():
            """Use the currently selected log entry's timestamp with offset for both From and To fields."""
            if not self.selected_log:
                messagebox.showinfo("No Selection", "Please select a log entry first.", parent=dialog)
                return
            
            time_str = self.selected_log.get('time', '')
            if not time_str:
                messagebox.showinfo("No Time", "Selected log entry has no timestamp.", parent=dialog)
                return
            
            try:
                log_time = datetime.fromisoformat(str(time_str).replace('Z', '+00:00'))
                
                # Parse offset
                offset_str = offset_var.get()
                offset_seconds = 0
                if "second" in offset_str:
                    offset_seconds = int(offset_str.split()[0])
                elif "minute" in offset_str:
                    offset_seconds = int(offset_str.split()[0]) * 60
                elif "hour" in offset_str:
                    offset_seconds = int(offset_str.split()[0]) * 3600
                
                # Apply offset for both From (subtract) and To (add) fields
                from_time = log_time - timedelta(seconds=offset_seconds)
                to_time = log_time + timedelta(seconds=offset_seconds)
                
                # Format dates
                from_date_str = from_time.strftime('%Y-%m-%dT%H:%M:%S') + 'Z'
                to_date_str = to_time.strftime('%Y-%m-%dT%H:%M:%S') + 'Z'
                
                # Set both From and To fields
                self.date_from_var.set(from_date_str)
                self.date_to_var.set(to_date_str)
                
                # Close the dialog
                dialog.destroy()
                
                # Apply the date filter automatically
                self.apply_date_filter()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to parse timestamp: {str(e)}", parent=dialog)
        
        ttk.Button(selected_log_frame, text="Use Selected Log", command=use_selected_log).pack(pady=5)
        
        # Show selected log info if available
        if self.selected_log:
            time_str = self.selected_log.get('time', 'N/A')
            msg = self.selected_log.get('message', 'N/A')
            if len(msg) > 40:
                msg = msg[:37] + "..."
            selected_info = ttk.Label(selected_log_frame, 
                                     text=f"Selected: {time_str}\n{msg}",
                                     font=('TkDefaultFont', 8),
                                     foreground='#666666')
            selected_info.pack(pady=(5, 0))
        
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
            # Set initial width before adding to paned window
            self.sidebar_frame.config(width=300)
            # Allow the sidebar to be resizable by user
            self.paned_window.add(self.sidebar_frame, weight=0)
            self.sidebar_visible = True
            # Force the paned window to respect the initial width
            self.paned_window.update_idletasks()
            
            # Create sidebar structure once
            self._create_sidebar_structure()
        
        # Update content without recreating structure
        self._update_sidebar_content()
    
    def _create_sidebar_structure(self):
        """Create the sidebar structure once (called only when sidebar is first shown)."""
        # Create sidebar header
        self.sidebar_header_frame = ttk.Frame(self.sidebar_frame)
        self.sidebar_header_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
        
        ttk.Label(self.sidebar_header_frame, text="Log Details", font=('TkDefaultFont', 10, 'bold')).pack(side=tk.LEFT)
        ttk.Button(self.sidebar_header_frame, text="✕", width=3, command=self.hide_sidebar).pack(side=tk.RIGHT)
        
        # Create scrollable frame for metadata
        self.sidebar_canvas = tk.Canvas(self.sidebar_frame)
        self.sidebar_scrollbar = ttk.Scrollbar(self.sidebar_frame, orient="vertical", command=self.sidebar_canvas.yview)
        self.sidebar_scrollable_frame = ttk.Frame(self.sidebar_canvas)
        
        self.sidebar_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.sidebar_canvas.configure(scrollregion=self.sidebar_canvas.bbox("all"))
        )
        
        self.sidebar_canvas.create_window((0, 0), window=self.sidebar_scrollable_frame, anchor="nw", width=self.sidebar_canvas.winfo_reqwidth())
        self.sidebar_canvas.configure(yscrollcommand=self.sidebar_scrollbar.set)
        
        # Bind canvas resize to update text widget widths
        self.sidebar_canvas.bind('<Configure>', self._on_canvas_resize)
        
        # Enable mouse wheel scrolling on the canvas
        self.sidebar_canvas.bind('<MouseWheel>', lambda e: self.sidebar_canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        self.sidebar_canvas.bind('<Button-4>', lambda e: self.sidebar_canvas.yview_scroll(-1, "units"))  # Linux scroll up
        self.sidebar_canvas.bind('<Button-5>', lambda e: self.sidebar_canvas.yview_scroll(1, "units"))   # Linux scroll down
        
        # Also bind to the scrollable frame to capture events when mouse is over content
        self.sidebar_scrollable_frame.bind('<MouseWheel>', lambda e: self.sidebar_canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
        self.sidebar_scrollable_frame.bind('<Button-4>', lambda e: self.sidebar_canvas.yview_scroll(-1, "units"))
        self.sidebar_scrollable_frame.bind('<Button-5>', lambda e: self.sidebar_canvas.yview_scroll(1, "units"))
        
        self.sidebar_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        self.sidebar_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def _update_sidebar_content(self):
        """Update the sidebar content with the selected log data."""
        if not hasattr(self, 'sidebar_scrollable_frame'):
            return
        
        # Clear only the content area, not the entire structure
        for widget in self.sidebar_scrollable_frame.winfo_children():
            widget.destroy()
        
        # Reset scroll position to top
        self.sidebar_canvas.yview_moveto(0)
        
        # Add metadata content - show all fields
        # Get system default background color from root window
        default_bg = self.app.root.cget('background')
        
        # Store text widgets for dynamic resizing
        self.sidebar_text_widgets = []
        
        for col in self.all_columns:
            if col in self.selected_log:
                value = self.selected_log[col]
                frame = ttk.Frame(self.sidebar_scrollable_frame)
                frame.pack(fill=tk.X, pady=2, padx=5)
                
                # Use a Label for the field name (non-selectable)
                label = ttk.Label(frame, text=f"{col}:", font=('TkDefaultFont', 8, 'bold'))
                label.pack(anchor='w')
                
                # Check if value is JSON and format it
                formatted_value = self._format_value_if_json(value)
                
                # Use a Text widget for the value to make it selectable
                value_text = tk.Text(frame, wrap=tk.WORD, relief=tk.SOLID,
                                    bg=default_bg, borderwidth=1, 
                                    highlightthickness=0, padx=5, pady=2,
                                    font=('TkDefaultFont', 9))
                value_text.insert('1.0', formatted_value)
                value_text.config(state=tk.DISABLED)
                
                # Add right-click context menu for filtering
                def show_context_menu(event, field_name=col, field_value=formatted_value):
                    context_menu = tk.Menu(value_text, tearoff=0)
                    context_menu.add_command(
                        label="Filter by this field",
                        command=lambda: self.filter_by_field(field_value)
                    )
                    try:
                        context_menu.tk_popup(event.x_root, event.y_root)
                    finally:
                        context_menu.grab_release()
                
                value_text.bind('<Button-3>', show_context_menu)  # Right-click on Windows/Linux
                value_text.bind('<Button-2>', show_context_menu)  # Right-click on macOS
                
                # Calculate initial height based on content
                lines = formatted_value.count('\n') + 1
                initial_height = min(max(1, lines), 15)
                value_text.config(height=initial_height)
                
                # Pack with fill to allow horizontal expansion
                value_text.pack(anchor='w', fill=tk.BOTH, expand=True, pady=2)
                
                # Store reference for dynamic height updates
                self.sidebar_text_widgets.append((value_text, formatted_value))
        
        # Initial height calculation after widgets are mapped (reduced delay)
        self.sidebar_frame.after(50, self._update_all_text_heights)
    
    def _on_canvas_resize(self, event):
        """Handle canvas resize to update text widget widths and heights."""
        if hasattr(self, 'sidebar_canvas') and hasattr(self, 'sidebar_text_widgets'):
            # Update the width of the window in the canvas
            canvas_width = event.width - 20  # Account for scrollbar and padding
            self.sidebar_canvas.itemconfig(1, width=canvas_width)  # Update canvas window width
            
            # Schedule text height updates
            self.sidebar_frame.after(50, self._update_all_text_heights)
    
    def _update_text_height(self, text_widget):
        """Update the height of a text widget based on its content and width."""
        try:
            # Make sure widget is ready
            text_widget.update_idletasks()
            
            # Get the actual content
            content = text_widget.get('1.0', 'end-1c')
            
            if not content:
                text_widget.config(height=1)
                return
            
            # Enable the widget temporarily to measure properly
            state = text_widget.cget('state')
            text_widget.config(state=tk.NORMAL)
            
            # Use the Text widget's count method with '-displaylines' option
            # This counts the number of display lines (including wrapped lines)
            # between two indices
            try:
                display_line_count = text_widget.count('1.0', 'end', 'displaylines')
                # count() returns a tuple with one element or None
                if display_line_count is None or not display_line_count:
                    # Fallback to logical line count
                    display_line_count = int(text_widget.index('end-1c').split('.')[0])
                elif isinstance(display_line_count, tuple):
                    display_line_count = display_line_count[0]
            except (tk.TclError, TypeError):
                # Fallback: count logical lines
                display_line_count = int(text_widget.index('end-1c').split('.')[0])
            
            # Restore state
            text_widget.config(state=state)
            
            # Set height with reasonable limits
            height = max(1, min(display_line_count, 20))  # Min 1, max 20 lines visible
            text_widget.config(height=height)
            
        except (tk.TclError, ValueError, AttributeError):
            # Widget may have been destroyed or not ready
            pass
    
    def _update_all_text_heights(self):
        """Update heights of all text widgets in sidebar."""
        if hasattr(self, 'sidebar_text_widgets'):
            for text_widget, _ in self.sidebar_text_widgets:
                self._update_text_height(text_widget)
    
    def _format_value_if_json(self, value) -> str:
        """Format value as pretty JSON if it's valid JSON, otherwise return as string."""
        # If value is already a dict or list (Python object), format it directly
        if isinstance(value, (dict, list)):
            try:
                return json.dumps(value, indent=2, ensure_ascii=False)
            except (TypeError, ValueError):
                return str(value)
        
        value_str = str(value)
        
        # Try to parse as JSON string
        try:
            # Only try to parse if it looks like JSON (starts with { or [)
            stripped = value_str.strip()
            if stripped.startswith('{') or stripped.startswith('['):
                parsed = json.loads(value_str)
                # Format with indentation
                return json.dumps(parsed, indent=2, ensure_ascii=False)
        except (json.JSONDecodeError, ValueError, TypeError):
            # Not valid JSON, return as-is
            pass
        
        return value_str
    
    def filter_by_field(self, field_value: str):
        """Add field value to search filters."""
        # Get the first empty search field or add a new one if all are filled
        search_field_added = False
        for search_var in self.app.search_fields:
            if not search_var.get().strip():
                search_var.set(field_value)
                search_field_added = True
                break
        
        # If all fields are filled, add a new one
        if not search_field_added:
            self.app.add_search_field()
            self.app.search_fields[-1].set(field_value)
        
        # Trigger search
        self.app.apply_search()
    
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
    
    def apply_level_filter(self, level_filter: str):
        """Apply log level filter."""
        self.level_filter = level_filter
        # Re-apply all filters including multi-search
        search_terms = [var.get().strip() for var in self.app.search_fields if var.get().strip()] if hasattr(self.app, 'search_fields') else []
        search_logic = self.app.search_logic_var.get() if hasattr(self.app, 'search_logic_var') else 'AND'
        self.apply_search_multi(search_terms, search_logic)
    
    def _passes_level_filter(self, log: Dict[str, Any]) -> bool:
        """Check if a log entry passes the level filter."""
        if self.level_filter == 'all':
            return True
        
        log_level = str(log.get('level', '')).lower()
        
        # Get the numeric level of the log entry
        log_level_value = self.LOG_LEVELS.get(log_level, -1)
        
        # If log level is unknown, include it by default
        if log_level_value == -1:
            return True
        
        # Get the filter threshold
        filter_value = self.LOG_LEVELS.get(self.level_filter, 0)
        
        # Include logs at or above the filter level
        return log_level_value >= filter_value
    
    def apply_search(self, search_text: str):
        """Apply search filter to logs, including level filter."""
        search_text = search_text.lower()
        
        if not search_text:
            # Store the currently selected log before clearing search
            selected_log_to_restore = self.selected_log
            
            # Apply level filter only
            if self.level_filter == 'all':
                self.filtered_logs = []
            else:
                self.filtered_logs = [log for log in self.logs if self._passes_level_filter(log)]
            
            self.display_logs()
            
            if self.level_filter == 'all':
                self.app.status_var.set(f"Showing all {len(self.logs):,} log entries")
            else:
                self.app.status_var.set(f"Showing {len(self.filtered_logs):,} of {len(self.logs):,} log entries (level: {self.level_filter}+)")
            
            # Restore selection and scroll to it
            if selected_log_to_restore:
                self.scroll_to_log(selected_log_to_restore)
            return
        
        # Filter logs containing search text in any field AND passing level filter
        self.filtered_logs = []
        for log in self.logs:
            # First check level filter
            if not self._passes_level_filter(log):
                continue
            
            # Then check search text
            for value in log.values():
                if search_text in str(value).lower():
                    self.filtered_logs.append(log)
                    break
        
        self.display_logs()
        
        if self.level_filter == 'all':
            self.app.status_var.set(f"Found {len(self.filtered_logs):,} of {len(self.logs):,} log entries")
        else:
            self.app.status_var.set(f"Found {len(self.filtered_logs):,} of {len(self.logs):,} log entries (level: {self.level_filter}+)")
    
    def apply_search_multi(self, search_terms: List[str], search_logic: str = "AND"):
        """Apply multiple search filters to logs with AND/OR logic, including level filter.
        
        Args:
            search_terms (List[str]): List of search terms to filter by
            search_logic (str): Logic operator 'AND' or 'OR' (default: 'AND')
        """
        # If no search terms, clear search
        if not search_terms:
            # Store the currently selected log before clearing search
            selected_log_to_restore = self.selected_log
            
            # Apply level filter only
            if self.level_filter == 'all':
                self.filtered_logs = []
            else:
                self.filtered_logs = [log for log in self.logs if self._passes_level_filter(log)]
            
            self.display_logs()
            
            if self.level_filter == 'all':
                self.app.status_var.set(f"Showing all {len(self.logs):,} log entries")
            else:
                self.app.status_var.set(f"Showing {len(self.filtered_logs):,} of {len(self.logs):,} log entries (level: {self.level_filter}+)")
            
            # Restore selection and scroll to it
            if selected_log_to_restore:
                self.scroll_to_log(selected_log_to_restore)
            return
        
        # Convert all search terms to lowercase
        search_terms = [term.lower() for term in search_terms]
        
        # Filter logs based on search terms and logic
        self.filtered_logs = []
        for log in self.logs:
            # First check level filter
            if not self._passes_level_filter(log):
                continue
            
            # Convert all log values to lowercase strings
            log_values_str = [str(value).lower() for value in log.values()]
            
            if search_logic == "AND":
                # All search terms must be found in the log
                match = True
                for term in search_terms:
                    term_found = any(term in value for value in log_values_str)
                    if not term_found:
                        match = False
                        break
                if match:
                    self.filtered_logs.append(log)
            else:  # OR logic
                # At least one search term must be found in the log
                match = False
                for term in search_terms:
                    term_found = any(term in value for value in log_values_str)
                    if term_found:
                        match = True
                        break
                if match:
                    self.filtered_logs.append(log)
        
        self.display_logs()
        
        # Build status message
        if len(search_terms) == 1:
            search_desc = f"'{search_terms[0]}'"
        else:
            search_desc = f"{len(search_terms)} terms ({search_logic})"
        
        if self.level_filter == 'all':
            self.app.status_var.set(f"Found {len(self.filtered_logs):,} of {len(self.logs):,} log entries for {search_desc}")
        else:
            self.app.status_var.set(f"Found {len(self.filtered_logs):,} of {len(self.logs):,} log entries for {search_desc} (level: {self.level_filter}+)")
    
    
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
    
    def scroll_to_log(self, log_entry: Dict[str, Any]):
        """Scroll to and select a specific log entry in the tree view."""
        if not log_entry:
            return
        
        # Get the list being displayed
        logs_to_display = self.filtered_logs if self.filtered_logs else self.logs
        
        # Find the index of this log entry in the displayed logs
        try:
            # Use object identity to find the exact log entry
            log_index = None
            for i, log in enumerate(logs_to_display):
                if log is log_entry:
                    log_index = i
                    break
            
            # If not found by identity, try matching by content
            if log_index is None:
                for i, log in enumerate(logs_to_display):
                    if log == log_entry:
                        log_index = i
                        break
            
            if log_index is not None:
                # Load items up to this index if not yet loaded
                current_count = len(self.tree.get_children())
                if log_index >= current_count:
                    # Load more items to include the target log
                    display_columns = self.visible_columns if self.visible_columns else self.columns
                    for log in logs_to_display[current_count:log_index + 1]:
                        values = [log.get(col, '') for col in display_columns]
                        level = str(log.get('level', '')).lower()
                        tag = level if level in self.level_colors else ''
                        self.tree.insert('', tk.END, values=values, tags=(tag,))
                
                # Get the tree item ID for this index
                children = self.tree.get_children()
                if log_index < len(children):
                    item_id = children[log_index]
                    # Select and scroll to this item
                    self.tree.selection_set(item_id)
                    self.tree.see(item_id)
                    self.tree.focus(item_id)
        except Exception as e:
            # If we can't scroll to the log, just continue without error
            print(f"Warning: Could not scroll to log: {e}")
    
    def show_context_menu(self, event):
        """Show context menu on right-click in the treeview."""
        # Select the item under cursor if not already selected
        item = self.tree.identify_row(event.y)
        if item and item not in self.tree.selection():
            self.tree.selection_set(item)
        
        # Create context menu
        context_menu = tk.Menu(self.tree, tearoff=0)
        
        # Get selected items
        selected_items = self.tree.selection()
        
        if selected_items:
            context_menu.add_command(
                label=f"Export Selected ({len(selected_items)} entries)",
                command=self.export_selected
            )
        
        context_menu.add_command(
            label="Export All Displayed Results",
            command=self.export_displayed
        )
        
        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()
    
    def export_selected(self):
        """Export selected log entries."""
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showinfo("No Selection", "No log entries are selected.")
            return
        
        # Get the logs corresponding to selected items
        logs_to_display = self.filtered_logs if self.filtered_logs else self.logs
        selected_logs = []
        
        for item in selected_items:
            item_index = self.tree.index(item)
            if item_index < len(logs_to_display):
                selected_logs.append(logs_to_display[item_index])
        
        if not selected_logs:
            messagebox.showinfo("No Data", "No log entries to export.")
            return
        
        self._export_logs(selected_logs, "selected")
    
    def export_displayed(self):
        """Export all displayed/filtered log entries."""
        logs_to_export = self.filtered_logs if self.filtered_logs else self.logs
        
        if not logs_to_export:
            messagebox.showinfo("No Data", "No log entries to export.")
            return
        
        self._export_logs(logs_to_export, "displayed")
    
    def _export_logs(self, logs: List[Dict[str, Any]], export_type: str):
        """Export logs to a file with format selection.
        
        Args:
            logs: List of log entries to export
            export_type: Type of export ("selected" or "displayed")
        """
        if not logs:
            return
        
        # Ask user for file format and location
        file_types = [
            ("JSONL files", "*.jsonl"),
            ("CSV files", "*.csv"),
            ("JSON files", "*.json"),
            ("All files", "*.*")
        ]
        
        filename = filedialog.asksaveasfilename(
            title=f"Export {export_type} log entries",
            defaultextension=".jsonl",
            filetypes=file_types
        )
        
        if not filename:
            return  # User cancelled
        
        try:
            # Determine format from file extension
            file_ext = os.path.splitext(filename)[1].lower()
            
            if file_ext == '.csv':
                self._export_to_csv(logs, filename)
            elif file_ext == '.json':
                self._export_to_json(logs, filename)
            else:  # Default to JSONL
                self._export_to_jsonl(logs, filename)
            
            messagebox.showinfo(
                "Export Successful",
                f"Exported {len(logs):,} log entries to:\n{filename}"
            )
            self.app.status_var.set(f"Exported {len(logs):,} entries to {os.path.basename(filename)}")
            
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export logs: {str(e)}")
    
    def _export_to_jsonl(self, logs: List[Dict[str, Any]], filename: str):
        """Export logs to JSONL format."""
        with open(filename, 'w', encoding='utf-8') as f:
            for log in logs:
                f.write(json.dumps(log, ensure_ascii=False) + '\n')
    
    def _export_to_json(self, logs: List[Dict[str, Any]], filename: str):
        """Export logs to JSON format (array of objects)."""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(logs, f, indent=2, ensure_ascii=False)
    
    def _export_to_csv(self, logs: List[Dict[str, Any]], filename: str):
        """Export logs to CSV format."""
        if not logs:
            return
        
        # Get all unique columns from all logs
        all_columns = set()
        for log in logs:
            all_columns.update(log.keys())
        
        # Sort columns with priority (time, level, message first)
        priority_columns = ['time', 'level', 'message']
        sorted_columns = []
        for col in priority_columns:
            if col in all_columns:
                sorted_columns.append(col)
                all_columns.discard(col)
        sorted_columns.extend(sorted(all_columns))
        
        # Write CSV
        with open(filename, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=sorted_columns, extrasaction='ignore')
            writer.writeheader()
            
            for log in logs:
                # Convert nested objects to JSON strings for CSV
                row = {}
                for col in sorted_columns:
                    value = log.get(col, '')
                    if isinstance(value, (dict, list)):
                        row[col] = json.dumps(value, ensure_ascii=False)
                    else:
                        row[col] = value
                writer.writerow(row)




class ZeroLogViewer:
    """Main application class for the ZeroLog Viewer."""
    
    # Constants
    MIN_SEARCH_FIELDS = 1  # Minimum number of search fields to maintain
    
    def __init__(self, root):
        """Initialize the ZeroLog Viewer application."""
        self.root = root
        
        # Get version information
        self.version_info = get_version_info()
        
        # Set title with version
        title = "ZeroLog Viewer"
        if self.version_info['version'] != 'Unknown':
            title += f" v{self.version_info['version']}"
        if self.version_info['git_version'] != 'Unknown':
            title += f" ({self.version_info['git_version']})"
        self.root.title(title)
        
        # Load configuration
        self.config = ConfigManager.load_config()
        self.root.geometry(self.config.get("window_geometry", "1200x700"))
        
        self.tabs: List[LogTab] = []
        
        # Search fields management
        self.search_fields: List[tk.StringVar] = []  # List of StringVar objects for each search field
        self.search_entries: List[ttk.Entry] = []  # List of Entry widgets
        
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
        file_menu.add_command(label="Export Displayed Results", command=self.export_displayed_results)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Settings menu
        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Settings", menu=settings_menu)
        settings_menu.add_command(label="Configure Visible Columns...", command=self.configure_columns)
        settings_menu.add_command(label="Configure Level Colors...", command=self.configure_colors)
        settings_menu.add_separator()
        settings_menu.add_command(label="Reset to Default Settings", command=self.reset_to_defaults)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
        
        # Toolbar frame
        toolbar = ttk.Frame(self.root, padding="5")
        toolbar.pack(side=tk.TOP, fill=tk.X)
        
        # Open button
        ttk.Button(toolbar, text="Open File", command=self.open_file).pack(side=tk.LEFT, padx=2)
        
        # Search container frame (will hold multiple search fields)
        self.search_container = ttk.Frame(toolbar)
        self.search_container.pack(side=tk.LEFT, fill=tk.X, expand=False, padx=(10, 0))
        
        # AND/OR logic selector
        ttk.Label(self.search_container, text="Search:").pack(side=tk.LEFT, padx=(0, 2))
        self.search_logic_var = tk.StringVar(value="AND")
        search_logic_combo = ttk.Combobox(
            self.search_container,
            textvariable=self.search_logic_var,
            values=["AND", "OR"],
            width=5,
            state="readonly"
        )
        search_logic_combo.pack(side=tk.LEFT, padx=2)
        search_logic_combo.bind('<<ComboboxSelected>>', lambda event: self.apply_search())
        
        # Frame to hold search field entries
        self.search_fields_frame = ttk.Frame(self.search_container)
        self.search_fields_frame.pack(side=tk.LEFT, fill=tk.X, expand=False)
        
        # Add first search field by default
        self.add_search_field()
        
        # Add/Remove buttons
        ttk.Button(self.search_container, text="+", width=3, command=self.add_search_field).pack(side=tk.LEFT, padx=1)
        ttk.Button(self.search_container, text="-", width=3, command=self.remove_search_field).pack(side=tk.LEFT, padx=1)
        
        # Clear search button
        ttk.Button(self.search_container, text="Clear", command=self.clear_search).pack(side=tk.LEFT, padx=2)
        
        # Log level filter
        ttk.Label(toolbar, text="Level:").pack(side=tk.LEFT, padx=(10, 2))
        self.level_filter_var = tk.StringVar(value="All logs")
        level_filter_combo = ttk.Combobox(
            toolbar, 
            textvariable=self.level_filter_var,
            values=["All logs", "Debug and more", "Info and more", "Warn and more", "Error and more"],
            width=15,
            state="readonly"
        )
        level_filter_combo.pack(side=tk.LEFT, padx=2)
        level_filter_combo.bind('<<ComboboxSelected>>', lambda event: self.apply_level_filter())
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready. Open a JSONL file or drag and drop files here.")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.notebook.bind('<<NotebookTabChanged>>', self.on_tab_changed)
        
        # Bind click event for close button and drag-and-drop
        self.notebook.bind('<Button-1>', self.on_tab_click)
        self.notebook.bind('<ButtonPress-1>', self.on_tab_press)
        self.notebook.bind('<B1-Motion>', self.on_tab_drag)
        self.notebook.bind('<ButtonRelease-1>', self.on_tab_release)
        
        # Variables for drag and drop
        self.drag_start_x = None
        self.drag_start_tab = None
        self.drag_start_tab_x = None
        
        self.search_debounce_id: Optional[str] = None
    
    def on_drop(self, event):
        """Handle drag and drop files."""
        files = self.root.tk.splitlist(event.data)
        valid_files = []
        for file_path in files:
            # Remove curly braces if present (Windows)
            file_path = file_path.strip('{}')
            if os.path.isfile(file_path):
                valid_files.append(file_path)
        
        if valid_files:
            self._handle_multiple_files(valid_files)
    
    def on_tab_changed(self, event):
        """Handle tab change event."""
        # Status bar is now centralized - no need to update from tabs
        pass
    
    def on_tab_click(self, event):
        """Handle click on tab - not used, but kept for potential future use."""
        pass
    
    def on_tab_press(self, event):
        """Handle mouse press on tab for drag start."""
        try:
            clicked_tab = self.notebook.tk.call(self.notebook._w, "identify", "tab", event.x, event.y)
            if clicked_tab != '':
                tab_index = int(clicked_tab)
                self.drag_start_x = event.x
                self.drag_start_tab = tab_index
                
                # Store the initial tab position for close button detection
                tab_coords = self.notebook.bbox(tab_index)
                if tab_coords:
                    self.drag_start_tab_x = tab_coords[0]
            else:
                self.drag_start_x = None
                self.drag_start_tab = None
                self.drag_start_tab_x = None
        except:
            self.drag_start_x = None
            self.drag_start_tab = None
            self.drag_start_tab_x = None
    
    def on_tab_drag(self, event):
        """Handle dragging of tab."""
        if self.drag_start_tab is None or self.drag_start_x is None:
            return
        
        # Check if we've moved enough to consider it a drag (not just a click)
        if abs(event.x - self.drag_start_x) < 10:
            return
        
        try:
            # Get the tab currently under the mouse
            target_tab = self.notebook.tk.call(self.notebook._w, "identify", "tab", event.x, event.y)
            if target_tab != '' and target_tab != self.drag_start_tab:
                target_index = int(target_tab)
                source_index = self.drag_start_tab
                
                # Reorder the tabs
                if abs(target_index - source_index) >= 1:
                    self.reorder_tabs(source_index, target_index)
                    # Update drag start position
                    self.drag_start_tab = target_index
        except:
            pass
    
    def on_tab_release(self, event):
        """Handle mouse release after drag - check for close button click."""
        # Check if this was a click (not a drag) on the close button
        if self.drag_start_tab is not None and self.drag_start_x is not None:
            # If mouse didn't move much, it's a click not a drag
            if abs(event.x - self.drag_start_x) < 10:
                try:
                    # Verify we're still clicking on the same tab
                    clicked_tab = self.notebook.tk.call(self.notebook._w, "identify", "tab", event.x, event.y)
                    if clicked_tab != '' and int(clicked_tab) == self.drag_start_tab:
                        tab_index = self.drag_start_tab
                        
                        # Get the actual bounding box of each tab to find positions
                        # We'll iterate through all tabs to find start and end positions
                        tab_right_edge = 0
                        tab_left_edge = 0
                        
                        for i in range(len(self.notebook.tabs())):
                            tab_text = self.notebook.tab(i, "text")
                            # Use Tk font measure to get actual text width
                            try:
                                # Get the font being used for tabs
                                import tkinter.font as tkfont
                                # ttk.Notebook uses TkDefaultFont typically
                                font = tkfont.nametofont("TkDefaultFont")
                                text_width = font.measure(tab_text)
                                # Add padding (typical padding is around 12-16 pixels per side)
                                tab_width = text_width + 24
                            except:
                                # Fallback to estimation if font measurement fails
                                tab_width = len(tab_text) * 6 + 24
                            
                            if i < tab_index:
                                tab_left_edge += tab_width
                            
                            if i == tab_index:
                                tab_right_edge = tab_left_edge + tab_width
                                break
                        
                        # Calculate click position within the tab
                        click_distance_from_right = tab_right_edge - event.x
                        
                        # Debug output
                        print(f"Click debug: event.x={event.x}, tab_left={tab_left_edge}, tab_right={tab_right_edge}")
                        print(f"Distance from right edge: {click_distance_from_right}")
                        
                        # Only close if clicking within 20 pixels from the right edge
                        if click_distance_from_right >= 0 and click_distance_from_right <= 40:
                            print(f"Closing tab {tab_index}")
                            self.close_tab(tab_index)
                        else:
                            print(f"Not closing - distance from right: {click_distance_from_right}")
                            
                except Exception as e:
                    print(f"Exception in on_tab_release: {e}")
                    import traceback
                    traceback.print_exc()
        
        # Reset drag state
        self.drag_start_x = None
        self.drag_start_tab = None
        self.drag_start_tab_x = None
    
    def reorder_tabs(self, source_index: int, target_index: int):
        """Reorder tabs by moving source to target position."""
        if source_index == target_index:
            return
        
        if 0 <= source_index < len(self.tabs) and 0 <= target_index < len(self.tabs):
            # Move the tab in our list
            tab = self.tabs.pop(source_index)
            self.tabs.insert(target_index, tab)
            
            # Move in the notebook widget
            self.notebook.insert(target_index, self.notebook.tabs()[source_index])
    
    def close_tab(self, tab_index: int):
        """Close a tab at the specified index."""
        if 0 <= tab_index < len(self.tabs):
            self.notebook.forget(tab_index)
            self.tabs.pop(tab_index)
            if not self.tabs:
                self.status_var.set("Ready. Open a JSONL file or drag and drop files here.")
    
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
    
    def add_search_field(self):
        """Add a new search field to the search container."""
        search_var = tk.StringVar()
        search_var.trace('w', lambda *args: self.debounced_search())
        
        search_entry = ttk.Entry(self.search_fields_frame, textvariable=search_var, width=20)
        search_entry.pack(side=tk.LEFT, padx=2)
        search_entry.bind('<Return>', lambda event: self.apply_search())
        
        self.search_fields.append(search_var)
        self.search_entries.append(search_entry)
    
    def remove_search_field(self):
        """Remove the last search field from the search container."""
        if len(self.search_fields) > self.MIN_SEARCH_FIELDS:
            # Remove the last search field
            search_var = self.search_fields.pop()
            search_entry = self.search_entries.pop()
            
            # Destroy the widget
            search_entry.destroy()
            
            # Apply search with remaining fields
            self.apply_search()
    
    def debounced_search(self):
        """Debounce search input to avoid too many updates."""
        if self.search_debounce_id:
            self.root.after_cancel(self.search_debounce_id)
        self.search_debounce_id = self.root.after(300, self.apply_search)  # 300ms debounce
    
    def apply_search(self):
        """Apply search to current tab with multiple search terms."""
        current_tab = self.get_current_tab()
        if current_tab:
            # Collect all search terms from search fields
            search_terms = [var.get().strip() for var in self.search_fields if var.get().strip()]
            search_logic = self.search_logic_var.get()
            current_tab.apply_search_multi(search_terms, search_logic)
    
    def clear_search(self):
        """Clear all search filters and remove extra search fields."""
        # Clear all search field values
        for search_var in self.search_fields:
            search_var.set('')
        
        # Remove extra search fields, keeping only the first one
        while len(self.search_fields) > self.MIN_SEARCH_FIELDS:
            search_var = self.search_fields.pop()
            search_entry = self.search_entries.pop()
            search_entry.destroy()
    
    def apply_level_filter(self):
        """Apply log level filter to current tab."""
        current_tab = self.get_current_tab()
        if current_tab:
            # Map display name to internal level name
            level_map = {
                "All logs": "all",
                "Debug and more": "debug",
                "Info and more": "info",
                "Warn and more": "warn",
                "Error and more": "error"
            }
            level_filter = level_map.get(self.level_filter_var.get(), "all")
            current_tab.apply_level_filter(level_filter)
    
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
        dialog.transient(self.root)
        
        # Center dialog over parent window
        dialog.update_idletasks()
        width = 400
        height = 500
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (width // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")
        
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
        dialog.transient(self.root)
        
        # Center dialog over parent window
        dialog.update_idletasks()
        width = 400
        height = 400
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (width // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")
        
        # Instructions
        ttk.Label(dialog, text="Select colors for log levels:", font=('TkDefaultFont', 10, 'bold')).pack(pady=10)
        
        # Frame for color pickers
        color_frame = ttk.Frame(dialog)
        color_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Get current colors
        current_colors = self.config.get("level_colors", {
            "debug": "#808080",      # Gray
            "info": "#0066CC",       # Blue
            "warn": "#FF8C00",       # Orange
            "warning": "#FF8C00",    # Orange
            "error": "#CC0000",      # Red
            "fatal": "#8B0000",      # Dark Red
            "panic": "#8B0000"       # Dark Red
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
    
    def show_about(self):
        """Show About dialog with author and license information."""
        # Create dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("About ZeroLog Viewer")
        dialog.transient(self.root)
        dialog.resizable(False, False)
        
        # Center dialog over parent window
        dialog.update_idletasks()
        width = 450
        height = 400
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (width // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")
        
        # Content frame
        content_frame = ttk.Frame(dialog, padding="20")
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        ttk.Label(content_frame, text="ZeroLog Viewer", 
                 font=('TkDefaultFont', 16, 'bold')).pack(pady=(0, 10))
        
        # Version information
        version_text = f"Version {self.version_info['version']}"
        if self.version_info['git_version'] != 'Unknown':
            version_text += f"\nGit: {self.version_info['git_version']}"
        ttk.Label(content_frame, text=version_text,
                 font=('TkDefaultFont', 9),
                 justify=tk.CENTER).pack(pady=(0, 5))
        
        # Description
        ttk.Label(content_frame, 
                 text="A cross-platform GUI application for viewing\nand analyzing JSONL log files",
                 font=('TkDefaultFont', 10),
                 justify=tk.CENTER).pack(pady=(0, 20))
        
        # Author
        ttk.Label(content_frame, text="Author:", 
                 font=('TkDefaultFont', 9, 'bold')).pack(anchor='w')
        ttk.Label(content_frame, text="Adrian Shajkofci", 
                 font=('TkDefaultFont', 9)).pack(anchor='w', pady=(0, 10))
        
        # GitHub link
        ttk.Label(content_frame, text="GitHub Repository:", 
                 font=('TkDefaultFont', 9, 'bold')).pack(anchor='w')
        
        # Create clickable link
        github_link = tk.Label(content_frame, 
                              text="https://github.com/ashajkofci/zerolog_viewer",
                              font=('TkDefaultFont', 9, 'underline'),
                              foreground='blue',
                              cursor='hand2')
        github_link.pack(anchor='w', pady=(0, 10))
        github_link.bind('<Button-1>', lambda e: self.open_url('https://github.com/ashajkofci/zerolog_viewer'))
        
        # License
        ttk.Label(content_frame, text="License:", 
                 font=('TkDefaultFont', 9, 'bold')).pack(anchor='w')
        
        # License info with view button
        license_frame = ttk.Frame(content_frame)
        license_frame.pack(anchor='w', fill=tk.X, pady=(0, 20))
        
        ttk.Label(license_frame, text="BSD 3-Clause License", 
                 font=('TkDefaultFont', 9)).pack(side=tk.LEFT)
        ttk.Button(license_frame, text="View License", 
                  command=self.show_license).pack(side=tk.LEFT, padx=(10, 0))
        
        # Close button
        ttk.Button(content_frame, text="Close", command=dialog.destroy).pack(pady=(10, 0))
    
    def show_license(self):
        """Show the full license text in a new window."""
        # Create dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("License - ZeroLog Viewer")
        dialog.transient(self.root)
        
        # Center dialog over parent window
        dialog.update_idletasks()
        width = 600
        height = 500
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (width // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")
        
        # Content frame
        content_frame = ttk.Frame(dialog, padding="10")
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        ttk.Label(content_frame, text="BSD 3-Clause License", 
                 font=('TkDefaultFont', 12, 'bold')).pack(pady=(0, 10))
        
        # Text widget with scrollbar for license
        text_frame = ttk.Frame(content_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        license_text = tk.Text(text_frame, wrap=tk.WORD, yscrollcommand=scrollbar.set,
                              font=('TkFixedFont', 9), padx=10, pady=10)
        license_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=license_text.yview)
        
        # Insert license text
        license_content = get_license_text()
        license_text.insert('1.0', license_content)
        license_text.config(state=tk.DISABLED)
        
        # Close button
        ttk.Button(content_frame, text="Close", command=dialog.destroy).pack(pady=(10, 0))
    
    def open_url(self, url: str):
        """Open URL in default web browser."""
        import webbrowser
        webbrowser.open(url)
    
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
                ("All supported", "*.jsonl *.json *.log *.log.gz *.gz"),
                ("JSONL files", "*.jsonl"),
                ("JSON files", "*.json"),
                ("Log files", "*.log"),
                ("Gzip files", "*.gz"),
                ("All files", "*.*")
            ]
        )
        
        if filenames:
            self._handle_multiple_files(list(filenames))
    
    def _handle_multiple_files(self, filenames: List[str]):
        """Handle opening multiple files - ask user if they want to merge or open separately."""
        if not filenames:
            return
        
        # If only one file, just load it normally
        if len(filenames) == 1:
            self.load_file(filenames[0])
            return
        
        # Ask user what to do with multiple files
        dialog = tk.Toplevel(self.root)
        dialog.title("Multiple Files Selected")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center dialog over parent window
        dialog.update_idletasks()
        width = 500
        height = 200
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (width // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (height // 2)
        dialog.geometry(f"{width}x{height}+{x}+{y}")
        
        # Message
        message_frame = ttk.Frame(dialog, padding="20")
        message_frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(message_frame, 
                 text=f"You have selected {len(filenames)} files.",
                 font=('TkDefaultFont', 10, 'bold')).pack(pady=(0, 10))
        
        ttk.Label(message_frame, 
                 text="How would you like to open them?",
                 font=('TkDefaultFont', 10)).pack(pady=(0, 20))
        
        # Store user choice
        user_choice = {'action': None}
        
        def on_merge():
            user_choice['action'] = 'merge'
            dialog.destroy()
        
        def on_separate():
            user_choice['action'] = 'separate'
            dialog.destroy()
        
        def on_cancel():
            user_choice['action'] = 'cancel'
            dialog.destroy()
        
        # Buttons
        button_frame = ttk.Frame(message_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="Merge into One Tab", 
                  command=on_merge, width=20).pack(side=tk.LEFT, padx=5, expand=True)
        ttk.Button(button_frame, text="Open in Separate Tabs", 
                  command=on_separate, width=20).pack(side=tk.LEFT, padx=5, expand=True)
        
        ttk.Button(message_frame, text="Cancel", 
                  command=on_cancel).pack(pady=(10, 0))
        
        # Wait for dialog to close
        self.root.wait_window(dialog)
        
        # Handle user choice
        if user_choice['action'] == 'merge':
            self.load_merged_files(filenames)
        elif user_choice['action'] == 'separate':
            for filename in filenames:
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
            
            # Check if file is gzipped
            is_gzipped = filename.endswith('.gz')
            
            # Read and parse JSONL file with streaming for large files
            if is_gzipped:
                file_handle = gzip.open(filename, 'rt', encoding='utf-8')
            else:
                file_handle = open(filename, 'r', encoding='utf-8')
            
            try:
                line_num = 0
                for line in file_handle:
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
            finally:
                file_handle.close()
            
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
    
    def load_merged_files(self, filenames: List[str]):
        """Load and merge multiple files into a single tab."""
        if not filenames:
            return
        
        # Create a merged filename for the tab
        if len(filenames) == 2:
            merged_name = f"{os.path.basename(filenames[0])} + {os.path.basename(filenames[1])}"
        else:
            merged_name = f"{len(filenames)} merged files"
        
        # Check if merged tab already exists with this name
        for tab in self.tabs:
            if tab.filename == merged_name:
                # Switch to existing tab
                tab_index = self.tabs.index(tab)
                self.notebook.select(tab_index)
                return
        
        # Create new tab
        tab = LogTab(self.notebook, merged_name, self)
        self.tabs.append(tab)
        
        # Load files in background thread
        self.status_var.set(f"Loading and merging {len(filenames)} files...")
        self.root.update_idletasks()
        
        thread = threading.Thread(target=self._load_merged_files_thread, args=(tab, filenames))
        thread.daemon = True
        thread.start()
    
    def _load_merged_files_thread(self, tab: LogTab, filenames: List[str]):
        """Load and merge multiple files in background thread."""
        try:
            all_logs = []
            columns = set()
            
            for file_idx, filename in enumerate(filenames):
                # Update status
                self.root.after(0, lambda f=filename, idx=file_idx: self.status_var.set(
                    f"Loading file {idx + 1}/{len(filenames)}: {os.path.basename(f)}..."
                ))
                
                # Check if file is gzipped
                is_gzipped = filename.endswith('.gz')
                
                # Read and parse JSONL file
                if is_gzipped:
                    file_handle = gzip.open(filename, 'rt', encoding='utf-8')
                else:
                    file_handle = open(filename, 'r', encoding='utf-8')
                
                try:
                    line_num = 0
                    for line in file_handle:
                        line = line.strip()
                        if line:
                            try:
                                log_entry = json.loads(line)
                                all_logs.append(log_entry)
                                
                                # Collect all unique column names
                                columns.update(log_entry.keys())
                                
                                line_num += 1
                                
                                # Update status periodically
                                if line_num % 10000 == 0:
                                    self.root.after(0, lambda n=line_num, f=filename: self.status_var.set(
                                        f"Loading {os.path.basename(f)}... ({n:,} entries)"
                                    ))
                            except json.JSONDecodeError as e:
                                print(f"Warning: Skipping invalid JSON in {filename} on line {line_num}: {e}")
                finally:
                    file_handle.close()
            
            if not all_logs:
                self.root.after(0, lambda: messagebox.showwarning("No Data", "No valid log entries found in the files."))
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
            tab.all_columns = sorted_columns.copy()
            
            # Set visible columns from config
            default_visible = ['time', 'level', 'message', 'url']
            config_visible = self.config.get("visible_columns", default_visible)
            tab.visible_columns = [col for col in config_visible if col in tab.all_columns]
            if not tab.visible_columns:
                tab.visible_columns = [col for col in default_visible if col in tab.all_columns]
            if not tab.visible_columns:
                tab.visible_columns = tab.all_columns.copy()
            
            tab.all_logs = all_logs
            tab.logs = all_logs.copy()
            
            # Sort by time
            tab.logs.sort(key=lambda x: x.get('time', ''))
            
            # Display on main thread
            self.root.after(0, lambda: self._finalize_merged_load(tab, len(filenames)))
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to load files: {str(e)}"))
            self.root.after(0, lambda: self.close_current_tab())
    
    def _finalize_merged_load(self, tab: LogTab, file_count: int):
        """Finalize merged load on the main thread."""
        tab.display_logs()
        self.status_var.set(f"Loaded and merged {len(tab.logs):,} log entries from {file_count} files")
    
    def export_displayed_results(self):
        """Export displayed results from the current tab."""
        current_tab = self.get_current_tab()
        if not current_tab:
            messagebox.showinfo("No File Open", "Please open a file first.")
            return
        
        current_tab.export_displayed()
    
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
