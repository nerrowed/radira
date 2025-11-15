# Memory Training Script

Script untuk menambahkan pengetahuan dasar ke memory system tentang tools, workflows, dan best practices.

## 📋 Overview

Script `train_memory.py` menambahkan pengetahuan ke ChromaDB memory system tentang:
- ✅ Cara penggunaan tools (file_system, terminal, pentest)
- ✅ Lokasi file output dan script
- ✅ Cara membaca output
- ✅ Best practices untuk berbagai operasi
- ✅ Workflow patterns untuk pentest

## 🚀 Usage

### Training Semua Module

```bash
python train_memory.py
```

atau dengan module spesifik:

```bash
python train_memory.py --module all
```

### Export Training Data

Export semua training data ke file untuk backup atau sharing:

```bash
# Export ke JSON (default)
python train_memory.py --export training_data.json

# Export ke YAML
python train_memory.py --export training_data.yaml --format yaml
```

**Export Format:**
```json
{
  "version": "1.0",
  "exported_at": "2025-11-15T14:52:45.123456",
  "experiences": [
    {
      "task": "Membaca file output pentest",
      "actions": ["file_system.list", "file_system.read"],
      "outcome": "Berhasil membaca file",
      "success": true,
      "timestamp": "2025-11-15T14:52:45.123456"
    }
  ],
  "lessons": [
    {
      "lesson": "File system tool menggunakan path relatif dari workspace",
      "context": "File operations",
      "category": "tool_usage",
      "importance": 0.9,
      "timestamp": "2025-11-15T14:52:45.123456"
    }
  ],
  "strategies": [
    {
      "strategy": "List directory dulu sebelum read file",
      "task_type": "file_operations",
      "success_rate": 0.95,
      "context": "Reading files from output directories"
    }
  ]
}
```

### Import Training Data

Import training data dari file (merge dengan data existing):

```bash
# Import dari JSON
python train_memory.py --import training_data.json

# Import dari YAML
python train_memory.py --import training_data.yaml
```

**Import akan:**
- ✅ Validate data structure
- ✅ Merge dengan data existing (default)
- ✅ Report jumlah items yang diimport
- ✅ Show errors jika ada data invalid

**Output example:**
```
📥 Importing training data from training_data.json...
✅ Imported 15 experiences, 25 lessons, 8 strategies
```

### Training Module Spesifik

```bash
# Tool usage patterns
python train_memory.py --module tools

# File operations
python train_memory.py --module files

# Terminal operations
python train_memory.py --module terminal

# Output locations
python train_memory.py --module outputs

# Reading outputs
python train_memory.py --module reading

# Pentest workflows
python train_memory.py --module pentest

# Best practices
python train_memory.py --module practices
```

## 📚 Training Modules

### 1. Tool Usage (`--module tools`)

Menambahkan pengetahuan tentang:
- File System Tool: cara menggunakan path relatif, list directory, read file
- Terminal Tool: cara menggunakan httpx, check_output parameter
- Pentest Tool: cara menggunakan subdomain enumeration, output locations

**Contoh Lessons:**
- "File system tool menggunakan path relatif dari workspace"
- "httpx command: 'httpx -l <file> -o <output>' untuk filter URL aktif"
- "Pentest tool menyimpan output ke workspace/pentest_output/"

### 2. File Operations (`--module files`)

Menambahkan pengetahuan tentang:
- Path resolution (relatif vs absolute)
- File reading workflow
- Output file locations
- File search patterns

**Contoh Lessons:**
- "Path untuk file_system tool adalah relatif dari workspace"
- "Selalu list directory dulu sebelum read"
- "File output pentest biasanya di workspace/pentest_output/"

### 3. Terminal Operations (`--module terminal`)

Menambahkan pengetahuan tentang:
- httpx command usage
- Terminal tool parameters
- Input/output handling

**Contoh Lessons:**
- "httpx command untuk filter URL aktif: 'httpx -l <input_file> -o <output_file>'"
- "Selalu set check_output=true saat menggunakan terminal tool"
- "Command httpx bisa membaca dari stdin atau file"

### 4. Output Locations (`--module outputs`)

