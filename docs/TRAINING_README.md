# Agent Training Documentation

Dokumentasi lengkap untuk melatih Radira AI Agent menggunakan ChromaDB vector memory.

## 📖 Dokumentasi

### 1. [Panduan Lengkap](CHROMADB_TRAINING_GUIDE.md)
Panduan komprehensif yang mencakup:
- Arsitektur sistem learning
- 6+ metode training yang tersedia
- Best practices & recommendations
- Step-by-step implementation
- Monitoring & evaluasi

**Baca ini:** Jika Anda ingin memahami secara mendalam bagaimana training bekerja.

### 2. [Quick Reference](TRAINING_QUICK_REFERENCE.md)
Referensi cepat berisi:
- Code snippets siap pakai
- Perintah monitoring
- Troubleshooting tips
- Maintenance schedule

**Baca ini:** Untuk referensi cepat saat coding.

### 3. [Contoh Praktis](../examples/training_examples.py)
Script Python yang bisa langsung dijalankan:
- 7 contoh berbeda
- Lengkap dengan output
- Siap pakai

**Jalankan ini:** Untuk melihat training in action.

---

## 🚀 Quick Start

### Opsi 1: Langsung Pakai (Zero Configuration)

```python
# Agent sudah otomatis belajar dari setiap task!
# Tidak perlu konfigurasi tambahan.

# Optional: Monitor progress
from agent.learning.learning_manager import get_learning_manager
learning_mgr = get_learning_manager()

stats = learning_mgr.get_learning_statistics()
print(f"Success Rate: {stats['overall_success_rate']:.1%}")
print(f"Total Experiences: {stats['total_experiences']}")
```

### Opsi 2: Bootstrap dengan Domain Knowledge

```python
from agent.state.memory_manager import get_memory_manager

mem_mgr = get_memory_manager()

# Inject lessons
mem_mgr.add_lesson(
    lesson="Always validate HTML before deployment",
    context="Web development",
    category="quality_assurance",
    importance=0.9
)

# Inject strategies
mem_mgr.add_strategy(
    strategy="Read → Validate → Edit → Verify",
    task_type="file_modification",
    success_rate=0.95
)
```

### Opsi 3: Run Examples

```bash
# Show learning dashboard
python examples/training_examples.py --example dashboard

# Bootstrap agent
python examples/training_examples.py --example bootstrap

# Run all examples
python examples/training_examples.py --example all
```

---

## 📊 Metode Training Available

| Metode | Auto? | Difficulty | Use Case |
|--------|-------|------------|----------|
| **Experience-Based Learning** | ✅ | ⭐ Easy | Semua task (Recommended) |
| **Error-Driven Learning** | ⚠️ Semi | ⭐⭐ Medium | Improve reliability |
| **Guided Learning** | ❌ | ⭐⭐ Medium | Bootstrap agent |
| **Batch Import/Export** | ❌ | ⭐ Easy | Clone/backup |
| **Retrieval-Augmented (RAG)** | ✅ | ⭐⭐⭐ Advanced | Leverage past knowledge |
| **Active Learning** | ⚠️ Semi | ⭐⭐⭐ Advanced | Continuous optimization |

**Legend:**
- ✅ Auto = Berjalan otomatis
- ⚠️ Semi = Perlu trigger manual kadang-kadang
- ❌ = Fully manual

---

## 🎯 Recommended Training Pipeline

### Phase 1: Bootstrap (Hari 1)
```python
# 1. Inject domain knowledge
mem_mgr = get_memory_manager()
mem_mgr.add_lesson(...)
mem_mgr.add_strategy(...)

# 2. Import pre-trained knowledge (optional)
# mem_mgr.import_memory(Path("pretrained.json"))
```

### Phase 2: Active Learning (Minggu 1-4)
```python
# Agent belajar otomatis dari setiap task
# Anda hanya perlu:

# Weekly: Error analysis
learning_mgr.learn_from_errors()

# Check progress
stats = learning_mgr.get_learning_statistics()
```

### Phase 3: Optimization (Ongoing)
```python
# Weekly: Review suggestions
suggester = get_self_improvement_suggester()
suggestions = suggester.get_improvement_suggestions()

# Monthly: Backup
mem_mgr.export_all_memory(Path(f"backup_{datetime.now():%Y%m}.json"))

# As needed: Performance analysis
analysis = suggester.analyze_performance()
```

---

## 📈 Monitoring

### Quick Health Check
```bash
python examples/training_examples.py --example dashboard
```

### Detailed Monitoring
```python
from agent.learning.learning_manager import get_learning_manager
from agent.learning.self_improvement import get_self_improvement_suggester

learning_mgr = get_learning_manager()
suggester = get_self_improvement_suggester()

# Statistics
stats = learning_mgr.get_learning_statistics()
print(f"Success Rate: {stats['overall_success_rate']:.1%}")
print(f"Experiences: {stats['total_experiences']}")
print(f"Lessons: {stats['total_lessons']}")

# Performance
analysis = suggester.analyze_performance()
print(f"Efficiency: {analysis['efficiency_metrics']['efficiency_rating']}")

# Suggestions
for sug in suggester.get_improvement_suggestions():
    print(f"[{sug['priority']}] {sug['suggestion']}")

# Errors
error_summary = learning_mgr.get_error_summary()
print(error_summary)
```

