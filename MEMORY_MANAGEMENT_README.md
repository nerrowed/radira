# Memory Management System

## Deskripsi

**Memory Management System** adalah tool untuk mengelola semua memory yang disimpan dalam ChromaDB oleh AI agent. Sistem ini memungkinkan Anda untuk:

- 📋 List dan view semua memory (context, experiences, lessons, strategies)
- ➕ Menambahkan memory baru
- 🗑️ Menghapus memory tertentu
- 🔍 Search memory dengan semantic search
- 📊 Melihat statistik memory
- 💾 Export/import memory
- 🧹 Clear/reset memory

## Arsitektur

### Memory Types

1. **Context Memory** - Tracking urutan tindakan AI
   - User commands
   - AI actions
   - Results & status
   - Stored in: `workspace/.context/`

2. **Experiences** - Task execution history
   - Task descriptions
   - Actions taken
   - Outcomes (success/failure)
   - Stored in: ChromaDB collection "experiences"

3. **Lessons Learned** - Knowledge dari pengalaman
   - Lesson text
   - Context aplikasi
   - Category & importance
   - Stored in: ChromaDB collection "lessons_learned"

4. **Strategies** - Strategi yang berhasil
   - Strategy description
   - Task type
   - Success rate & usage count
   - Stored in: ChromaDB collection "successful_strategies"

## Instalasi

### Prerequisites

```bash
# Install ChromaDB (opsional, untuk semantic search)
pip install chromadb
```

Jika ChromaDB tidak tersedia, sistem akan fallback ke JSON-only mode dengan fungsionalitas terbatas.

## Penggunaan

### CLI Tool

#### 1. List Memory

```bash
# List context memory (10 terakhir)
python manage_memory.py list context --limit 10

# Filter context by status
python manage_memory.py list context --status success

# List experiences
python manage_memory.py list experiences --limit 20

# List only successful experiences
python manage_memory.py list experiences --success-only

# List lessons
python manage_memory.py list lessons --limit 15

# Filter lessons by category
python manage_memory.py list lessons --category file_operations

# List strategies
python manage_memory.py list strategies --limit 10

# Filter strategies by task type
python manage_memory.py list strategies --task-type "file operations"
```

**Output example:**
```
============================================================
                       Context Memory
============================================================

1. [2025-11-13 17:14:27] ✓
   ID: evt_1763054067.828598
   Command: Buat aplikasi web sederhana...
   Action: web_generator
   Status: success

2. [2025-11-13 17:14:27] ✗
   ID: evt_1763054067.828941
   Command: Baca file config.json...
   Action: file_system
   Status: error
```

#### 2. Search Memory

```bash
# Search across all memory types
python manage_memory.py search "file operations"

# Search with custom result limit
python manage_memory.py search "error handling" --limit 10
```

**Output example:**
```
============================================================
              Search Results for: 'file operations'
============================================================

[Context Memory]
1. file_system - Baca file config.json...
2. file_system - Buat file report.txt...

[Experiences]
1. ✓ Task: Create and read configuration file...
2. ✗ Task: Parse JSON file with validation...

[Lessons]
1. Always validate file paths before operations...
2. Check file permissions before writing...

[Strategies]
1. Use try-catch for all file operations...
```

#### 3. Delete Memory

```bash
# Delete context event
python manage_memory.py delete context evt_1763054067.828598

# Delete experience
python manage_memory.py delete experience exp_1763054120.123456

# Delete lesson
python manage_memory.py delete lesson lesson_1763055421.254475

# Delete strategy
python manage_memory.py delete strategy strat_1763054200.987654
```

#### 4. Add Memory

```bash
# Add experience
python manage_memory.py add experience \
    --task "Create config file" \
    --actions "validate_path,create_file,write_content" \
    --outcome "File created successfully" \
    --success

# Add lesson
python manage_memory.py add lesson \
    --lesson "Always validate file paths before operations" \
    --context "File system operations" \
    --category "file_operations" \
    --importance 0.9

# Add strategy
python manage_memory.py add strategy \
    --strategy "Use try-catch blocks for all file I/O" \
    --task-type "file operations" \
    --success-rate 0.95 \
    --context "Prevents crashes from file access errors"
```

