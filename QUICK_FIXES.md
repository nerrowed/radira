# Quick Fixes - Urgent Issues

## ❌ Issue #1: "No tools available" Error

### Problem
```
Task: coba baca file radira.txt
🔧 Tools allowed: ['filesystem']  ← Wrong name!
WARNING: No tools available
Error: No tools available for this task
```

### Root Cause
Nama tool mismatch - classifier expects `'filesystem'` tapi actual tool name adalah `'file_system'` (dengan underscore).

### Fix Location
**File**: `agent/core/task_classifier.py`
**Line**: 153

### Current Code (WRONG):
```python
TaskType.FILE_OPERATION: ["file_system"],  # ← Correct
```

But output shows `['filesystem']` without underscore!

### Debug First:
```bash
python3 debug_tools.py
```

This will show exactly what's in registry vs what classifier expects.

### Likely Fixes:

**Option A**: Classifier has typo somewhere
```bash
# Search for 'filesystem' without underscore
grep -r "filesystem" agent/core/task_classifier.py
```

**Option B**: Clear Python cache
```bash
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
python3 main.py  # Restart fresh
```

**Option C**: Verify registry singleton
```python
# At top of main.py, add debug:
registry = setup_tools()
print(f"DEBUG: Registry has {len(registry)} tools")
print(f"DEBUG: Tool names: {registry.list_tool_names()}")
```

---

## ✅ Issue #2: AI Not Using Semantic Retrieval

### Fix
Apply changes from `SEMANTIC_RETRIEVAL_IMPLEMENTATION.md`:

1. **Update _react_loop()** to use `create_react_prompt_with_semantic_context()`
2. **Update system prompt** to use `create_agentic_system_prompt_v2()`
3. **Add auto-reflection** in `run()` method

---

## ✅ Issue #3: Memory Fix Working?

### Test
```python
python3 main.py

Task: halo namaku Budi
Task: siapa namaku?
```

Expected:
```
💭 Found 1 similar past conversations
💬 Response: Namamu Budi
```

If shows "tidak ingat", check:
1. Memory fix applied? (line 152 in memory.py uses `full_experience`)
2. ChromaDB working? Check `workspace/.memory/`

---

## 🚨 Priority Order

1. **URGENT**: Fix "No tools available" error
   - Run `debug_tools.py`
   - Fix name mismatch
   - Test file operations work

2. **HIGH**: Enable semantic retrieval
   - Update `_react_loop()`
   - Use new prompts
   - Test shows semantic context

3. **MEDIUM**: Add auto-reflection
   - Update `run()` method
   - Verify ChromaDB stores lessons
   - Test learning accumulates

4. **LOW**: Better logging
   - Replace print statements
   - Use `format_log_message()`
   - Verify emoji logs work

---

## 🧪 Quick Test Suite

```bash
# Test 1: Basic file operation
Task: list files di workspace

# Test 2: Create file
Task: buat file test.txt dengan isi hello

# Test 3: Read file (should use past experience)
Task: baca file test.txt

# Test 4: Memory test
Task: halo namaku Alice
Task: siapa namaku?

# Test 5: Learning test (run twice)
Task: buat file sample.json
Task: buat file another.json  # Should show semantic context
```

---

## 📊 Expected vs Actual

### Expected (After Fixes):
```
Task: buat file test.txt

📚 [RETRIEVAL] Retrieved 2 similar experiences
💭 [THINKING] Starting iteration 1/3

[SEMANTIC MEMORY CONTEXT]
📚 2 Past Similar Tasks:
  ✅ create file config.json
  ✅ write to new file data.txt

🔧 [ACTION] Executing file_system.write
✅ [SUCCESS] File created

🤔 [REFLECTION] Auto-reflecting...
✨ [LEARNED] 1 lessons, 1 strategies stored

Final Answer: File test.txt created successfully
```

### Actual (Current - Broken):
```
Task: coba baca file radira.txt

🔧 Tools allowed: ['filesystem']
WARNING: No tools available
Error: No tools available for this task
```

---

## 🔧 Manual Verification Commands

```python
# 1. Check registry
from agent.tools.registry import get_registry
registry = get_registry()
print("Tools:", registry.list_tool_names())

# 2. Check classifier
from agent.core.task_classifier import get_task_classifier, TaskType
from agent.llm.groq_client import get_groq_client
classifier = get_task_classifier(get_groq_client())
print("File ops tools:", classifier.get_required_tools(TaskType.FILE_OPERATION))

# 3. Check learning
from agent.learning.learning_manager import get_learning_manager
lm = get_learning_manager()
print(lm.get_error_summary())

# 4. Check semantic retrieval
context = lm.get_relevant_experience("buat file")
print("Similar experiences:", len(context['similar_experiences']))
print("Lessons:", len(context['relevant_lessons']))
```

---

## 📝 Status Checklist

- [ ] `debug_tools.py` run successfully
- [ ] Tool name mismatch identified and fixed
- [ ] File operations work (create, read, list)
- [ ] Semantic retrieval shows in logs
- [ ] Auto-reflection happens after tasks
- [ ] ChromaDB grows with lessons/strategies
- [ ] Memory recall works for conversations
- [ ] Error remediation suggestions appear
- [ ] Logging is clear with emojis

---

**Priority**: Fix #1 first - nothing else works until tools are available!