---

## 🔧 Maintenance Tasks

### Weekly Tasks
```python
# 1. Error learning
learning_mgr.learn_from_errors()

# 2. Check statistics
stats = learning_mgr.get_learning_statistics()

# 3. Review suggestions
suggestions = suggester.get_improvement_suggestions()
```

### Monthly Tasks
```python
# 1. Backup memory
from datetime import datetime
from pathlib import Path

backup_file = Path(f"backups/memory_{datetime.now():%Y%m}.json")
mem_mgr.export_all_memory(backup_file)

# 2. Performance report
report = suggester.get_learning_progress_report()

# 3. Error analysis
error_analysis = learning_mgr.analyze_error_patterns(time_window_days=30)
```

---

## 🐛 Troubleshooting

### ChromaDB tidak tersedia
```bash
# Install ChromaDB
pip install chromadb

# Verify
python -c "from agent.state.memory import get_vector_memory; vm = get_vector_memory(); print(f'Available: {vm.available}')"
```

### Success rate rendah
```python
# Get actionable suggestions
suggestions = suggester.get_improvement_suggestions()
for sug in suggestions:
    if sug['priority'] in ['critical', 'high']:
        print(f"[{sug['priority'].upper()}] {sug['suggestion']}")
```

### Memory terlalu besar
```python
# Check size
stats = mem_mgr.get_all_statistics()
print(f"Experiences: {stats['vector_memory']['total_experiences']}")

# Export old data
mem_mgr.export_all_memory(Path("archive.json"))

# Clear if needed (WARNING: Cannot be undone!)
# mem_mgr.clear_all_memory()
```

---

## 📚 File Structure

```
radira/
├── docs/
│   ├── TRAINING_README.md           ← You are here
│   ├── CHROMADB_TRAINING_GUIDE.md   ← Full guide
│   └── TRAINING_QUICK_REFERENCE.md  ← Quick reference
├── examples/
│   └── training_examples.py         ← Runnable examples
├── agent/
│   ├── learning/
│   │   ├── learning_manager.py      ← Main learning orchestrator
│   │   ├── reflection_engine.py     ← Task reflection
│   │   └── self_improvement.py      ← Performance analysis
│   └── state/
│       ├── memory.py                ← ChromaDB vector memory
│       ├── memory_manager.py        ← Memory management tools
│       └── error_memory.py          ← Error tracking
└── workspace/
    └── .memory/                     ← ChromaDB storage
```

---

## 🎓 Learning Path

**Beginner:**
1. Read [Quick Reference](TRAINING_QUICK_REFERENCE.md)
2. Run `python examples/training_examples.py --example dashboard`
3. Let agent learn automatically
4. Weekly: Run error learning

**Intermediate:**
1. Read [Full Guide](CHROMADB_TRAINING_GUIDE.md)
2. Run all examples: `python examples/training_examples.py --example all`
3. Bootstrap with domain knowledge
4. Set up monitoring dashboard

**Advanced:**
1. Customize training pipeline
2. Implement domain-specific learning strategies
3. Optimize ChromaDB configuration
4. Build automated monitoring & alerting

---

## 💡 Tips & Best Practices

### DO ✅
- Let agent learn automatically from every task
- Run error analysis weekly
- Backup memory monthly
- Use descriptive task names
- Include context in metadata
- Monitor success rate trends

### DON'T ❌
- Don't disable automatic learning
- Don't use vague task descriptions
- Don't ignore error patterns
- Don't clear memory without backup
- Don't forget to monitor progress

---

## 🆘 Need Help?

1. **Quick answers:** Check [Quick Reference](TRAINING_QUICK_REFERENCE.md)
2. **Detailed info:** Read [Full Guide](CHROMADB_TRAINING_GUIDE.md)
3. **See it in action:** Run `examples/training_examples.py`
4. **Troubleshooting:** See troubleshooting section above

---

## 🎉 Get Started Now!

```bash
# Option 1: Show dashboard (recommended)
python examples/training_examples.py --example dashboard

# Option 2: Run all examples
python examples/training_examples.py --example all

# Option 3: Just let it learn (zero config)
# Agent already learning automatically! ✨
```

---

**Remember:** Agent sudah belajar otomatis dari setiap task. Anda hanya perlu:
1. Jalankan tasks seperti biasa
2. Weekly: Error learning
3. Monthly: Backup

**That's it!** 🚀

---

**Created:** 2025-11-15
**Version:** 1.0
**Agent:** Radira AI Agent with ChromaDB Learning
