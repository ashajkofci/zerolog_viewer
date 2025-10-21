#!/usr/bin/env python3
"""
Demo script showing the new column visibility and metadata features.
"""

def show_new_features():
    print("""
╔══════════════════════════════════════════════════════════════════════════════════════════╗
║                   ZeroLog Viewer - Column Visibility & Metadata Features                ║
╠══════════════════════════════════════════════════════════════════════════════════════════╣

🆕 NEW FEATURE 1: HIDDEN COLUMNS BY DEFAULT
─────────────────────────────────────────────────────────────────────────────────────────

Only 4 columns visible by default: time, level, message, url

Before (showing all columns):
┌──────────────────────────────────────────────────────────────────────────────────────┐
│ time         │level│message│git_rev│serialN│orgID│deviceID│duration│url│...        │
│──────────────────────────────────────────────────────────────────────────────────────│
│ 2025-10-20...│debug│Device...│v0.9.0│910335│67e5..│68cd61..│2.750  │   │[8 more] │
└──────────────────────────────────────────────────────────────────────────────────────┘

After (only visible columns):
┌───────────────────────────────────────────────────────────────────────────────────────┐
│ time              │ level  │ message                  │ url                          │
│───────────────────────────────────────────────────────────────────────────────────────│
│ 2025-10-20 17:19:16│ debug │ Device found             │ https://api.example.com     │
│ 2025-10-20 17:19:17│ info  │ Connection established   │ https://api.example.com/v2  │
│ 2025-10-20 17:19:18│ warn  │ High latency detected    │ https://api.example.com/v2  │
└───────────────────────────────────────────────────────────────────────────────────────┘

✓ Cleaner display with only essential columns
✓ Less horizontal scrolling needed
✓ Easier to read at a glance


🆕 NEW FEATURE 2: DOUBLE-CLICK TO VIEW METADATA
─────────────────────────────────────────────────────────────────────────────────────────

Double-click any log entry to see ALL fields in a popup:

┌─────────────────────────────────────────────────────────────────────────┐
│ Log Entry Metadata                                              [X]     │
├─────────────────────────────────────────────────────────────────────────┤
│ Complete Log Entry Metadata                                             │
│ ══════════════════════════════════════════════════════════════════════  │
│                                                                          │
│ Visible Columns:                                                        │
│ ──────────────────────────────────────────────────────────────────────  │
│ time:                                                                    │
│   2025-10-20T17:19:16Z                                                  │
│                                                                          │
│ level:                                                                   │
│   debug                                                                  │
│                                                                          │
│ message:                                                                 │
│   Device found                                                          │
│                                                                          │
│ url:                                                                     │
│   https://api.example.com                                               │
│                                                                          │
│ Hidden Columns:                                                         │
│ ──────────────────────────────────────────────────────────────────────  │
│ git_revision:                                                            │
│   v0.9.0-3f5b689                                                        │
│                                                                          │
│ serialNumber:                                                            │
│   910335                                                                │
│                                                                          │
│ organizationID:                                                          │
│   67e59f3d11d57bb940742d07                                              │
│                                                                          │
│ deviceID:                                                                │
│   68cd61eaadba4ed22ccdc080                                              │
│                                                                          │
│ duration:                                                                │
│   2.750617                                                              │
│                                                                          │
│                                          [Close]                         │
└─────────────────────────────────────────────────────────────────────────┘

✓ All fields accessible via double-click
✓ Organized: visible columns first, then hidden columns
✓ Scrollable for long content
✓ Read-only display


🆕 NEW FEATURE 3: SETTINGS MENU TO CONFIGURE COLUMNS
─────────────────────────────────────────────────────────────────────────────────────────

Menu: Settings → Configure Visible Columns...

┌──────────────────────────────────────────────────┐
│ Configure Visible Columns                  [X]  │
├──────────────────────────────────────────────────┤
│ Select columns to display:                       │
│                                                   │
│ ┌──────────────────────────────────────────────┐ │
│ │ ☑ time                                       │ │
│ │ ☑ level                                      │ │
│ │ ☑ message                                    │ │
│ │ ☑ url                                        │ │
│ │ ☐ git_revision                               │ │
│ │ ☐ serialNumber                               │ │
│ │ ☐ organizationID                             │ │
│ │ ☐ deviceID                                   │ │
│ │ ☐ duration                                   │ │
│ │                                               │ │
│ └──────────────────────────────────────────────┘ │
│                                                   │
│               [Apply]  [Cancel]                  │
└──────────────────────────────────────────────────┘

✓ Check/uncheck columns to show/hide
✓ Changes apply immediately
✓ All columns available


🆕 NEW FEATURE 4: AUTOMATIC CONFIGURATION PERSISTENCE
─────────────────────────────────────────────────────────────────────────────────────────

Configuration saved automatically to:
- Windows: %APPDATA%/zerolog_viewer/config.json
- macOS:   ~/Library/Application Support/zerolog_viewer/config.json
- Linux:   ~/.config/zerolog_viewer/config.json

Example config.json:
{
  "visible_columns": [
    "time",
    "level",
    "message",
    "url"
  ],
  "window_geometry": "1200x700"
}

✓ Settings persist across app restarts
✓ Each system uses appropriate config location
✓ Window size and position remembered


🆕 NEW FEATURE 5: SEARCH STILL WORKS ON HIDDEN COLUMNS
─────────────────────────────────────────────────────────────────────────────────────────

Search: [910335              ]  [Clear]

Even though "serialNumber" is hidden:
┌───────────────────────────────────────────────────────────────────────────────────────┐
│ time              │ level  │ message                  │ url                          │
│───────────────────────────────────────────────────────────────────────────────────────│
│ 2025-10-20 17:19:16│ debug │ Device found             │ https://api.example.com     │
└───────────────────────────────────────────────────────────────────────────────────────┘
Status: Found 1 of 6 log entries (serial number 910335 matched in hidden field)

✓ Search includes ALL fields (visible and hidden)
✓ Hidden fields are searchable
✓ Results show matching entries even when match is in hidden column


═══════════════════════════════════════════════════════════════════════════════════════

📋 USAGE SUMMARY:

1. **Default View**: Opens with only time, level, message, url visible
2. **View Metadata**: Double-click any log entry to see all fields
3. **Configure Columns**: Settings → Configure Visible Columns...
4. **Persistent Settings**: Column visibility saved automatically
5. **Full Search**: Search works across all fields (visible + hidden)

═══════════════════════════════════════════════════════════════════════════════════════

🎯 BENEFITS:

✓ Cleaner, less cluttered interface
✓ Focus on essential information
✓ Quick access to full details when needed
✓ Customizable per user preference
✓ No loss of functionality - all data still accessible

═══════════════════════════════════════════════════════════════════════════════════════
""")

if __name__ == '__main__':
    show_new_features()
