# Token Optimization Guide

## 🎯 Token Budget Goals

### Recommended Limits (per task)

```
┌─────────────────────┬──────────────┬────────────────┐
│ Task Type           │ Target       │ Hard Limit     │
├─────────────────────┼──────────────┼────────────────┤
│ Simple Search       │ 10-15k       │ 20k            │
│ File Operations     │ 8-12k        │ 15k            │
│ Web Generation      │ 15-25k       │ 30k            │
│ Code Generation     │ 20-30k       │ 40k            │
│ Complex Multi-step  │ 30-40k       │ 50k            │
└─────────────────────┴──────────────┴────────────────┘
```

**Default**: 20k tokens per task (configurable)

## 📊 Current Optimization

### Before Optimization:
- ❌ 59k tokens for 10 iterations (5,900/iteration)
- ❌ max_tokens: 4096 per response
- ❌ Full history in every prompt
- ❌ No token tracking

### After Optimization:
- ✅ ~15k tokens for 10 iterations (1,500/iteration)
- ✅ max_tokens: 1024 per response
- ✅ Keep only last 3 iterations in context
- ✅ Real-time token tracking and budget enforcement

**Result**: ~75% token reduction! 🎉

## ⚙️ Configuration

### File: `.env`

```bash
# Token Budget Configuration
MAX_TOKENS_PER_RESPONSE=1024       # Max tokens per LLM response
MAX_TOTAL_TOKENS_PER_TASK=20000    # Total budget per task
HISTORY_KEEP_LAST_N=3              # Only keep last N iterations
```

### Customization by Task Type

**For simple tasks** (search, read file, 1-3 steps):
```bash
MAX_TOKENS_PER_RESPONSE=768
MAX_TOTAL_TOKENS_PER_TASK=12000
HISTORY_KEEP_LAST_N=4  # Keep at least 4 to avoid loops
```

**For medium tasks** (subdomain enum, web gen, 4-6 steps):
```bash
MAX_TOKENS_PER_RESPONSE=1024
MAX_TOTAL_TOKENS_PER_TASK=30000
HISTORY_KEEP_LAST_N=6  # RECOMMENDED - prevents loops
```

**For complex tasks** (full pentest, code gen, 7-10 steps):
```bash
MAX_TOKENS_PER_RESPONSE=1536
MAX_TOTAL_TOKENS_PER_TASK=50000
HISTORY_KEEP_LAST_N=8  # Keep more context for complex workflows
```

**For production with tight budget** (use with caution):
```bash
MAX_TOKENS_PER_RESPONSE=768
MAX_TOTAL_TOKENS_PER_TASK=15000
HISTORY_KEEP_LAST_N=5  # Minimum 5 to avoid forgetting
```

## ⚠️ Critical: HISTORY_KEEP_LAST_N Guidelines

**Rule of thumb**: `HISTORY_KEEP_LAST_N` should be **at least HALF of MAX_ITERATIONS**

```
MAX_ITERATIONS=10  →  HISTORY_KEEP_LAST_N >= 5
MAX_ITERATIONS=8   →  HISTORY_KEEP_LAST_N >= 4
MAX_ITERATIONS=6   →  HISTORY_KEEP_LAST_N >= 3
```

**Why?** Agent needs to remember earlier steps to avoid repeating work!

**Common mistake**:
```bash
MAX_ITERATIONS=10
HISTORY_KEEP_LAST_N=2  # ❌ TOO LOW! Agent will loop
```

**Fixed**:
```bash
MAX_ITERATIONS=10
HISTORY_KEEP_LAST_N=6  # ✅ Good - agent remembers context
```

## 🔧 How It Works

### 1. Response Token Limit
```python
# Before: max_tokens=4096 (wasteful)
response = llm.chat(messages, max_tokens=4096)

# After: max_tokens=1024 (efficient)
response = llm.chat(messages, max_tokens=settings.max_tokens_per_response)
```

