# Quick Guide: Inject Custom Memory ke ChromaDB Agent

## 🚀 3 Cara Inject Memory

### **Cara 1: Interactive Mode (Paling Mudah)**

```bash
python inject_custom_memory.py
```

Lalu pilih menu:
- `1` - Inject Lesson
- `2` - Inject Strategy
- `3` - Inject Experience
- `4` - Inject dari JSON file

**Contoh sesi:**
```
CUSTOM MEMORY INJECTION
======================================================================

1. Inject Lesson
2. Inject Strategy
3. Inject Experience
4. Inject from JSON file
5. Show current statistics
6. Exit

Pilih (1-6): 1

INJECT LESSON
======================================================================

Lesson text: Always validate HTML before deployment
Context (dimana lesson ini berlaku): Web development
Category [general]: quality_assurance
Importance (0.0 - 1.0) [0.8]: 0.9

✅ Lesson berhasil di-inject!
   ID: lesson_1731652800.123
   Category: quality_assurance
   Importance: 0.9
```

---

### **Cara 2: Python Code (Programmatic)**

```python
from agent.state.memory_manager import get_memory_manager

mem_mgr = get_memory_manager()

# Inject Lesson
lesson_id = mem_mgr.add_lesson(
    lesson="Always validate HTML before deployment",
    context="Web development - Quality assurance",
    category="quality_assurance",
    importance=0.9
)

# Inject Strategy
strategy_id = mem_mgr.add_strategy(
    strategy="Read file → Validate → Edit → Write → Verify",
    task_type="file_modification",
    success_rate=0.95,
    context="Safe file editing workflow"
)

# Inject Experience
experience_id = mem_mgr.add_experience(
    task="Fix authentication bug in login system",
    actions=[
        "check_logs",
        "identify_token_expiry",
        "refresh_token_logic",
        "verify_auth_success"
    ],
    outcome="Successfully fixed auth by implementing token refresh",
    success=True,
    metadata={
        "category": "debugging",
        "complexity": "medium"
    }
)

print(f"Injected: {lesson_id}, {strategy_id}, {experience_id}")
```

---

### **Cara 3: Batch Import dari JSON (Banyak Sekaligus)**

#### **Step 1: Buat JSON file**

```bash
# Option A: Buat template otomatis
python inject_custom_memory.py --create-template

# Option B: Pakai template yang sudah ada
cp templates/web_development_memory.json my_custom_memory.json
```

#### **Step 2: Edit JSON file**

```json
{
  "lessons": [
    {
      "lesson": "Your lesson here",
      "context": "Where this applies",
      "category": "best_practice",
      "importance": 0.9
    }
  ],
  "strategies": [
    {
      "strategy": "Step 1 → Step 2 → Step 3",
      "task_type": "your_task_type",
      "success_rate": 0.9,
      "context": "Optional context"
    }
  ],
  "experiences": [
    {
      "task": "Task description",
      "actions": ["action1", "action2"],
      "outcome": "What happened",
      "success": true,
      "metadata": {
        "category": "category_name",
        "complexity": "medium"
      }
    }
  ]
}
```

#### **Step 3: Inject**

```bash
python inject_custom_memory.py --from-file my_custom_memory.json
```

---

## 📋 Format & Fields

### **Lesson**

| Field | Required | Type | Description | Example |
|-------|----------|------|-------------|---------|
| `lesson` | ✅ Yes | string | The lesson text | "Always validate input" |
| `context` | ✅ Yes | string | Where it applies | "Security - Input handling" |
| `category` | ❌ No | string | Category | "security", "best_practice" |
| `importance` | ❌ No | float | 0.0 - 1.0 | 0.9 |

**Categories:** `error_prevention`, `best_practice`, `security`, `quality_assurance`, `optimization`, `general`

---

### **Strategy**

| Field | Required | Type | Description | Example |
|-------|----------|------|-------------|---------|
| `strategy` | ✅ Yes | string | Strategy description | "Step 1 → Step 2 → Step 3" |
| `task_type` | ✅ Yes | string | Type of task | "web_development" |
| `success_rate` | ❌ No | float | 0.0 - 1.0 | 0.9 |
| `context` | ❌ No | string | Additional info | "Production deployment" |

**Task Types:** `web_development`, `file_modification`, `debugging`, `testing`, `deployment`, `security`, `general`

---

### **Experience**

| Field | Required | Type | Description | Example |
|-------|----------|------|-------------|---------|
| `task` | ✅ Yes | string | Task description | "Fix login bug" |
| `actions` | ✅ Yes | array | List of actions | ["check_logs", "fix_code"] |
| `outcome` | ✅ Yes | string | What happened | "Successfully fixed" |
| `success` | ✅ Yes | boolean | Success/failure | true |
| `metadata` | ❌ No | object | Extra info | {"category": "debugging"} |

---

## 🎯 Template Siap Pakai

Kami sudah menyediakan template untuk berbagai domain:

### **1. Web Development**
```bash
python inject_custom_memory.py --from-file templates/web_development_memory.json
```

**Berisi:**
- 8 lessons (HTML, CSS, security, SEO, responsive design)
- 4 strategies (page creation, debugging, form handling)
- 3 experiences (landing page, XSS fix, optimization)

---

### **2. Security Testing**
```bash
python inject_custom_memory.py --from-file templates/security_testing_memory.json
```

**Berisi:**
- 7 lessons (pentesting ethics, methodology, validation)
- 4 strategies (pentesting, vulnerability assessment)
- 3 experiences (web app assessment, SQL injection, API security)

