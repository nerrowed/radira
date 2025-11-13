# Enhanced AI Pipeline - Semantic Retrieval & Agentic Reasoning

## Overview

Pipeline AI ini telah ditingkatkan dengan kemampuan:
1. **Semantic Retrieval Integration** - Menggunakan hasil dari Chroma vector database
2. **Reflective Memory Reuse** - Menggunakan lessons dan strategies dari masa lalu
3. **Routing & Tool Invocation** - Memanggil custom functions secara dinamis
4. **Agentic Reasoning Prompt** - Deep step-by-step thinking
5. **Auto-Reflection & Self-Improvement** - Otomatis belajar setelah setiap task
6. **Structured Logging** - Log yang jelas dengan tag [THINKING], [RETRIEVAL], [ACTION], [LEARNED]

---

## 1. Semantic Retrieval Integration

### Masalah Sebelumnya
- AI mengambil data dari Chroma tapi **TIDAK dipakai**
- Retrieval hanya di-print ke console, tidak masuk ke prompt model
- Model inference dilakukan tanpa context dari pengalaman masa lalu

### Solusi
File: `agent/llm/enhanced_prompts.py`

```python
def format_retrieval_context(experiences, lessons, strategies) -> str:
    """Format hasil retrieval menjadi context string yang di-inject ke prompt."""

    # Format experiences, lessons, strategies menjadi text yang readable
    # Return formatted string untuk di-inject ke prompt
```

```python
def create_prompt_with_retrieval(
    question, tools, history,
    retrieval_context=None,  # <- INJECT DI SINI
    intent_analysis=None
) -> str:
    """Create prompt dengan retrieval context DI AWAL prompt."""

    # Struktur prompt:
    # 1. KONTEKS DARI MEMORI SEMANTIK (retrieval_context)
    # 2. ANALISIS INTENT USER
    # 3. TASK SAAT INI
    # 4. AVAILABLE TOOLS
    # 5. HISTORY
```

### Di Orchestrator
File: `agent/core/orchestrator.py`

```python
# Retrieve dari memory
retrieval_context = None
if self.enable_learning and self.learning_manager:
    relevant_experience = self.learning_manager.get_relevant_experience(task, n_results=3)

    # FORMAT hasil retrieval menjadi context string
    retrieval_context = format_retrieval_context(
        experiences=relevant_experience.get("similar_experiences", []),
        lessons=relevant_experience.get("relevant_lessons", []),
        strategies=relevant_experience.get("recommended_strategies", [])
    )

# INJECT retrieval_context ke prompt sebelum inference
prompt = create_prompt_with_retrieval(
    question=task,
    tools=tools,
    history=trimmed_history,
    retrieval_context=retrieval_context  # <- DI SINI!
)

# Model sekarang melihat retrieval context SEBELUM inference
response = self.llm.chat([
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": prompt}  # <- Prompt sudah include retrieval
])
```

### Hasil
✅ Model sekarang **BENAR-BENAR MENGGUNAKAN** hasil retrieval dari Chroma
✅ Pengalaman masa lalu, lessons, dan strategies masuk ke context model
✅ AI bisa belajar dari kesalahan dan kesuksesan masa lalu

---

## 2. Reflective Memory Reuse

### Implementasi
File: `agent/learning/learning_manager.py`

```python
def get_relevant_experience(self, current_task: str, n_results: int = 3):
    """Get relevant past experiences, lessons, AND strategies."""

    # 1. Similar experiences
    similar_experiences = self.memory.recall_similar_experiences(
        query=current_task,
        n_results=n_results
    )

    # 2. Relevant lessons
    relevant_lessons = self.memory.recall_lessons(
        query=current_task,
        n_results=5
    )

    # 3. Strategies for this task type
    task_type = self._classify_task_type(current_task, [])
    relevant_strategies = self.memory.recall_strategies(
        task_type=task_type,
        n_results=3
    )

    return {
        "similar_experiences": similar_experiences,
        "relevant_lessons": relevant_lessons,
        "recommended_strategies": relevant_strategies
    }
```

### Hasil
✅ Lessons dari masa lalu di-retrieve berdasarkan similarity
✅ Strategies yang sudah terbukti berhasil direkomendasikan
✅ AI bisa menghindari kesalahan yang pernah dibuat

---

## 3. Routing & Tool Invocation

### Custom Function Tools
File: `agent/tools/custom_functions.py`

Contoh tools yang tersedia:

```python
class BitcoinPriceTool(BaseTool):
    """Get Bitcoin price from CoinDesk API."""

    def _execute(self, **kwargs):
        response = requests.get("https://api.coindesk.com/v1/bpi/currentprice.json")
        data = response.json()
        return ToolResult(
            status=ToolStatus.SUCCESS,
            output=f"Bitcoin price: ${data['bpi']['USD']['rate']}"
        )

class CalculatorTool(BaseTool):
    """Perform mathematical calculations."""

    def _execute(self, expression: str, **kwargs):
        result = eval(expression, {"__builtins__": {}}, {})
        return ToolResult(
            status=ToolStatus.SUCCESS,
            output=f"{expression} = {result}"
        )

class TimeTool(BaseTool):
    """Get current time and date."""

class HttpRequestTool(BaseTool):
    """Make HTTP GET requests."""
```