Menambahkan pengetahuan tentang:
- Lokasi direktori output
- File naming conventions
- File types per directory

**Output Directories:**
- `workspace/pentest_output/` - Output pentest (subdomains.txt, scan_results.txt)
- `workspace/generated_web/` - Generated web files (.html, .css, .js)
- `workspace/generated_code/` - Generated code files (.py, .js, .html)

### 5. Reading Outputs (`--module reading`)

Menambahkan pengetahuan tentang:
- Format file output
- Parsing output
- Processing workflow

**Contoh Lessons:**
- "File output pentest biasanya berisi satu item per line"
- "File subdomain format: satu subdomain per line"
- "File output httpx berisi URL dengan status code"

### 6. Pentest Workflows (`--module pentest`)

Menambahkan pengetahuan tentang:
- Complete workflows untuk pentest operations
- Step-by-step strategies
- Best practices

**Workflows:**
1. **Subdomain Enumeration**: subfinder → save → read → filter
2. **Filter Active URLs**: read subdomain → httpx → save → read results
3. **Read Previous Output**: list → search → read

### 7. Best Practices (`--module practices`)

Menambahkan pengetahuan tentang:
- Safety practices
- Path handling
- Workflow best practices
- Error prevention

**Contoh Lessons:**
- "Selalu verifikasi path sebelum operasi file"
- "Path untuk file_system tool harus relatif dari workspace root"
- "Saat menggunakan terminal tool, pastikan input file sudah ada"

## 📊 Output

Setelah training, script akan menampilkan:

```
✅ Training completed!

📊 Memory Statistics:
   Experiences: 15
   Lessons: 25
   Strategies: 8
```

## 🔍 Verifikasi

Untuk melihat hasil training, gunakan:

```bash
python manage_memory.py stats
```

Atau query memory:

```bash
python manage_memory.py search --query "cara membaca file output pentest"
```

## 🎯 Use Cases

### Use Case 1: Training Awal Setup

Saat pertama kali setup system, jalankan training lengkap:

```bash
python train_memory.py --module all
```

Ini akan menambahkan semua pengetahuan dasar ke memory system.

### Use Case 2: Update Knowledge

Jika ada perubahan di tools atau workflow, jalankan module spesifik:

```bash
# Update knowledge tentang terminal operations
python train_memory.py --module terminal
```

### Use Case 3: Custom Training

Edit `train_memory.py` untuk menambahkan knowledge custom sesuai kebutuhan.

## 📝 Customization

Untuk menambahkan knowledge custom, edit `train_memory.py`:

```python
def train_custom_knowledge(self):
    """Tambahkan knowledge custom."""
    self.memory_manager.add_lesson(
        lesson="Your custom lesson here",
        context="Custom context",
        category="custom",
        importance=0.9
    )
```

Lalu panggil di `train_all()`:

```python
def train_all(self):
    # ... existing code ...
    self.train_custom_knowledge()
```

## 🔄 Re-training

Training bisa dijalankan berkali-kali. Memory system akan:
- Menambahkan knowledge baru
- Tidak menghapus knowledge lama
- Update jika ada duplikasi (berdasarkan similarity)

## ⚠️ Notes

1. **ChromaDB Required**: Training memerlukan ChromaDB. Pastikan sudah terinstall:
   ```bash
   pip install chromadb
   ```

2. **Workspace Setup**: Pastikan workspace directory sudah ada:
   ```bash
   workspace/
   ├── pentest_output/
   ├── generated_web/
   └── generated_code/
   ```

3. **Memory Persistence**: Knowledge yang ditambahkan akan tersimpan di:
   ```
   workspace/.memory/
   ```

## 🐛 Troubleshooting

### Error: ChromaDB not available
```bash
pip install chromadb
```

### Error: Workspace not found
Pastikan `WORKING_DIRECTORY` di settings sudah benar.

### Error: Import errors
Pastikan semua dependencies terinstall:
```bash
pip install -r requirements.txt
```

## 📚 Related Documentation

- [Memory Management README](MEMORY_MANAGEMENT_README.md)
- [Learning System](LEARNING_SYSTEM.md)
- [Error Learning System](ERROR_LEARNING_SYSTEM.md)