#### 5. Statistics

```bash
# Show all memory statistics
python manage_memory.py stats
```

**Output example:**
```
============================================================
                     Memory Statistics
============================================================

[Context Memory]
  Total Events: 22
  ChromaDB: Available
  Status Breakdown:
    • success: 15
    • error: 5
    • completed: 2
  Most Common Actions:
    • file_system: 13
    • terminal: 6
    • Final Answer: 2

[Vector Memory]
  Experiences: 45
  Lessons: 23
  Strategies: 12
  Backend: chromadb
  Storage: workspace/.memory
```

#### 6. Export Memory

```bash
# Export all memory to JSON
python manage_memory.py export memory_backup.json

# Export with custom path
python manage_memory.py export /path/to/backup.json
```

**Export format:**
```json
{
  "context": [...],
  "experiences": [...],
  "lessons": [...],
  "strategies": [...],
  "statistics": {...},
  "exported_at": "2025-11-13T17:30:00Z"
}
```

#### 7. Import Memory

```bash
# Import memory from backup
python manage_memory.py import memory_backup.json

# Import from custom path
python manage_memory.py import /path/to/backup.json
```

**Output example:**
```
Importing memory from memory_backup.json...
✓ Import complete:
   Experiences: 45
   Lessons: 23
   Strategies: 12
```

#### 8. Clear Memory

```bash
# Clear context memory only
python manage_memory.py clear context

# Clear ALL memory (requires confirmation)
python manage_memory.py clear all
```

**Clear all prompt:**
```
⚠️  WARNING: This will delete ALL memory!
Type 'yes' to confirm: yes
Clearing all memory...
✓ context: Cleared
✓ experiences: Cleared
✓ lessons: Cleared
✓ strategies: Cleared
```

### Programmatic Usage

```python
from agent.state.memory_manager import get_memory_manager

# Initialize manager
manager = get_memory_manager()

# List context memory
events = manager.list_context_memory(limit=10, status_filter="success")

# Search across all memory
results = manager.search_all("file operations", n_results=5)

# Add new lesson
lesson_id = manager.add_lesson(
    lesson="Always validate input before processing",
    context="Data validation",
    category="validation",
    importance=0.85
)

# Delete experience
manager.delete_experience("exp_123456")

# Get statistics
stats = manager.get_all_statistics()

# Export memory
from pathlib import Path
manager.export_all_memory(Path("backup.json"))

# Clear all memory (use with caution!)
results = manager.clear_all_memory()
```

## API Reference

### MemoryManager Methods

#### Context Memory

- `list_context_memory(limit, status_filter)` - List context events
- `get_context_by_id(event_id)` - Get specific event
- `delete_context_by_id(event_id)` - Delete event
- `clear_all_context()` - Clear all context

#### Experiences

- `list_experiences(limit, success_only)` - List experiences
- `get_experience_by_id(exp_id)` - Get specific experience
- `add_experience(task, actions, outcome, success, metadata)` - Add experience
- `delete_experience(exp_id)` - Delete experience

#### Lessons

- `list_lessons(limit, category)` - List lessons
- `add_lesson(lesson, context, category, importance)` - Add lesson
- `delete_lesson(lesson_id)` - Delete lesson

#### Strategies

- `list_strategies(limit, task_type)` - List strategies
- `add_strategy(strategy, task_type, success_rate, context)` - Add strategy
- `delete_strategy(strategy_id)` - Delete strategy

#### Search & Query

- `search_all(query, n_results)` - Search across all memory types

#### Bulk Operations

- `get_all_statistics()` - Get statistics for all memory
- `clear_all_memory()` - Clear ALL memory (warning!)
- `export_all_memory(output_file)` - Export to JSON
- `import_memory(input_file)` - Import from JSON

## Use Cases

### 1. Debugging & Inspection

```bash
# Lihat apa yang agent lakukan
python manage_memory.py list context --limit 20

# Cari error tertentu
python manage_memory.py search "error"
```

### 2. Knowledge Management

```bash
# Tambahkan lesson dari pengalaman
python manage_memory.py add lesson \
    --lesson "Always check dependencies before running tasks" \
    --context "Task execution" \
    --importance 0.9

# Review lessons yang ada
python manage_memory.py list lessons
```

