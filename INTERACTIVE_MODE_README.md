# Interactive Memory Management Mode

## Overview

**Interactive Mode** adalah versi user-friendly dari Memory Management System dengan menu-driven interface. Tidak perlu menghafal command-line arguments - cukup pilih dari menu!

## Features

✅ **Menu-Driven Interface** - Navigasi mudah dengan numbered menu
✅ **Colored Output** - Visual feedback dengan ANSI colors
✅ **Interactive Prompts** - Guided input untuk setiap operasi
✅ **Real-time Feedback** - Success/error messages yang jelas
✅ **Confirmation Dialogs** - Proteksi untuk operasi destructive
✅ **Clear Screen** - Clean interface tanpa clutter
✅ **Help System** - Built-in help dan tips

## Quick Start

```bash
# Launch interactive mode
python manage_memory_interactive.py
```

## Main Menu

```
============================================================
            RADIRA - Memory Management System
============================================================

Main Menu:

  1. List Memory
  2. Search Memory
  3. Add Memory
  4. Delete Memory
  5. Statistics
  6. Export/Import
  7. Clear Memory
  8. Help
  9. Exit

Select option (1-9):
```

## Usage Guide

### 1. List Memory

**What it does:** View memory items with filters

**Steps:**
1. Select `1` from main menu
2. Choose memory type:
   - Context Memory (tracking AI actions)
   - Experiences (task history)
   - Lessons Learned (knowledge)
   - Strategies (successful approaches)
3. Enter filters (optional):
   - Limit: number of items to show
   - Status/Category: filter by specific type
4. View results

**Example Flow:**
```
List Memory > Context Memory > Limit: 10 > Status: success
→ Shows 10 most recent successful actions
```

### 2. Search Memory

**What it does:** Search across all memory types with one query

**Steps:**
1. Select `2` from main menu
2. Enter search query (e.g., "file operations")
3. Specify results per type (default: 5)
4. View results grouped by memory type

**Example Flow:**
```
Search Memory > Query: "error" > Results: 10
→ Shows errors from all memory types
```

### 3. Add Memory

**What it does:** Manually add new memory items

**Steps:**
1. Select `3` from main menu
2. Choose what to add:
   - Experience
   - Lesson
   - Strategy
3. Fill in required fields
4. Confirm addition

**Example - Add Lesson:**
```
Add Memory > Add Lesson
→ Lesson text: Always validate file paths
→ Context: File operations
→ Category: file_operations
→ Importance: 0.9
✓ Added lesson: lesson_123456
```

### 4. Delete Memory

**What it does:** Remove specific memory items

**Steps:**
1. Select `4` from main menu
2. Choose memory type
3. Enter item ID (get from list command)
4. Confirm deletion

**Safety:** Asks for confirmation before deleting

**Example:**
```
Delete Memory > Delete Context Event
→ Enter ID: evt_1763054067
→ Confirm? y
✓ Deleted: evt_1763054067
```

### 5. Statistics

**What it does:** View comprehensive memory statistics

**Shows:**
- Total events/items per type
- Status breakdown (success/error/completed)
- Most common actions
- Storage backend status
- Storage paths

**Example Output:**
```
[Context Memory]
  Total Events: 22
  ChromaDB: Available
  Status Breakdown:
    • success: 15
    • error: 5
    • completed: 2

[Vector Memory]
  Experiences: 45
  Lessons: 23
  Strategies: 12
```

### 6. Export/Import

**What it does:** Backup and restore memory

#### Export Memory:
1. Select `6 > 1` (Export)
2. Enter filename (default: memory_backup.json)
3. Wait for export to complete
4. Check file size

#### Import Memory:
1. Select `6 > 2` (Import)
2. Enter filename
3. Confirm import (adds to existing memory)
4. View import counts

**Use Cases:**
- Regular backups
- Transfer memory between systems
- Restore after clearing

### 7. Clear Memory

**What it does:** Remove old or all memory

⚠️ **WARNING:** Cannot be undone!

**Options:**
1. Clear Context Only - Removes only context tracking
2. Clear ALL Memory - Removes everything

**Safety Features:**
- Red warning message
- Multiple confirmation prompts
- Shows what will be deleted

**Recommended Workflow:**
```
1. Export memory first (backup)
2. Clear memory
3. Verify with statistics
4. Import if needed to restore
```

### 8. Help

**What it does:** Display help information

**Shows:**
- System overview
- Feature descriptions
- Usage tips
- Keyboard shortcuts

### 9. Exit

**What it does:** Exit the program safely

- Asks for confirmation
- Ensures clean exit

## Color Guide

Interactive mode uses colors for better readability:

- 🔵 **Cyan/Blue** - Headers, info, numbers
- 🟢 **Green** - Success messages, checkmarks
- 🔴 **Red** - Errors, warnings, destructive actions
- 🟡 **Yellow** - Warnings, prompts, back options
- **Bold** - Important text, menu options

## Keyboard Shortcuts

- **Enter** - Continue after viewing results
- **Ctrl+C** - Cancel current operation (returns to main menu)
- **0** - Back to previous menu (in sub-menus)
- **9** - Exit program (from main menu)

## Tips & Best Practices

### Regular Maintenance

