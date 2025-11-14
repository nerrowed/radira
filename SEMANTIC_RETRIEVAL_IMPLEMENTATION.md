# Semantic Retrieval & Self-Improvement Implementation Guide

## 🎯 Tujuan
Membuat AI agent yang benar-benar "smart" dengan:
1. Semantic retrieval - gunakan memori masa lalu
2. Reflective learning - belajar dari pengalaman
3. Tool invocation yang lebih baik
4. Auto-reflection setelah tasks
5. Logging yang jelas

---

## ✅ Yang Sudah Dibuat

### 1. Enhanced Prompts (agent/llm/enhanced_prompts.py)

**Functions yang sudah ada:**
- `create_context_enriched_prompt()` - Inject semantic context ke prompt
- `create_react_prompt_with_semantic_context()` - ReAct dengan memori
- `create_agentic_system_prompt_v2()` - System prompt yang aware
- `format_log_message()` - Logging dengan emoji

**Cara pakai:**
```python
from agent.llm.enhanced_prompts import (
    create_react_prompt_with_semantic_context,
    create_agentic_system_prompt_v2,
    format_log_message
)

# Get semantic context
semantic_context = learning_manager.get_relevant_experience(task)

# Create prompt dengan context
prompt = create_react_prompt_with_semantic_context(
    question=task,
    tools=tools,
    history=history,
    current_iteration=iter,
    max_iterations=max_iter,
    semantic_context=semantic_context  # ← KEY: Inject context
)
```

---

## 🔧 Yang Perlu Di-Update

### CRITICAL FIX 1: Update dual_orchestrator _react_loop()

**File**: `agent/core/dual_orchestrator.py`
**Method**: `_react_loop()` (around line 258)

**Current Code** (line ~286):
```python
# Create ReAct prompt
prompt = create_react_prompt(
    question=task,
    tools=tools,
    history=trimmed_history,
    current_iteration=self.iteration,
    max_iterations=max_iterations
)
```

**CHANGE TO**:
```python
# Import at top of file
from agent.llm.enhanced_prompts import (
    create_react_prompt_with_semantic_context,
    format_log_message
)

# In _react_loop(), replace create_react_prompt with:
prompt = create_react_prompt_with_semantic_context(
    question=task,
    tools=tools,
    history=trimmed_history,
    current_iteration=self.iteration,
    max_iterations=max_iterations,
    semantic_context=relevant_experience  # ← Already retrieved at line 251
)
```

**Why**: Ini akan inject semantic context ke dalam prompt, jadi LLM bisa lihat past experiences, lessons, dan strategies.

---

### CRITICAL FIX 2: Use Agentic System Prompt

**File**: `agent/core/dual_orchestrator.py`
**Method**: `_create_enhanced_system_prompt()` (around line 593)

**Current**: Uses `create_system_prompt()` from old prompts

**CHANGE TO**:
```python
from agent.llm.enhanced_prompts import create_agentic_system_prompt_v2

def _create_enhanced_system_prompt(self, tools: List) -> str:
    """Create system prompt for ReAct loop."""

    # Use new agentic prompt
    base_prompt = create_agentic_system_prompt_v2()

    # Add tool descriptions
    tool_desc = "\n".join([
        f"- {tool.name}: {tool.description}"
        for tool in tools
    ])

    return f"""{base_prompt}

🔧 AVAILABLE TOOLS:
{tool_desc}

Remember: Use semantic context when provided, apply proven strategies, avoid past mistakes!
"""
```

---

### CRITICAL FIX 3: Auto-Reflection After Task

**File**: `agent/core/dual_orchestrator.py`
**Method**: `run()` (around line 95)

