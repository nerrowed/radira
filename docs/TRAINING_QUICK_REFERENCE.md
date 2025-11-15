# ChromaDB Training Quick Reference

## 🚀 Quick Start (3 Langkah)

```python
# 1. Import learning manager
from agent.learning.learning_manager import get_learning_manager
learning_mgr = get_learning_manager()

# 2. Let agent learn automatically (sudah berjalan di background)
# Tidak perlu konfigurasi tambahan!

# 3. Optional: Periodic maintenance (weekly)
learning_mgr.learn_from_errors()  # Belajar dari error patterns
```

---

## 📋 Metode Training Ringkas

| Metode | Kapan Pakai | Complexity | Auto? |
|--------|-------------|------------|-------|
| **Experience-Based** | Semua task | ⭐ Easy | ✅ Yes |
| **Error-Driven** | Frequent errors | ⭐⭐ Medium | ⚠️ Semi |
| **Guided Learning** | Bootstrap agent | ⭐⭐ Medium | ❌ No |
| **Batch Import** | Clone/restore | ⭐ Easy | ❌ No |
| **Retrieval (RAG)** | Before new task | ⭐⭐⭐ Advanced | ✅ Yes |
| **Active Learning** | Optimization | ⭐⭐⭐ Advanced | ⚠️ Semi |

---

## 💻 Code Snippets

### Inject Domain Knowledge
```python
from agent.state.memory_manager import get_memory_manager
mem_mgr = get_memory_manager()

mem_mgr.add_lesson(
    lesson="Always validate input before processing",
    context="Security best practices",
    category="security",
    importance=0.9
)
```

### Learn from Task
```python
from agent.learning.learning_manager import get_learning_manager
learning_mgr = get_learning_manager()

learning_mgr.learn_from_task(
    task="Create login page",
    actions=["create_html", "add_form", "add_validation"],
    outcome="Login page created successfully",
    success=True
)
```

### Analyze Errors
```python
# Analyze error patterns
error_analysis = learning_mgr.analyze_error_patterns(time_window_days=7)

# Convert to lessons
learning_mgr.learn_from_errors()
```

### Get Relevant Experience
```python
insights = learning_mgr.get_relevant_experience(
    current_task="Fix authentication bug",
    n_results=5
)

print(insights['similar_experiences'])
print(insights['relevant_lessons'])
print(insights['recommended_strategies'])
```

### Monitor Progress
```python
from agent.learning.self_improvement import get_self_improvement_suggester
suggester = get_self_improvement_suggester()

# Get performance analysis
analysis = suggester.analyze_performance()
print(f"Success rate: {analysis['success_rate']:.1%}")

# Get suggestions
suggestions = suggester.get_improvement_suggestions()
for sug in suggestions:
    print(f"[{sug['priority']}] {sug['suggestion']}")
```

### Backup & Restore
```python
from pathlib import Path

# Export
mem_mgr.export_all_memory(Path("backup.json"))

# Import
counts = mem_mgr.import_memory(Path("backup.json"))
print(f"Imported {counts['experiences']} experiences")
```

---

## 📊 Monitoring Commands

```python
# Get statistics
stats = learning_mgr.get_learning_statistics()
print(f"Success Rate: {stats['overall_success_rate']:.1%}")
print(f"Total Experiences: {stats['total_experiences']}")

# Get error summary
error_summary = learning_mgr.get_error_summary()
print(error_summary)

# Get all memory stats
mem_stats = mem_mgr.get_all_statistics()
print(mem_stats)
```

---

## 🎯 Best Practices

### ✅ DO
- Enable automatic experience logging (default)
- Run error analysis weekly
- Backup memory monthly
- Monitor success rate trends
- Use specific, descriptive task names
- Include context in metadata

### ❌ DON'T
- Don't disable automatic learning
- Don't ignore error patterns
- Don't use vague task descriptions
- Don't forget to backup
- Don't clear memory without backup

---

## 🔧 Maintenance Schedule

| Task | Frequency | Command |
|------|-----------|---------|
| Error Learning | Weekly | `learning_mgr.learn_from_errors()` |
| Backup | Monthly | `mem_mgr.export_all_memory(...)` |
| Stats Review | Weekly | `learning_mgr.get_learning_statistics()` |
| Suggestions | Weekly | `suggester.get_improvement_suggestions()` |

---

## 🐛 Troubleshooting

### ChromaDB tidak tersedia
```python
# Check status
from agent.state.memory import get_vector_memory
vm = get_vector_memory()
print(f"Available: {vm.available}")

# If False, install ChromaDB
# pip install chromadb
```

### Memory penuh / terlalu besar
```python
# Check size
stats = mem_mgr.get_all_statistics()
print(stats)

# Export dan clear jika perlu
mem_mgr.export_all_memory(Path("backup.json"))
# mem_mgr.clear_all_memory()  # WARNING: Cannot be undone!
```

### Success rate rendah
```python
# Get suggestions
suggestions = suggester.get_improvement_suggestions()

# Check error patterns
error_analysis = learning_mgr.analyze_error_patterns()
print(error_analysis)
```

---

## 📚 Resources

- Full Guide: `docs/CHROMADB_TRAINING_GUIDE.md`
- Examples: `examples/training_examples.py`
- Code: `agent/learning/`, `agent/state/`

---

## 🎬 Run Examples

```bash
# Show dashboard
python examples/training_examples.py --example dashboard

# Bootstrap with domain knowledge
python examples/training_examples.py --example bootstrap

# Learn from tasks
python examples/training_examples.py --example learn_task

# Error learning
python examples/training_examples.py --example error_learning

# Run all examples
python examples/training_examples.py --example all
```

---

**Quick Tip:** Agent sudah otomatis belajar dari setiap task. Yang perlu Anda lakukan:
1. Jalankan tasks seperti biasa ✓
2. Weekly: `learning_mgr.learn_from_errors()` ✓
3. Monthly: Backup memory ✓

That's it! 🎉