### 2. History Trimming
```python
# Keep only last N iterations to reduce prompt size
trimmed_history = history[-settings.history_keep_last_n:]
```

### 3. Budget Enforcement
```python
# Stop task if budget exceeded
if total_tokens > settings.max_total_tokens_per_task:
    return "Task stopped: Token budget exceeded"
```

### 4. Real-time Monitoring
```
📊 Tokens this iteration: 1,234 | Total: 3,456/20,000
```

## 💡 Additional Optimization Tips

### 1. Use Fast Model for Simple Tasks
```bash
GROQ_MODEL=gemma2-9b-it  # Faster, cheaper for simple tasks
```

### 2. Reduce Temperature
```bash
# Lower temperature = more focused, shorter responses
temperature=0.1  # Very focused (current: 0.3)
```

### 3. Optimize System Prompt
- Keep tool descriptions concise
- Remove unnecessary examples
- Use abbreviated language

### 4. Smart History Management
```python
# Instead of full observation, store summary
observation_summary = observation[:200] + "..."
```

### 5. Early Termination
```python
# Stop if task clearly cannot be completed
if iteration > 3 and no_progress:
    return early_answer
```

## 📈 Token Usage Analysis

### Breaking Down 59k Token Usage (Before):

```
Per Iteration (~5,900 tokens):
├─ System Prompt: ~1,200 tokens
│  ├─ Base prompt: 400 tokens
│  ├─ Tool descriptions: 800 tokens (5 tools × 160 each)
│
├─ User Prompt: ~1,500 tokens
│  ├─ Task description: 100 tokens
│  ├─ Full history: 1,200 tokens (grows each iteration!)
│  ├─ Current iteration info: 200 tokens
│
├─ LLM Response: ~2,500 tokens
│  ├─ Thinking (<think> tags): 1,500 tokens
│  ├─ Actual response: 1,000 tokens
│
└─ Observation: ~700 tokens

Total: ~5,900 tokens/iteration × 10 iterations = 59,000 tokens
```

### After Optimization (~1,500 tokens):

```
Per Iteration (~1,500 tokens):
├─ System Prompt: ~1,200 tokens (unchanged, but sent only once*)
│
├─ User Prompt: ~600 tokens
│  ├─ Task description: 100 tokens
│  ├─ Trimmed history: 300 tokens (last 3 only)
│  ├─ Current iteration: 200 tokens
│
├─ LLM Response: ~700 tokens (capped at 1024)
│  ├─ Focused response: 700 tokens
│
└─ Observation: ~300 tokens (trimmed)

Total: ~1,500 tokens/iteration × 10 iterations = 15,000 tokens
```

*Note: System prompt counted in prompt_tokens but only sent once per chat session.

## 🎨 Visual Token Budget

```
Task Budget: 20,000 tokens
━━━━━━━━━━━━━━━━━━━━ 100%

Iteration 1:  ████ 1,200/20,000 (6%)
Iteration 2:  ████ 2,400/20,000 (12%)
Iteration 3:  ████ 3,600/20,000 (18%)
Iteration 4:  ████ 4,800/20,000 (24%)
Iteration 5:  ████ 6,000/20,000 (30%)
...
```

## 🚨 Budget Exceeded Handling

When budget is exceeded:

```
⚠️  Token budget exceeded: 21,234/20,000

Task stopped: Token budget exceeded (21,234 tokens used, limit: 20,000)
```

Agent will:
1. Stop execution immediately
2. Return partial result with explanation
3. Log token usage for analysis
4. Store learning experience (budget exceeded = failure pattern)

## 📝 Monitoring Token Usage

### In Real-time

Agent shows token usage after each iteration:
```
📊 Tokens this iteration: 1,234 | Total: 3,456/20,000
```

### In Statistics

```
--- Agent Statistics ---
Total tokens used: 15,234
  - Prompt: 12,000
  - Completion: 3,234
  - Average per iteration: 1,523
```