### Auto-Registration
File: `agent/tools/registry.py`

```python
def get_registry() -> ToolRegistry:
    """Auto-register all tools on first call."""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()

        # Auto-register core tools
        _registry.register(FileSystemTool())
        _registry.register(TerminalTool())
        _registry.register(WebSearchTool())

        # Auto-register custom functions
        from agent.tools.custom_functions import register_custom_tools
        register_custom_tools(_registry)

    return _registry
```

### Hasil
✅ AI bisa memanggil `get_bitcoin_price()`, `calculator()`, `get_current_time()`, dll
✅ Tools otomatis ter-register saat startup
✅ Mudah menambahkan custom function baru

---

## 4. Agentic Reasoning Prompt

### System Prompt Baru
File: `agent/llm/enhanced_prompts.py`

```python
def create_agentic_reasoning_prompt(tools: list) -> str:
    """System prompt yang mendorong deep reasoning."""

    return f"""You are Radira, an advanced AI agent with:

### 1. DEEP REASONING
- Analisis masalah secara mendalam
- Pecah menjadi sub-masalah
- Rencanakan sequence of actions
- Prediksi hasil dari setiap action
- Reflect setelah action diambil

### 2. SEMANTIC MEMORY
- Gunakan pengalaman masa lalu untuk membuat keputusan
- Pelajari dari kesalahan
- Terapkan strategi yang sudah terbukti berhasil
- Hindari pattern yang menyebabkan kegagalan

### 3. TOOL INVOCATION
Available Tools:
{tool_descriptions}

### 4. SELF-REFLECTION & IMPROVEMENT
Setelah setiap task:
- Reflect: Apa yang berhasil? Apa yang gagal?
- Learn: Pelajaran apa yang bisa diambil?
- Improve: Strategi baru apa yang muncul?
- Store: Simpan insights ke memory

## Response Format:

Thought: [Reasoning mendalam]
- Analisis: [Apa yang diminta user?]
- Memory Context: [Apa yang dipelajari dari pengalaman masa lalu?]
- Plan: [Action apa yang akan diambil dan mengapa?]
- Expected Outcome: [Hasil yang diharapkan?]

Action: [tool_name]
Action Input: [parameters]

Remember: You are THINKING, LEARNING, and IMPROVING with every task!
"""
```

### Di Orchestrator
File: `agent/core/orchestrator.py`

```python
# Use agentic reasoning prompt if learning enabled
if self.enable_learning:
    system_prompt = create_agentic_reasoning_prompt(tools)
    print("[THINKING] Using agentic reasoning mode with semantic memory")
```

### Hasil
✅ AI berpikir lebih dalam sebelum mengambil action
✅ Reasoning mencakup memory context dari pengalaman masa lalu
✅ Lebih banyak reflection dan self-awareness

---

## 5. Auto-Reflection & Self-Improvement

### Implementation
File: `agent/core/orchestrator.py`

```python
# Setelah task selesai (success OR failure)
if self.enable_learning and self.learning_manager:
    print("[LEARNED] Reflecting on execution and storing insights...")

    learning_summary = self.learning_manager.learn_from_task(
        task=task,
        actions=actions,
        outcome=outcome,
        success=success,
        errors=self.errors_encountered
    )

    # Show what was learned
    print(f"[LEARNED] Learned {lessons_count} lesson(s)")
    print(f"[LEARNED] Recorded {strategies_count} strategy(ies)")
    print(f"[LEARNED] Key insights:")
    for lesson in lessons:
        print(f"          • {lesson['lesson']}")
```

### Learning Cycle
File: `agent/learning/learning_manager.py`

```python
def learn_from_task(self, task, actions, outcome, success, errors):
    """Complete learning cycle."""

    # 1. Reflect on what happened
    reflection_result = self.reflection.reflect_on_task(...)

    # 2. Store experience in vector memory
    experience_id = self.memory.store_experience(...)

    # 3. Extract and store lessons
    for lesson_data in reflection_result["lessons"]:
        self.memory.store_lesson(...)

    # 4. Store successful strategies
    if success:
        strategy = self._extract_strategy(actions, reflection_result)
        self.memory.store_strategy(...)

    return learning_summary
```

### Hasil
✅ AI otomatis reflect setelah SETIAP task
✅ Lessons dan strategies disimpan ke Chroma
✅ Next time task serupa, AI akan retrieve insights ini

---

## 6. Structured Logging

### Log Tags
File: `agent/core/orchestrator.py`