---

### **3. General Programming**
```bash
python inject_custom_memory.py --from-file templates/general_programming_memory.json
```

**Berisi:**
- 10 lessons (error handling, testing, security, best practices)
- 6 strategies (development, debugging, refactoring, TDD)
- 4 experiences (debugging, refactoring, auth implementation, optimization)

---

## 💡 Best Practices

### ✅ DO

1. **Be Specific**
   ```json
   // Good
   "lesson": "Validate HTML with W3C validator before deployment to catch syntax errors"

   // Bad
   "lesson": "Check HTML"
   ```

2. **Include Context**
   ```json
   "context": "Web development - Quality assurance for production sites"
   ```

3. **Use Realistic Success Rates**
   ```json
   "success_rate": 0.85  // Good - realistic
   "success_rate": 1.0   // Risky - too optimistic
   ```

4. **Add Metadata**
   ```json
   "metadata": {
     "category": "debugging",
     "complexity": "medium",
     "domain": "authentication"
   }
   ```

### ❌ DON'T

1. **Don't use vague descriptions**
   ```json
   // Bad
   "lesson": "Be careful"
   "strategy": "Do stuff"
   ```

2. **Don't skip required fields**
   ```json
   // Bad - missing required fields
   {
     "lesson": "Something"
     // Missing "context"!
   }
   ```

3. **Don't use invalid importance values**
   ```json
   "importance": 5.0  // Bad - must be 0.0 to 1.0
   ```

---

## 🔍 Verify Injection

### Check Statistics
```bash
python inject_custom_memory.py
# Pilih menu: 5. Show current statistics
```

Atau dengan Python:
```python
from agent.state.memory_manager import get_memory_manager

mem_mgr = get_memory_manager()
stats = mem_mgr.get_all_statistics()

print(f"Lessons: {stats['vector_memory']['total_lessons']}")
print(f"Strategies: {stats['vector_memory']['total_strategies']}")
print(f"Experiences: {stats['vector_memory']['total_experiences']}")
```

### View Injected Items
```python
# List lessons
lessons = mem_mgr.list_lessons(limit=10)
for lesson in lessons:
    print(f"- {lesson['lesson']}")

# List strategies
strategies = mem_mgr.list_strategies(limit=10)
for strategy in strategies:
    print(f"- {strategy['strategy']} ({strategy['task_type']})")

# List experiences
experiences = mem_mgr.list_experiences(limit=10)
for exp in experiences:
    print(f"- {exp['task']} (Success: {exp['success']})")
```

---

## 🎬 Quick Examples

### Example 1: Inject Single Lesson via Command Line
```bash
python inject_custom_memory.py \
  --type lesson \
  --data '{"lesson": "Always use HTTPS in production", "context": "Web security", "category": "security", "importance": 1.0}'
```

### Example 2: Inject dari Python Script
```python
from agent.state.memory_manager import get_memory_manager

mem_mgr = get_memory_manager()

# Inject multiple lessons at once
lessons = [
    {
        "lesson": "Test edge cases in user input",
        "context": "Quality assurance - Testing",
        "category": "quality_assurance",
        "importance": 0.85
    },
    {
        "lesson": "Use parameterized queries to prevent SQL injection",
        "context": "Security - Database",
        "category": "security",
        "importance": 1.0
    }
]

for lesson_data in lessons:
    mem_mgr.add_lesson(**lesson_data)
    print(f"✓ Added: {lesson_data['lesson']}")
```

### Example 3: Bootstrap Agent untuk Domain Spesifik
```python
# Untuk agent yang fokus pada web development
from pathlib import Path
import subprocess

# Load web development knowledge
result = subprocess.run([
    "python", "inject_custom_memory.py",
    "--from-file", "templates/web_development_memory.json"
], capture_output=True)

print(result.stdout.decode())

# Verify
from agent.state.memory_manager import get_memory_manager
stats = get_memory_manager().get_all_statistics()
print(f"Ready! Loaded {stats['vector_memory']['total_lessons']} lessons")
```

---

## 🆘 Troubleshooting

### "ChromaDB not available"
```bash
# Install ChromaDB
pip install chromadb

# Verify
python -c "import chromadb; print('✓ ChromaDB available')"
```

### "Required fields missing"
```python
# Pastikan semua required fields ada
# Lesson: lesson, context
# Strategy: strategy, task_type
# Experience: task, actions, outcome, success

# Example yang lengkap:
mem_mgr.add_lesson(
    lesson="...",      # Required
    context="...",     # Required
    category="...",    # Optional
    importance=0.9     # Optional
)
```

### "JSON parse error"
```bash
# Validate JSON dulu
python -m json.tool my_memory.json

# Atau gunakan online JSON validator
```

---

## 📚 Resources

- **Script:** `inject_custom_memory.py`
- **Templates:** `templates/*.json`
- **Documentation:** `docs/CHROMADB_TRAINING_GUIDE.md`
- **Memory Manager Code:** `agent/state/memory_manager.py`

---

## 🎉 Ready to Go!

```bash
# Quick start
python inject_custom_memory.py

# Atau langsung inject dari template
python inject_custom_memory.py --from-file templates/web_development_memory.json

# Atau buat template sendiri
python inject_custom_memory.py --create-template
nano custom_memory_template.json
python inject_custom_memory.py --from-file custom_memory_template.json
```

**Happy injecting! 🚀**