### In Learning System

```python
from agent.learning.self_improvement import get_self_improvement_suggester

suggester = get_self_improvement_suggester()
analysis = suggester.analyze_performance()

# Check efficiency metrics
efficiency = analysis['efficiency_metrics']
print(f"Avg tokens per task: {efficiency['avg_tokens']}")
```

## 🔍 Debugging High Token Usage

### Step 1: Check Per-Iteration Usage
```
📊 Tokens this iteration: 5,234 | Total: ...
```
If > 2,000 per iteration → Problem!

### Step 2: Identify Culprit

**High Prompt Tokens?**
- History too long → Reduce `HISTORY_KEEP_LAST_N`
- Tool descriptions too verbose → Simplify

**High Completion Tokens?**
- LLM being verbose → Reduce `MAX_TOKENS_PER_RESPONSE`
- Model hallucinating → Lower temperature

**Growing each iteration?**
- History not being trimmed → Check trimming code
- Observations too long → Truncate observations

### Step 3: Adjust Settings

Start conservative:
```bash
MAX_TOKENS_PER_RESPONSE=512
HISTORY_KEEP_LAST_N=2
```

Increase gradually if needed:
```bash
MAX_TOKENS_PER_RESPONSE=1024
HISTORY_KEEP_LAST_N=3
```

## 💰 Cost Implications

### Groq Pricing (as of 2025):

```
Model: llama-3.1-70b-versatile
- Input: $0.59 per 1M tokens
- Output: $0.79 per 1M tokens

Before (59k tokens):
- Input: ~50k × $0.59/1M = $0.0295
- Output: ~9k × $0.79/1M = $0.0071
- Total: ~$0.037 per task

After (15k tokens):
- Input: ~12k × $0.59/1M = $0.0071
- Output: ~3k × $0.79/1M = $0.0024
- Total: ~$0.0095 per task

Savings: 74% cost reduction! 💰
```

For 1,000 tasks:
- Before: $37
- After: $9.50
- **Saved: $27.50**

## 📚 Best Practices

1. **Start Conservative**: Begin with low limits and increase if needed
2. **Monitor Usage**: Watch token metrics in real-time
3. **Optimize Prompts**: Keep system prompt concise
4. **Trim History**: Only keep relevant past iterations
5. **Use Fast Models**: For simple tasks, use smaller/faster models
6. **Early Returns**: Return answer as soon as task is complete
7. **Truncate Observations**: Summarize long tool outputs
8. **Learn from Data**: Use learning system to identify token-heavy patterns

## 🎯 Optimization Checklist

- [x] Set `MAX_TOKENS_PER_RESPONSE` to 1024 or less
- [x] Set `MAX_TOTAL_TOKENS_PER_TASK` based on task complexity
- [x] Configure `HISTORY_KEEP_LAST_N` to 2-3
- [x] Enable real-time token monitoring
- [x] Implement budget enforcement
- [x] Use temperature 0.1-0.3
- [ ] Consider fast model for simple tasks
- [ ] Optimize system prompt further
- [ ] Implement observation truncation
- [ ] Add per-tool token limits

## 🚀 Advanced: Dynamic Token Budget

For even better optimization, implement dynamic budgets:

```python
def get_dynamic_budget(task_type: str) -> int:
    budgets = {
        "search": 10000,
        "file_ops": 12000,
        "web_gen": 25000,
        "code_gen": 35000,
        "pentest": 40000,
    }
    return budgets.get(task_type, 20000)

# Auto-detect task type and adjust budget
task_type = classify_task(task)
max_budget = get_dynamic_budget(task_type)
```

## 📞 Support

If you're still seeing high token usage after optimization:

1. Check logs: `logs/agent.log`
2. Review token stats in agent output
3. Open an issue with token usage details
4. Consider using a smaller model for your use case

---

*Remember: Lower tokens = Lower cost = Faster responses!* ⚡💰