```python
# During execution:
print("[THINKING] Using agentic reasoning mode with semantic memory")
print("[THINKING] --- Iteration 1/10 ---")

print("[RETRIEVAL] Searching semantic memory for relevant experiences...")
print("[RETRIEVAL] Found 3 experiences, 5 lessons, 2 strategies")

print("[ACTION] Executing: get_bitcoin_price")
print("[ACTION] Input: {}")
print("[ACTION] Result: Bitcoin price: $XX,XXX")

print("[LEARNED] Reflecting on execution and storing insights...")
print("[LEARNED] Learned 2 lesson(s)")
print("[LEARNED] Recorded 1 strategy(ies)")
print("[LEARNED] Key insights:")
print("          • Lesson 1...")
```

### Hasil
✅ Log yang jelas dan terstruktur
✅ Mudah tracking apa yang AI lakukan
✅ Debug-friendly dengan clear markers

---

## How to Use

### Basic Usage

```python
from agent.core.orchestrator import AgentOrchestrator
from agent.llm.groq_client import get_groq_client
from agent.tools.registry import get_registry

# Initialize with learning enabled
orchestrator = AgentOrchestrator(
    llm_client=get_groq_client(),
    tool_registry=get_registry(),  # Auto-registers custom tools
    enable_learning=True,           # Enable semantic memory
    enable_self_awareness=True,     # Enable intent understanding
    verbose=True                     # Show structured logs
)

# Run a task
result = orchestrator.run("Cek harga Bitcoin saat ini")
print(result)
```

### Run Tests

```bash
# Run enhanced pipeline tests
python test_enhanced_pipeline.py
```

This will demonstrate:
- Bitcoin price retrieval with custom function
- Calculator with semantic memory
- Time query
- Learning persistence check
- Multi-step reasoning (optional)

---

## Architecture Changes

### Before
```
User Query → Orchestrator → LLM → Tool Execution → Response
                ↓
           (Retrieval happens but NOT used)
```

### After
```
User Query → Orchestrator
                ↓
           [RETRIEVAL] Query Chroma for experiences/lessons/strategies
                ↓
           Format retrieval → INJECT to prompt
                ↓
           [THINKING] LLM with agentic reasoning + memory context
                ↓
           [ACTION] Execute tools (including custom functions)
                ↓
           [LEARNED] Auto-reflect and store insights
                ↓
           Response to User
```

---

## Files Modified/Created

### Modified
1. `agent/llm/enhanced_prompts.py` - Added semantic retrieval integration
2. `agent/core/orchestrator.py` - Inject retrieval to prompt, structured logging
3. `agent/tools/registry.py` - Auto-registration of tools
4. `agent/learning/learning_manager.py` - Already good, minor enhancements

### Created
1. `agent/tools/custom_functions.py` - Custom function tools
2. `test_enhanced_pipeline.py` - Test suite
3. `ENHANCED_PIPELINE.md` - This documentation

---

## Benefits

### For AI
✅ Learns from every interaction
✅ Uses past experiences to inform decisions
✅ Deeper reasoning with step-by-step thinking
✅ Can call external functions dynamically
✅ Auto-improvement through reflection

### For Developers
✅ Easy to add new custom functions
✅ Clear logging for debugging
✅ Transparent learning process
✅ Better task performance over time

### For Users
✅ Smarter AI that improves with use
✅ More reliable task execution
✅ Better error handling
✅ Consistent behavior based on learned strategies

---

## Next Steps

### Recommended Enhancements

1. **Add More Custom Functions**
   - Weather API integration
   - Database queries
   - Email sending
   - File processing utilities

2. **Improve Router**
   - Add intent-based routing
   - Smart tool selection based on task type
   - Dynamic tool composition

3. **Enhanced Reflection**
   - Use LLM for deeper reflection
   - Compare multiple strategies
   - Identify failure patterns

4. **Memory Management**
   - Prune old/irrelevant memories
   - Consolidate similar lessons
   - Priority-based retrieval

5. **Performance Optimization**
   - Cache frequent retrievals
   - Batch memory operations
   - Async tool execution

---

## Troubleshooting

### Issue: Retrieval returns empty
**Solution**: Ensure ChromaDB is installed and memory has been populated
```bash
pip install chromadb
# Run some tasks first to populate memory
```

### Issue: Custom tools not found
**Solution**: Check tool registration in registry
```python
from agent.tools.registry import get_registry
registry = get_registry()
print(registry.list_tool_names())  # Should include custom tools
```

### Issue: LLM doesn't use memory context
**Solution**: Verify logging shows [RETRIEVAL] and retrieval_context is not None
- Check that `enable_learning=True` in orchestrator
- Verify Chroma has stored experiences

---

## Conclusion

Pipeline AI sekarang:
✅ **BENAR-BENAR** menggunakan hasil retrieval dari Chroma
✅ Melakukan reasoning yang lebih dalam
✅ Memanggil custom functions bila diperlukan
✅ Belajar dan improve secara otomatis
✅ Logging yang jelas dan terstruktur

Semua requirement dari user telah diimplementasikan! 🎉
