# ZeroLog Viewer - Feature Documentation

## Application Screenshots and Features

### Main Window Layout

```
┌─────────────────────────────────────────────────────────────────┐
│ File                                                             │
├─────────────────────────────────────────────────────────────────┤
│ [Open File]  Search: [_______________] [Clear]                  │
├─────────────────────────────────────────────────────────────────┤
│ time              │ level │ message                │ ...         │
│ ══════════════════│═══════│════════════════════════│═════════   │
│ 2025-10-20T17:... │ debug │ Device found           │ ...         │
│ 2025-10-20T17:... │ info  │ Connection established │ ...         │
│ 2025-10-20T17:... │ warn  │ High latency detected  │ ...         │
│ 2025-10-20T17:... │ error │ Failed to authenticate │ ...         │
│                   │       │                        │             │
├─────────────────────────────────────────────────────────────────┤
│ Loaded 6 log entries from sample_logs.jsonl                     │
└─────────────────────────────────────────────────────────────────┘
```

## Key Features Implemented

### 1. JSONL File Loading
- **File → Open JSONL File** menu or **Open File** button
- Supports `.jsonl`, `.json`, and `.log` file extensions
- Automatic parsing of JSON Lines format
- Error handling for malformed JSON

### 2. Automatic Column Sizing
- Columns automatically detect their optimal width based on:
  - Column header text length
  - Content in the first 100 rows (for performance)
- Width limits: minimum 50px, maximum 400px
- Columns are resizable by dragging borders

### 3. Time-Based Indexing
- Logs are automatically sorted by the `time` field on load
- ISO 8601 timestamp format support
- Maintains chronological order for easy timeline analysis

### 4. Sortable Columns
- Click any column header to sort
- Click again to reverse sort order
- Smart sorting:
  - Timestamps parsed as dates
  - Numbers parsed as numeric values
  - Text sorted case-insensitively
- Status bar shows current sort order

### 5. Search Functionality
- Real-time search across all fields
- Case-insensitive matching
- Updates immediately as you type
- Status bar shows match count (e.g., "Found 5 of 100 log entries")
- **Clear** button to reset search

### 6. Color-Coded Log Levels
- **Debug**: Gray (#A0A0A0)
- **Info**: Blue (#4A90E2)
- **Warn/Warning**: Orange (#F5A623)
- **Error**: Red (#E74C3C)
- **Fatal/Panic**: Dark Red (#8B0000)

### 7. Column Priority
Columns are automatically ordered with priority:
1. `time` (first)
2. `level` (second)
3. `message` (third)
4. All other fields (alphabetically)

## Usage Examples

### Opening a File
1. Click **Open File** button
2. Select your JSONL file
3. Logs appear immediately with appropriate colors

### Searching
1. Type search term in the search box
2. Results filter in real-time
3. Search matches any field in the log entry

### Sorting
1. Click column header (e.g., "level")
2. Click again to reverse order
3. Status bar shows: "Sorted by 'level' (ascending/descending)"

### Adjusting Columns
1. Hover over column border
2. Cursor changes to resize cursor
3. Drag to desired width

## Sample Data Format

The viewer accepts standard JSONL format:

```json
{"level":"debug","time":"2025-10-20T17:19:16Z","message":"Device found"}
{"level":"info","time":"2025-10-20T17:19:17Z","message":"Connection OK"}
```

Each line is a complete JSON object. Any fields present in the JSON will become columns in the viewer.

## Performance

- Efficiently handles large files (thousands of entries)
- Column width calculated from sample (first 100 rows)
- Optimized TreeView updates
- Responsive UI even with many columns

## Cross-Platform Support

Built with tkinter (Python's standard GUI library):
- ✅ **Windows** 7, 8, 10, 11
- ✅ **macOS** 10.12+
- ✅ **Linux** (all major distributions with Python)

No external GUI dependencies required!