**Add at end of run() method, before return**:
```python
def run(self, task: str) -> str:
    # ... existing code ...

    result = # ... get result from routing ...

    # AUTO-REFLECTION
    if self.enable_learning and self.learning_manager:
        try:
            # Log reflection
            if self.verbose:
                print(format_log_message(
                    "REFLECTION",
                    "Auto-reflecting on completed task..."
                ))

            # Get actions taken
            actions_taken = []
            if self.task_type:
                actions_taken.append(f"route_{self.task_type.value}")

            # Add tool actions from history
            for thought, obs in self.history:
                if "Action:" in thought:
                    actions_taken.append(thought.split("Action:")[-1].split("\n")[0].strip())

            # Check success
            success = "error" not in result.lower() and "failed" not in result.lower()

            # Reflect and learn
            self.learning_manager.learn_from_task(
                task=task,
                actions=actions_taken or ["direct_response"],
                outcome=result[:500],  # Limit size
                success=success,
                errors=self.errors_encountered,
                context={"task_type": self.task_type.value if self.task_type else "unknown"}
            )

            if self.verbose:
                print(format_log_message(
                    "LEARNED",
                    f"Task reflection complete (success={success})"
                ))

        except Exception as e:
            logger.warning(f"Auto-reflection failed: {e}")

    return result
```

**Why**: Ini memastikan setiap task direfleksikan dan lessons disimpan ke ChromaDB.

---

### CRITICAL FIX 4: Enhanced Logging

**File**: `agent/core/dual_orchestrator.py`

**Replace all print statements dengan format_log_message():**

**Example replacements:**

```python
# OLD
print(f"💡 Found {len(relevant_experience['similar_experiences'])} similar experiences")

# NEW
print(format_log_message(
    "RETRIEVAL",
    f"Retrieved {len(relevant_experience['similar_experiences'])} similar experiences",
    {"success_count": success_count, "lessons": len(relevant_lessons)}
))
```

```python
# OLD
print(f"--- Iteration {self.iteration}/{max_iterations} ---\n")

# NEW
print(format_log_message(
    "THINKING",
    f"Starting iteration {self.iteration}/{max_iterations}"
))
```

```python
# OLD
logger.error(f"Action execution error: {e}")

# NEW
print(format_log_message(
    "ERROR",
    f"Action execution failed: {str(e)}",
    {"action": action, "iteration": self.iteration}
))
```

---

## 🔍 Verification Steps

### Test 1: Semantic Retrieval
```python
# Run agent twice with same task
python main.py

Task: buat file test.txt dengan isi hello
# Observe: Task completes, reflection logged

Task: buat file test2.txt dengan isi world
# Check logs for:
# [RETRIEVAL] Retrieved X similar experiences
# [MEMORY] Applying proven strategy
```

### Test 2: Learning Loop
```python
# Manually check learning
from agent.learning.learning_manager import get_learning_manager

lm = get_learning_manager()

# Get experience
exp = lm.get_relevant_experience("buat file")

print("Similar experiences:", len(exp['similar_experiences']))
print("Lessons:", len(exp['relevant_lessons']))
print("Strategies:", len(exp['recommended_strategies']))
```

### Test 3: Logging Clarity
Expected log output:
```
💭 [THINKING] Starting iteration 1/3
📚 [RETRIEVAL] Retrieved 2 similar experiences
    success_count: 1
    lessons: 3
🔧 [ACTION] Executing file_system.write
✅ [SUCCESS] File created successfully
🤔 [REFLECTION] Auto-reflecting on completed task...
✨ [LEARNED] Task reflection complete (success=True)
```

---

## 📊 Expected Behavior Changes

### Before (Current):
```
Task: buat file test.txt

--- Iteration 1/3 ---
Thought: I'll create the file
Action: file_system
Observation: File created

Final Answer: Done
```
**Problems**:
- No context from past
- No learning
- Generic execution

### After (With Changes):
```
Task: buat file test.txt

💭 [THINKING] Starting iteration 1/3

📚 [RETRIEVAL] Retrieved 2 similar experiences
    success_count: 2
    lessons: 1

[SEMANTIC MEMORY CONTEXT]

📚 2 Past Similar Tasks:
  ✅ buat file config.json dengan isi...
  ✅ create new file data.txt

💡 1 Relevant Lessons:
  • Verify file doesn't exist before creating to avoid overwrites

🎯 1 Proven Strategies:
  • [90%] Check if file exists first, then create if missing

[END SEMANTIC CONTEXT]

🔧 [ACTION] Executing file_system.exists
✅ [SUCCESS] File doesn't exist, safe to create

🔧 [ACTION] Executing file_system.write
✅ [SUCCESS] File created successfully

🤔 [REFLECTION] Auto-reflecting on completed task...
✨ [LEARNED] Task reflection complete (success=True)
    Stored: 1 lessons, 1 strategies

Final Answer: File test.txt berhasil dibuat
```

