# Panduan Metode Training untuk ChromaDB Agent

## 📚 Daftar Isi
1. [Arsitektur Sistem Learning](#arsitektur-sistem-learning)
2. [Metode Training yang Tersedia](#metode-training-yang-tersedia)
3. [Best Practices](#best-practices)
4. [Implementasi Step-by-Step](#implementasi-step-by-step)
5. [Monitoring & Evaluasi](#monitoring--evaluasi)

---

## 🏗️ Arsitektur Sistem Learning

Agent ini menggunakan **ChromaDB** sebagai vector database untuk menyimpan:

### 1. **Experiences Collection**
```python
# Menyimpan eksekusi task
- Task description
- Actions taken
- Outcome
- Success/failure status
- Metadata & context
```

### 2. **Lessons Learned Collection**
```python
# Menyimpan pelajaran yang dipetik
- Lesson text
- Context aplikasi
- Category
- Importance score
```

### 3. **Successful Strategies Collection**
```python
# Menyimpan strategi yang berhasil
- Strategy description
- Task type
- Success rate
- Usage count
```

---

## 🎯 Metode Training yang Tersedia

### **1. Experience-Based Learning (Recommended ⭐)**

**Apa itu?**
Agent belajar dari setiap task yang dijalankan, menyimpan pengalaman sukses dan gagal.

**Kapan digunakan?**
- Untuk semua jenis task
- Training berkelanjutan
- Paling cocok untuk production environment

**Cara Implementasi:**

```python
from agent.learning.learning_manager import get_learning_manager

# Initialize
learning_mgr = get_learning_manager()

# Setelah task selesai
learning_summary = learning_mgr.learn_from_task(
    task="Create a web page with contact form",
    actions=[
        "create_file: index.html",
        "write_content: HTML form",
        "verify_file_exists"
    ],
    outcome="Successfully created contact form page",
    success=True,
    errors=[],
    context={
        "task_type": "web_development",
        "complexity": "medium"
    }
)

print(f"Learned {learning_summary['lessons_count']} lessons")
print(f"Stored {learning_summary['strategies_count']} strategies")
```

**Keuntungan:**
- ✅ Otomatis dan tidak perlu manual intervention
- ✅ Belajar dari sukses DAN kegagalan
- ✅ Persistent storage di ChromaDB
- ✅ Vector search untuk retrieval cepat

**Kekurangan:**
- ⚠️ Membutuhkan waktu untuk akumulasi data
- ⚠️ Kualitas tergantung kualitas task execution

---

### **2. Error-Driven Learning (Recommended ⭐)**

**Apa itu?**
Agent secara khusus belajar dari error patterns dan membuat prevention strategies.

**Kapan digunakan?**
- Ketika sering muncul error yang sama
- Production debugging
- Improving reliability

**Cara Implementasi:**

```python
from agent.learning.learning_manager import get_learning_manager

learning_mgr = get_learning_manager()

# Analisis error patterns
error_analysis = learning_mgr.analyze_error_patterns(
    tool_name="filesystem",  # atau None untuk semua tools
    time_window_days=7
)

print(f"Total errors: {error_analysis['total_errors']}")
print(f"Top error types: {error_analysis['top_error_types']}")

# Konversi error patterns menjadi lessons
learning_result = learning_mgr.learn_from_errors()

print(f"Created {learning_result['lessons_created']} lessons from errors")
print(f"Created {learning_result['strategies_created']} prevention strategies")
```

**Keuntungan:**
- ✅ Fokus pada improvement area
- ✅ Mengurangi repeated mistakes
- ✅ Actionable recommendations
- ✅ Automatic pattern detection

**Kekurangan:**
- ⚠️ Hanya belajar dari error, tidak dari sukses

---

### **3. Guided Learning (Manual Injection)**

**Apa itu?**
Anda secara manual inject lessons, experiences, atau strategies ke dalam ChromaDB.

**Kapan digunakan?**
- Bootstrap agent dengan domain knowledge
- Transfer knowledge dari expert
- Quick start untuk use case spesifik

**Cara Implementasi:**

```python
from agent.state.memory_manager import get_memory_manager

mem_mgr = get_memory_manager()

# 1. Inject manual lesson
lesson_id = mem_mgr.add_lesson(
    lesson="Always verify file existence before reading to avoid FileNotFoundError",
    context="File operations, especially in dynamic environments",
    category="error_prevention",
    importance=0.9
)

# 2. Inject successful strategy
strategy_id = mem_mgr.add_strategy(
    strategy="Read file first → Validate content → Make changes → Verify result",
    task_type="file_modification",
    success_rate=0.95,
    context="Best practice for file editing tasks"
)

# 3. Inject experience
exp_id = mem_mgr.add_experience(
    task="Debug authentication error",
    actions=[
        "check_logs",
        "identify_token_expiry",
        "refresh_token",
        "verify_auth_success"
    ],
    outcome="Successfully fixed auth by refreshing expired token",
    success=True,
    metadata={
        "category": "debugging",
        "domain": "authentication"
    }
)

print(f"Injected: Lesson {lesson_id}, Strategy {strategy_id}, Experience {exp_id}")
```

**Keuntungan:**
- ✅ Instant knowledge transfer
- ✅ Bootstrap new agent quickly
- ✅ Control over what agent learns
- ✅ Great for domain-specific knowledge

**Kekurangan:**
- ⚠️ Requires manual effort
- ⚠️ Doesn't scale well

---

### **4. Batch Learning (Import/Export)**

**Apa itu?**
Import/export memory data dalam batch untuk transfer antar agent atau backup.

**Kapan digunakan?**
- Backup & restore
- Clone agent knowledge
- Share knowledge antar instances
- Disaster recovery

**Cara Implementasi:**

```python
from agent.state.memory_manager import get_memory_manager
from pathlib import Path

mem_mgr = get_memory_manager()

# EXPORT: Backup semua memory
export_success = mem_mgr.export_all_memory(
    output_file=Path("backups/agent_memory_2025-11-15.json")
)

# IMPORT: Restore atau transfer knowledge
import_counts = mem_mgr.import_memory(
    input_file=Path("backups/agent_memory_2025-11-15.json")
)

print(f"Imported:")
print(f"  - {import_counts['experiences']} experiences")
print(f"  - {import_counts['lessons']} lessons")
print(f"  - {import_counts['strategies']} strategies")
```

**Keuntungan:**
- ✅ Fast knowledge transfer
- ✅ Backup & disaster recovery
- ✅ Clone agent capabilities
- ✅ Easy migration

**Kekurangan:**
- ⚠️ Potential for outdated knowledge
- ⚠️ No automatic quality control

---

### **5. Retrieval-Augmented Learning (RAG-style)**

**Apa itu?**
Sebelum mengerjakan task, agent mencari pengalaman relevan dari ChromaDB untuk inform decision-making.

**Kapan digunakan?**
- Sebelum eksekusi task baru
- Complex problem solving
- Avoiding known pitfalls

**Cara Implementasi:**

```python
from agent.learning.learning_manager import get_learning_manager

learning_mgr = get_learning_manager()

# Sebelum mengerjakan task baru
current_task = "Create authentication system with JWT"

# Get relevant past experience
insights = learning_mgr.get_relevant_experience(
    current_task=current_task,
    n_results=5
)

# Insights berisi:
print("Similar past experiences:", insights['similar_experiences'])
print("Relevant lessons:", insights['relevant_lessons'])
print("Recommended strategies:", insights['recommended_strategies'])
print("Summary:", insights['experience_summary'])

# Gunakan insights untuk inform task execution
# (Agent orchestrator akan menggunakan ini)
```

**Keuntungan:**
- ✅ Prevents repeating mistakes
- ✅ Leverages past successes
- ✅ Context-aware decisions
- ✅ Automatic retrieval

**Kekurangan:**
- ⚠️ Depends on quality of stored experiences
- ⚠️ Vector search may not always find best match

---

### **6. Active Learning & Feedback Loop**

**Apa itu?**
Continuous improvement loop dengan monitoring dan periodic retraining.

**Kapan digunakan?**
- Production environment
- Long-running agents
- Critical applications

**Cara Implementasi:**

```python
from agent.learning.self_improvement import get_self_improvement_suggester
from agent.learning.learning_manager import get_learning_manager

# 1. Get performance analysis
suggester = get_self_improvement_suggester()
analysis = suggester.analyze_performance()

print(f"Success rate: {analysis['success_rate']:.1%}")
print(f"Total experiences: {analysis['total_experiences']}")

# 2. Get improvement suggestions
suggestions = suggester.get_improvement_suggestions()

for suggestion in suggestions:
    print(f"[{suggestion['priority'].upper()}] {suggestion['suggestion']}")
    if 'current_metric' in suggestion:
        print(f"  Current: {suggestion['current_metric']}")

# 3. Generate progress report
report = suggester.get_learning_progress_report()

# 4. Take action based on suggestions
# (Implement corrective actions or adjust strategies)
```

**Keuntungan:**
- ✅ Self-optimizing system
- ✅ Identifies weaknesses automatically
- ✅ Actionable recommendations
- ✅ Continuous improvement

**Kekurangan:**
- ⚠️ Requires regular monitoring
- ⚠️ May need human intervention for implementation

---

## 🎓 Best Practices

### **1. Kombinasi Metode**

**Recommended Training Pipeline:**

```
Phase 1: Bootstrap (Week 1)
├─ Guided Learning: Inject domain knowledge
├─ Batch Import: Load pre-trained knowledge base
└─ Manual lessons: Add critical patterns

Phase 2: Active Learning (Week 2-4)
├─ Experience-Based Learning: Run tasks, collect data
├─ Error-Driven Learning: Learn from failures
└─ Retrieval-Augmented: Use past experience

Phase 3: Optimization (Ongoing)
├─ Active Learning: Monitor & improve
├─ Periodic error analysis
└─ Export/backup regularly
```

### **2. Data Quality**

```python
# GOOD: Specific, actionable
learning_mgr.learn_from_task(
    task="Parse JSON config file and validate schema",
    actions=["read_file", "json_parse", "schema_validate"],
    outcome="Successfully validated config against schema v2.0",
    success=True,
    context={
        "schema_version": "2.0",
        "validation_library": "jsonschema"
    }
)

# BAD: Vague, no context
learning_mgr.learn_from_task(
    task="do something",
    actions=["action"],
    outcome="done",
    success=True
)
```

### **3. Regular Maintenance**

```python
from agent.state.memory_manager import get_memory_manager

mem_mgr = get_memory_manager()

# Weekly: Check statistics
stats = mem_mgr.get_all_statistics()
print(f"Experiences: {stats['vector_memory']['total_experiences']}")
print(f"Lessons: {stats['vector_memory']['total_lessons']}")
print(f"Strategies: {stats['vector_memory']['total_strategies']}")

# Monthly: Export backup
from datetime import datetime
backup_file = Path(f"backups/memory_{datetime.now().strftime('%Y%m')}.json")
mem_mgr.export_all_memory(backup_file)

# As needed: Clear outdated data
# mem_mgr.clear_all_memory()  # WARNING: Cannot be undone!
```

### **4. ChromaDB Optimization**

```python
# Dalam VectorMemory initialization (sudah di code)
import chromadb
from chromadb.config import Settings

client = chromadb.PersistentClient(
    path="workspace/.memory",
    settings=Settings(
        anonymized_telemetry=False,  # Disable telemetry
        allow_reset=True,
        chroma_telemetry_impl="none"
    )
)

# Tips:
# - Use persistent storage (already implemented)
# - Disable telemetry (already done)
# - Regular backups
# - Monitor disk usage
```

---

## 📋 Implementasi Step-by-Step

### **Scenario: Training Agent untuk Web Development Tasks**

#### **Step 1: Bootstrap dengan Domain Knowledge**

```python
from agent.state.memory_manager import get_memory_manager

mem_mgr = get_memory_manager()

# Inject web development lessons
lessons = [
    {
        "lesson": "Always validate HTML syntax before deployment",
        "context": "Web development - HTML files",
        "category": "quality_assurance",
        "importance": 0.9
    },
    {
        "lesson": "Include viewport meta tag for mobile responsiveness",
        "context": "Web development - Mobile-first design",
        "category": "best_practice",
        "importance": 0.8
    },
    {
        "lesson": "Sanitize user input to prevent XSS attacks",
        "context": "Web security - Input handling",
        "category": "security",
        "importance": 1.0
    }
]

for lesson_data in lessons:
    mem_mgr.add_lesson(**lesson_data)
    print(f"Added: {lesson_data['lesson']}")
```

#### **Step 2: Add Successful Strategies**

```python
strategies = [
    {
        "strategy": "Create HTML structure → Add CSS styling → Add JavaScript → Test",
        "task_type": "web_page_creation",
        "success_rate": 0.9,
        "context": "Standard web development workflow"
    },
    {
        "strategy": "Verify file paths → Check syntax → Test in browser → Deploy",
        "task_type": "web_deployment",
        "success_rate": 0.85,
        "context": "Deployment verification steps"
    }
]

for strategy_data in strategies:
    mem_mgr.add_strategy(**strategy_data)
    print(f"Added strategy for: {strategy_data['task_type']}")
```

#### **Step 3: Run Tasks & Collect Experience**

```python
from agent.learning.learning_manager import get_learning_manager

learning_mgr = get_learning_manager()

# Simulate task execution
task_result = {
    "task": "Create responsive landing page with hero section",
    "actions": [
        "create_file: landing.html",
        "add_html_structure",
        "add_css_styling: styles.css",
        "add_viewport_meta",
        "test_responsiveness"
    ],
    "outcome": "Created responsive landing page with hero section, tested on mobile and desktop",
    "success": True,
    "errors": [],
    "context": {
        "task_type": "web_development",
        "complexity": "medium",
        "technologies": ["HTML5", "CSS3"]
    }
}

summary = learning_mgr.learn_from_task(**task_result)
print(f"Learning summary: {summary}")
```

#### **Step 4: Monitor & Improve**

```python
from agent.learning.self_improvement import get_self_improvement_suggester

suggester = get_self_improvement_suggester()

# Get improvement suggestions
suggestions = suggester.get_improvement_suggestions()

print("\n=== Improvement Suggestions ===")
for sug in suggestions:
    print(f"\n[{sug['priority'].upper()}] {sug['category']}")
    print(f"  {sug['suggestion']}")
    if 'current_metric' in sug:
        print(f"  Metric: {sug['current_metric']}")
```

#### **Step 5: Periodic Maintenance**

```python
# Weekly backup
from pathlib import Path
from datetime import datetime

backup_file = Path(f"backups/web_agent_{datetime.now().strftime('%Y%m%d')}.json")
mem_mgr.export_all_memory(backup_file)

# Check statistics
stats = mem_mgr.get_all_statistics()
print(f"\n=== Memory Statistics ===")
print(f"Experiences: {stats['vector_memory']['total_experiences']}")
print(f"Lessons: {stats['vector_memory']['total_lessons']}")
print(f"Strategies: {stats['vector_memory']['total_strategies']}")

# Error analysis
error_summary = learning_mgr.get_error_summary()
print(f"\n=== Error Summary ===")
print(error_summary)
```

---

## 📊 Monitoring & Evaluasi

### **Key Metrics to Track**

```python
from agent.learning.learning_manager import get_learning_manager

learning_mgr = get_learning_manager()

# 1. Success Rate
stats = learning_mgr.get_learning_statistics()
print(f"Success Rate: {stats['overall_success_rate']:.1%}")

# 2. Memory Growth
memory_stats = stats
print(f"Total Experiences: {memory_stats['total_experiences']}")
print(f"Total Lessons: {memory_stats['total_lessons']}")
print(f"Total Strategies: {memory_stats['total_strategies']}")

# 3. Error Trends
error_analysis = learning_mgr.analyze_error_patterns(time_window_days=30)
print(f"Errors in last 30 days: {error_analysis.get('total_errors', 0)}")

# 4. Learning Effectiveness
from agent.learning.self_improvement import get_self_improvement_suggester
suggester = get_self_improvement_suggester()
analysis = suggester.analyze_performance()

efficiency = analysis.get('efficiency_metrics', {})
print(f"Efficiency Rating: {efficiency.get('efficiency_rating', 'unknown')}")
print(f"Avg Actions per Task: {efficiency.get('avg_actions_per_task', 0):.1f}")
```

### **Dashboard Script**

```python
#!/usr/bin/env python3
"""Learning Dashboard - Monitor agent training progress"""

from agent.learning.learning_manager import get_learning_manager
from agent.learning.self_improvement import get_self_improvement_suggester
from agent.state.memory_manager import get_memory_manager

def show_dashboard():
    learning_mgr = get_learning_manager()
    suggester = get_self_improvement_suggester()
    mem_mgr = get_memory_manager()

    print("=" * 60)
    print("AGENT LEARNING DASHBOARD")
    print("=" * 60)

    # Memory Stats
    stats = mem_mgr.get_all_statistics()
    vm = stats.get('vector_memory', {})
    print(f"\n📊 Memory Statistics:")
    print(f"  Experiences: {vm.get('total_experiences', 0)}")
    print(f"  Lessons: {vm.get('total_lessons', 0)}")
    print(f"  Strategies: {vm.get('total_strategies', 0)}")
    print(f"  Backend: {vm.get('backend', 'unknown')}")

    # Performance
    learning_stats = learning_mgr.get_learning_statistics()
    print(f"\n🎯 Performance:")
    print(f"  Success Rate: {learning_stats.get('overall_success_rate', 0):.1%}")

    # Suggestions
    suggestions = suggester.get_improvement_suggestions()
    print(f"\n💡 Top Suggestions:")
    for i, sug in enumerate(suggestions[:3], 1):
        print(f"  {i}. [{sug['priority']}] {sug['suggestion']}")

    # Errors
    error_summary = learning_mgr.get_error_summary()
    print(f"\n⚠️  Error Summary:")
    print(f"  {error_summary}")

    print("\n" + "=" * 60)

if __name__ == "__main__":
    show_dashboard()
```

---

## 🎯 Kesimpulan & Rekomendasi

### **Metode Training Terbaik untuk ChromaDB:**

1. **🥇 Experience-Based Learning** - Fundamental, auto-pilot
2. **🥈 Error-Driven Learning** - Prevent repeated failures
3. **🥉 Retrieval-Augmented** - Leverage past knowledge

### **Quick Start Recommendation:**

```python
# Minimal viable training setup
from agent.learning.learning_manager import get_learning_manager

learning_mgr = get_learning_manager()

# 1. Enable automatic learning (already running in agent)
# 2. Periodic error analysis (weekly)
learning_mgr.learn_from_errors()

# 3. Monthly backup
from pathlib import Path
from datetime import datetime
learning_mgr.export_learning_data(
    f"backups/memory_{datetime.now().strftime('%Y%m')}.json"
)

# That's it! Agent akan terus belajar automatically.
```

### **Resources:**

- Code: `agent/learning/learning_manager.py`
- Memory: `agent/state/memory_manager.py`
- ChromaDB: `workspace/.memory/`
- Backups: Create `backups/` directory

### **Next Steps:**

1. ✅ Review current memory statistics
2. ✅ Inject domain-specific knowledge (if needed)
3. ✅ Set up automated backups
4. ✅ Monitor learning progress weekly
5. ✅ Run error analysis monthly

---

**Created:** 2025-11-15
**Version:** 1.0
**Agent:** Radira AI Agent with ChromaDB Learning