```bash
# Weekly routine:
1. Check statistics
2. Export backup
3. Clear old context
4. Review lessons
```

### Finding Information

```bash
# Quick search workflow:
1. Search with keyword
2. Note relevant IDs
3. Use list to see full details
4. Export specific items if needed
```

### Safe Deletion

```bash
# Before deleting:
1. List items to find ID
2. Export as backup
3. Delete item
4. Verify with statistics
```

### Batch Operations

```bash
# For multiple operations:
1. Export current state
2. Perform operations
3. Verify results
4. Keep export as backup
```

## Comparison: CLI vs Interactive

### Command-Line Mode (`manage_memory.py`)

✅ **Best for:**
- Scripting and automation
- Quick one-off commands
- Integration with other tools
- Advanced users

```bash
python manage_memory.py list context --limit 10
python manage_memory.py search "error"
```

### Interactive Mode (`manage_memory_interactive.py`)

✅ **Best for:**
- Exploratory browsing
- Learning the system
- Complex workflows
- Visual feedback
- Beginners

```bash
python manage_memory_interactive.py
# Then navigate with menu
```

## Example Sessions

### Session 1: Inspection

```
1. Launch interactive mode
2. Select "5" (Statistics)
   → See: 22 context events, 45 experiences
3. Select "1" (List Memory) > "1" (Context)
   → Limit: 10, Status: all
   → Review recent AI actions
4. Select "2" (Search)
   → Query: "file"
   → See all file-related operations
5. Select "9" (Exit)
```

### Session 2: Cleanup

```
1. Launch interactive mode
2. Select "6" (Export/Import) > "1" (Export)
   → File: backup_before_clean.json
3. Select "7" (Clear Memory) > "1" (Clear Context)
   → Confirm: y
4. Select "5" (Statistics)
   → Verify: Context events reduced
5. Select "9" (Exit)
```

### Session 3: Adding Knowledge

```
1. Launch interactive mode
2. Select "3" (Add Memory) > "2" (Add Lesson)
   → Lesson: Always validate input
   → Context: Data validation
   → Category: validation
   → Importance: 0.9
3. Select "3" (Add Memory) > "3" (Add Strategy)
   → Strategy: Use try-catch blocks
   → Task type: error handling
   → Success rate: 0.95
4. Select "1" (List Memory) > "3" (Lessons)
   → Verify new lesson appears
5. Select "9" (Exit)
```

## Troubleshooting

### Colors Not Showing

**Problem:** No colors in output

**Solutions:**
1. Use terminal with ANSI support (most modern terminals)
2. On Windows: Use Windows Terminal or PowerShell
3. Alternative: Use command-line mode without colors

### ChromaDB Warnings

**Problem:** "ChromaDB not available" messages

**Solution:**
```bash
pip install chromadb
```

**Note:** System still works without ChromaDB (JSON fallback)

### Menu Not Clearing

**Problem:** Old text remains on screen

**Solution:**
- Ensure terminal supports clear command
- Try maximizing terminal window
- Use command-line mode if issues persist

### Input Not Working

**Problem:** Input prompts don't accept text

**Solutions:**
1. Check terminal is in interactive mode
2. Don't run in background
3. Ensure stdin is not redirected

## Integration with Main System

Interactive mode uses the same backend as CLI mode:

```
manage_memory_interactive.py
             ↓
     MemoryManager
             ↓
    ┌────────┴────────┐
    ↓                 ↓
ContextTracker   VectorMemory
    ↓                 ↓
   JSON          ChromaDB
```

**This means:**
- Changes in interactive mode affect CLI mode
- Both modes share the same data
- Use whichever is convenient

## Performance

- **Fast:** Direct memory access, no network calls
- **Efficient:** Loads only what you need
- **Responsive:** Instant menu navigation
- **Lightweight:** ~500 lines of Python

## Security Notes

⚠️ **Important:**
- Memory contains sensitive task information
- Backup files are unencrypted JSON
- Secure your backup files appropriately
- Don't commit memory files to public repos

## Future Enhancements

Planned features:
- 🔄 Auto-refresh for statistics
- 📊 Visual charts for memory distribution
- 🔍 Advanced search filters
- 📝 Edit existing memory items
- 🔗 Link related memory items
- 📤 Export to multiple formats (CSV, Markdown)

## Quick Reference Card

```
╔══════════════════════════════════════╗
║   Interactive Memory Management      ║
╠══════════════════════════════════════╣
║ 1 - List Memory                      ║
║ 2 - Search Memory                    ║
║ 3 - Add Memory                       ║
║ 4 - Delete Memory                    ║
║ 5 - Statistics                       ║
║ 6 - Export/Import                    ║
║ 7 - Clear Memory (⚠️ Destructive)    ║
║ 8 - Help                             ║
║ 9 - Exit                             ║
╠══════════════════════════════════════╣
║ 0 - Back (in sub-menus)              ║
║ Ctrl+C - Cancel operation            ║
╚══════════════════════════════════════╝
```

## Support

For issues or questions:
1. Check this documentation
2. Use option "8" (Help) in interactive mode
3. Review `MEMORY_MANAGEMENT_README.md` for API details
4. Check terminal compatibility for color issues

---

**Created by:** Nerrow
**Date:** 2025-11-13
**Version:** 1.0.0