**Benefits**:
- ✅ Uses past experience
- ✅ Applies lessons learned
- ✅ Follows proven strategy
- ✅ Auto-reflects and learns
- ✅ Clear, trackable logging

---

## 🚀 Quick Implementation Checklist

- [ ] **Step 1**: Update `_react_loop()` to use `create_react_prompt_with_semantic_context()`
- [ ] **Step 2**: Update `_create_enhanced_system_prompt()` to use `create_agentic_system_prompt_v2()`
- [ ] **Step 3**: Add auto-reflection in `run()` method after result
- [ ] **Step 4**: Replace print statements with `format_log_message()`
- [ ] **Step 5**: Test dengan task sederhana (buat file, baca file)
- [ ] **Step 6**: Verify ChromaDB menyimpan lessons/strategies
- [ ] **Step 7**: Test task kedua - verify retrieval works

---

## 🐛 Troubleshooting

### Issue: "No semantic context shown"
**Check**:
1. `enable_learning=True` in orchestrator init?
2. ChromaDB has stored experiences? Check `workspace/.memory/`
3. Relevant experience query returns results?

**Debug**:
```python
lm = get_learning_manager()
context = lm.get_relevant_experience("your task")
print("Context:", context)
```

### Issue: "Reflection not running"
**Check**:
1. Auto-reflection code added to `run()` method?
2. `enable_learning=True`?
3. Check logs for "REFLECTION" or "LEARNED" messages

**Debug**:
```python
# Add at end of run()
print(f"Learning enabled: {self.enable_learning}")
print(f"Learning manager: {self.learning_manager}")
```

### Issue: "Logs not formatted"
**Check**:
1. Import `format_log_message` at top of file?
2. Replaced all print statements?

---

## 📝 Additional Enhancements (Optional)

### Add Example Tool Function
```python
# In agent/tools/data_fetcher.py (new file)
import requests

class DataFetcherTool(BaseTool):
    """Fetch data from external APIs."""

    @property
    def name(self) -> str:
        return "data_fetcher"

    @property
    def description(self) -> str:
        return "Fetch data from external APIs (bitcoin price, weather, etc)"

    def execute(self, **kwargs) -> ToolResult:
        api_name = kwargs.get("api")

        if api_name == "bitcoin_price":
            res = requests.get("https://api.coindesk.com/v1/bpi/currentprice.json")
            data = res.json()
            price = data["bpi"]["USD"]["rate"]
            return ToolResult(
                status=ToolStatus.SUCCESS,
                output=f"Bitcoin price: ${price}"
            )

        return ToolResult(
            status=ToolStatus.ERROR,
            error=f"Unknown API: {api_name}"
        )
```

### Enhanced Intent Recognition
```python
# In task_classifier.py, add DATA_RETRIEVAL type
class TaskType(Enum):
    # ... existing ...
    DATA_RETRIEVAL = "data_retrieval"

# In classify():
DATA_RETRIEVAL_PATTERNS = [
    r'\b(cek|check|ambil|get|fetch)\s+(harga|price|data)',
    r'\b(bitcoin|crypto|weather|stock)\b'
]
```

---

## 🎯 Success Criteria

✅ AI uses semantic context in decisions
✅ Past lessons inform current actions
✅ Proven strategies are applied
✅ Auto-reflection works after every task
✅ Clear, trackable logs with emojis
✅ Error patterns are learned and avoided
✅ Continuous improvement over time

---

**Status**: Implementation guide complete
**Next**: Apply critical fixes 1-4 above
**Test**: Run agent multiple times with similar tasks
**Verify**: Check ChromaDB growth and log quality

Good luck! 🚀