### 3. Backup & Restore

```bash
# Backup sebelum eksperimen
python manage_memory.py export backup_before_experiment.json

# Restore jika ada masalah
python manage_memory.py clear all
python manage_memory.py import backup_before_experiment.json
```

### 4. Cleaning Up

```bash
# Hapus context lama
python manage_memory.py clear context

# Hapus experience yang failed
# (perlu dilakukan manual per ID atau via script)
```

### 5. Analysis & Monitoring

```bash
# Monitor memory usage
python manage_memory.py stats

# Search pattern tertentu
python manage_memory.py search "loop detected"
```

## Best Practices

### 1. Regular Backups

```bash
# Backup daily
python manage_memory.py export "backup_$(date +%Y%m%d).json"
```

### 2. Clean Up Old Data

```bash
# Keep only recent context (manual cleanup per ID)
# Or periodically clear context:
python manage_memory.py clear context
```

### 3. Review Statistics

```bash
# Check memory usage weekly
python manage_memory.py stats
```

### 4. Document Important Lessons

```bash
# Manually add critical lessons
python manage_memory.py add lesson \
    --lesson "..." \
    --context "..." \
    --importance 1.0
```

### 5. Test Before Clearing

```bash
# Always export before clearing
python manage_memory.py export backup.json
python manage_memory.py clear all
```

## Troubleshooting

### ChromaDB Not Available

**Symptom:**
```
ChromaDB not available. Only JSON logging will be used.
```

**Solution:**
```bash
pip install chromadb
```

**Alternative:** Sistem tetap bekerja dengan JSON fallback, tapi tanpa semantic search.

### Cannot Delete Memory

**Symptom:**
```
✗ Failed to delete context: evt_123456
```

**Solutions:**
1. Check if ID exists: `python manage_memory.py list context`
2. Try clearing entire collection: `python manage_memory.py clear context`
3. Check file permissions in `workspace/.context/`

### Import Fails

**Symptom:**
```
✗ Failed to import memory
```

**Solutions:**
1. Verify JSON format is valid
2. Check file path exists
3. Ensure ChromaDB is available for experiences/lessons/strategies

### Memory Usage Too High

**Symptom:** Large files in `workspace/.context/` or `workspace/.memory/`

**Solutions:**
1. Export and clear old data:
   ```bash
   python manage_memory.py export archive.json
   python manage_memory.py clear all
   ```

2. Limit context tracking in code:
   ```python
   # In context_tracker.py, adjust max_recent_events
   self.max_recent_events = 50  # Default: 100
   ```

## Files Created

### New Files
- `agent/state/memory_manager.py` - Memory manager module
- `manage_memory.py` - CLI tool
- `MEMORY_MANAGEMENT_README.md` - Documentation

### Modified Files
None (fully additive system)

## Performance

### Storage

- **Context Memory**: ~1 KB per 10 events
- **Experiences**: ~2 KB per 10 experiences (with embeddings)
- **Lessons**: ~1 KB per 10 lessons
- **Strategies**: ~1 KB per 10 strategies

### Query Speed

- **List operations**: O(n) - Very fast
- **Search (with ChromaDB)**: O(log n) - Fast
- **Delete**: O(1) - Instant
- **Clear all**: O(n) - Depends on size

### Recommendations

- Keep context memory under 1000 events
- Export and clear periodically
- Use search instead of listing all items

## Security & Privacy

⚠️ **Important Notes:**

1. Memory files contain **sensitive information** about tasks and actions
2. Always **secure backup files** with proper permissions
3. Do not commit memory files to public repositories
4. Consider **encryption** for backups containing sensitive data

## Future Enhancements

Potential improvements:
1. **Auto-cleanup**: Automatic old data removal
2. **Compression**: Compress old backups
3. **Encryption**: Built-in backup encryption
4. **Web UI**: Browser-based memory management
5. **Analytics**: Advanced memory analytics dashboard
6. **Filters**: More advanced filtering options
7. **Batch operations**: Delete/modify multiple items at once

## Credits

Created by: Nerrow
Date: 2025-11-13
Version: 1.0.0
