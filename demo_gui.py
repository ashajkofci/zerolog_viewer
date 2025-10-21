#!/usr/bin/env python3
"""
Generate a text-based representation of what the GUI looks like.
Since we're in a headless environment, this creates a mock visualization.
"""

import json

def create_gui_mockup():
    """Create a text-based mockup of the GUI."""
    
    # Read sample data
    with open('sample_logs.jsonl', 'r') as f:
        logs = []
        for line in f:
            if line.strip():
                logs.append(json.loads(line))
    
    print("=" * 100)
    print("ZeroLog Viewer - GUI Preview (Text Representation)")
    print("=" * 100)
    print()
    
    # Menu bar
    print("┌" + "─" * 98 + "┐")
    print("│ File                                                                                               │")
    print("├" + "─" * 98 + "┤")
    
    # Toolbar
    print("│ [Open File]  Search: [                    ] [Clear]                                               │")
    print("├" + "─" * 98 + "┤")
    
    # Column headers
    print("│ Time                  │ Level   │ Message                      │ Device ID       │ Duration    │")
    print("│ ─────────────────────┼─────────┼──────────────────────────────┼─────────────────┼──────────── │")
    
    # Color legend
    colors = {
        'debug': '🔷',
        'info': '🔵',
        'warn': '🟠',
        'warning': '🟠',
        'error': '🔴',
        'fatal': '⚫',
    }
    
    # Display logs with color indicators
    for log in logs[:6]:  # Show first 6 entries
        time = log.get('time', '')[:19].replace('T', ' ')
        level = log.get('level', '')
        message = log.get('message', '')[:28]
        device = log.get('deviceID', '')[:15]
        duration = str(log.get('duration', ''))[:10]
        
        icon = colors.get(level, '⚪')
        
        # Pad fields
        time_pad = time.ljust(21)
        level_pad = (icon + ' ' + level).ljust(9)
        msg_pad = message.ljust(30)
        device_pad = device.ljust(17)
        duration_pad = duration.ljust(12)
        
        print(f"│ {time_pad}│ {level_pad}│ {msg_pad}│ {device_pad}│ {duration_pad}│")
    
    print("│" + " " * 98 + "│")
    print("├" + "─" * 98 + "┤")
    
    # Status bar
    print(f"│ Loaded {len(logs)} log entries from sample_logs.jsonl" + " " * 57 + "│")
    print("└" + "─" * 98 + "┘")
    print()
    
    # Color legend
    print("Color Legend:")
    print("  🔷 Debug (Gray)     🔵 Info (Blue)      🟠 Warn (Orange)")
    print("  🔴 Error (Red)      ⚫ Fatal (Dark Red)")
    print()
    
    print("Features Demonstrated:")
    print("  ✓ Automatic column sizing based on content")
    print("  ✓ Time-based ordering (chronological)")
    print("  ✓ Color-coded log levels with visual indicators")
    print("  ✓ Search functionality (type to filter)")
    print("  ✓ Sortable columns (click headers)")
    print("  ✓ Resizable columns (drag borders)")
    print()

if __name__ == '__main__':
    create_gui_mockup()
