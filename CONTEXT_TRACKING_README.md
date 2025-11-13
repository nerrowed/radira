# Context Chain Tracking System

## Deskripsi

Sistem **Context Chain Tracking** adalah fitur baru yang memungkinkan AI agent mengingat dan melacak urutan tindakan, perintah user, dan hasil dari setiap aksi yang diambil. Sistem ini menyelesaikan masalah di mana AI tidak dapat menjawab pertanyaan tentang tindakan sebelumnya.

## Masalah yang Diselesaikan

**Sebelumnya:**
```
User: "Baca file report.txt"
AI: (membuat file baru)
User: "Kenapa kamu buat file?"
AI: (tidak tahu bahwa perintah sebelumnya adalah membaca file)
```

**Sekarang:**
```
User: "Baca file report.txt"
AI: (membuat file baru karena tidak ditemukan)
User: "Kenapa kamu buat file?"
AI: "Saya membuat file karena perintah sebelumnya adalah membaca file report.txt,
     tapi file tersebut tidak ditemukan, jadi saya membuatnya."
```

## Arsitektur Sistem

### 1. Storage Dual-Layer
- **JSON Log** (`workspace/.context/context_log.json`): Penyimpanan cepat untuk akses sekuensial
- **ChromaDB** (`workspace/.context`): Storage vector untuk semantic search (opsional)

### 2. Komponen Utama

#### `context_tracker.py`
Modul utama yang menyediakan:

```python
from agent.state.context_tracker import get_context_tracker

tracker = get_context_tracker()

# Tambah event
tracker.add_event(
    user_command="Baca file report.txt",
    ai_action="file_system",
    result="Error: File not found",
    status="error",
    metadata={"iteration": 1}
)

# Ambil aksi terakhir
last = tracker.get_last_action()

# Ringkasan aksi terakhir
summary = tracker.summarize_recent_actions(n=5)

# Penjelasan aksi terakhir
explanation = tracker.explain_last_action()

# Cari konteks terkait (semantic search)
related = tracker.find_related_context("file operations", n_results=3)
```

### 3. Format Event

Setiap event disimpan dalam format:
```json
{
  "id": "evt_1699876543.123",
  "timestamp": "2025-11-13T12:00:00Z",
  "user_command": "Baca file report.txt",
  "ai_action": "file_system",
  "result": "Error: File not found",
  "status": "error",
  "metadata": {
    "iteration": 1,
    "action_input": "read report.txt"
  }
}
```

### 4. Integrasi dengan Orchestrator

Sistem terintegrasi otomatis dengan:
- `AgentOrchestrator` (orchestrator.py)
- `DualOrchestrator` (dual_orchestrator.py)

Setiap kali AI menjalankan tool atau memberikan final answer, sistem otomatis tracking:

```python
# Di orchestrator __init__
self.context_tracker = get_context_tracker() if enable_context_tracking else None

# Setiap tool execution
if self.enable_context_tracking and self.context_tracker:
    self.context_tracker.add_event(
        user_command=self.current_task,
        ai_action=action,
        result=observation,
        status=status,
        metadata={...}
    )
```

## Fitur Utama

### 1. `add_event()`
Menyimpan setiap event ke log dan ChromaDB dengan format JSON.

### 2. `get_last_action()`
Mengambil aksi terakhir yang dilakukan AI.

```python
last = tracker.get_last_action()
# Returns: {
#   "user_command": "...",
#   "ai_action": "...",
#   "result": "...",
#   "status": "..."
# }
```

### 3. `summarize_recent_actions(n=5)`
Membuat ringkasan dalam format human-readable:

```
Ringkasan aksi terakhir:
1. [12:00:00] ✗ User: 'Baca file...' → AI Action: file_system
2. [12:00:01] ✓ User: 'Baca file...' → AI Action: file_system
3. [12:00:02] ✓ User: 'Kenapa...' → AI Action: Final Answer
```

### 4. `explain_last_action()`
Memberikan penjelasan kontekstual tentang aksi terakhir:

```
Aksi terakhir:
- Perintah user: "Kenapa kamu buat file?"
- Aksi yang diambil: Final Answer
- Hasil: Saya membuat file karena...
- Status: completed

Alasan: Saya mengambil aksi 'Final Answer' sebagai respons...
```

### 5. `find_related_context(query, n_results=3)`
Semantic search untuk menemukan aksi terkait:

```python
# Cari semua operasi file
related = tracker.find_related_context("file operations", n_results=5)

# Cari error-error sebelumnya
errors = tracker.find_related_context("error", n_results=10)
```

### 6. `get_statistics()`
Statistik lengkap tentang tracking:

```python
stats = tracker.get_statistics()
# Returns:
# {
#   "total_events": 100,
#   "status_breakdown": {"success": 80, "error": 20},
#   "most_common_actions": {"file_system": 50, "terminal": 30},
#   "chromadb_available": True
# }
```

## Cara Menggunakan

### 1. Instalasi ChromaDB (Opsional)
```bash
pip install chromadb
```

Jika ChromaDB tidak tersedia, sistem otomatis fallback ke JSON-only mode.

### 2. Enable Context Tracking

Context tracking sudah otomatis aktif di orchestrator:

```python
# Di main.py
agent = AgentOrchestrator(
    enable_context_tracking=True  # Default: True
)
```

### 3. Running Test

```bash
python test_context_tracking.py
```

### 4. Mengakses Context dari Agent

Untuk menambahkan fitur query context di agent Anda:

```python
# Dalam tool atau method agent
from agent.state.context_tracker import get_context_tracker

tracker = get_context_tracker()

# Jika user bertanya tentang aksi sebelumnya
if "kenapa" in user_query.lower() or "mengapa" in user_query.lower():
    explanation = tracker.explain_last_action()
    return explanation

# Jika user bertanya "apa yang sudah kamu lakukan?"
if "apa yang" in user_query.lower() and "lakukan" in user_query.lower():
    summary = tracker.summarize_recent_actions(n=10)
    return summary
```

## Status Tracking

Sistem tracking status:
- `success`: Aksi berhasil
- `error`: Aksi gagal dengan error
- `completed`: Task selesai dengan final answer
- `incomplete`: Task tidak selesai (max iterations)
- `partial`: Sebagian berhasil (custom)

## Performa & Efisiensi

### Token Usage
- **Minimal overhead**: Hanya metadata yang disimpan, tidak full conversation
- **Result truncation**: Result dipotong max 500 karakter untuk efisiensi
- **In-memory cache**: Hanya 100 event terakhir di memory

### Storage
- **JSON log**: ~100 KB untuk 1000 events
- **ChromaDB**: ~10 MB untuk 1000 events dengan embeddings

### Query Speed
- `get_last_action()`: O(1) - instant
- `summarize_recent_actions()`: O(n) - very fast
- `find_related_context()`: O(log n) dengan ChromaDB, O(n) fallback

## File Changes

### New Files
- `agent/state/context_tracker.py` - Modul utama
- `test_context_tracking.py` - Test suite
- `CONTEXT_TRACKING_README.md` - Dokumentasi ini

### Modified Files
- `agent/core/orchestrator.py` - Integrasi tracking
- `agent/core/dual_orchestrator.py` - Integrasi tracking

## Use Cases

### 1. Debugging & Introspection
AI bisa menjelaskan mengapa mengambil keputusan tertentu.

### 2. Error Recovery
AI bisa melihat error sebelumnya dan menghindari kesalahan yang sama.

### 3. Multi-step Task Tracking
User bisa melihat progress lengkap task kompleks.

### 4. Conversational Context
AI bisa menjawab pertanyaan follow-up tentang tindakan sebelumnya.

## Contoh Output

```bash
$ python test_context_tracking.py

Test 1: Basic Context Tracking
Last Action:
  User Command: Kenapa kamu buat file?
  AI Action: Final Answer
  Result: Saya membuat file karena file report.txt tidak ditemukan
  Status: completed

Summary of Recent Actions:
1. [12:00:00] ✗ User: 'Baca file...' → AI Action: file_system
2. [12:00:01] ✓ User: 'Baca file...' → AI Action: file_system
3. [12:00:02] ✓ User: 'Kenapa...' → AI Action: Final Answer
```

## Future Enhancements

Potensi pengembangan:
1. **Clustering**: Grup similar actions untuk pattern recognition
2. **Anomaly Detection**: Deteksi tindakan yang tidak biasa
3. **Prediction**: Prediksi action selanjutnya based on history
4. **Export**: Export chain ke berbagai format (Markdown, PDF, etc.)
5. **Visualization**: UI untuk visualisasi action chain

## Credits

Created by: Nerrow
Date: 2025-11-13
Version: 1.0.0
