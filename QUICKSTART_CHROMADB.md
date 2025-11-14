# Quick Start: ChromaDB Memory + Confirmation

## 🚀 Test Sekarang!

### Test 1: With Memory + Auto Confirmation (Recommended)
```bash
python main.py --fc --memory "buatkan aplikasi kalkulator dengan nama kal.py"
```

**What happens**:
1. 📚 Queries ChromaDB for past similar tasks
2. 💭 LLM thinks with context (if found)
3. 🔧 Decides to call file_system.write
4. ⚠️ Asks confirmation (AUTO mode, write is dangerous)
5. ✅ Creates kal.py
6. 💾 Stores experience for future use

**Expected prompt**:
```
⚠️  About to execute: file_system.write
   Arguments: path=kal.py, operation=write
   Proceed? [Y/n]:
```

Type `y` and press Enter.

---

### Test 2: Always YES (No Prompts)
```bash
python main.py --fc --memory --confirm yes "buatkan web login dengan html dan css"
```

**What happens**:
- No confirmation prompts
- Direct execution
- Faster workflow
- Good for trusted tasks

---

### Test 3: Read Operation (Auto-Approved)
```bash
python main.py --fc --memory "baca file README.md"
```

**What happens**:
- Read is SAFE operation
- No confirmation needed even in AUTO mode
- Direct execution
- Shows: `✓ Auto-approved: file_system.read (safe)`

---

### Test 4: Without Memory (Fast, No Learning)
```bash
python main.py --fc "halo apa kabar?"
```

**What happens**:
- Conversational task
- No ChromaDB query (faster)
- No confirmation needed
- Direct response
- No experience stored

---

## 📊 Comparison

| Command | Memory | Confirmation | Use Case |
|---------|--------|--------------|----------|
| `python main.py --fc "task"` | ❌ | AUTO | Fast, one-time tasks |
| `python main.py --fc -m "task"` | ✅ | AUTO | **Recommended** - Learning + Safe |
| `python main.py --fc -m --confirm yes "task"` | ✅ | NONE | Repetitive, trusted tasks |
| `python main.py --fc -m --confirm no "task"` | ✅ | ALWAYS | Testing, high-risk operations |

---

## 🎯 Quick Commands Reference

```bash
# Full power (memory + smart confirmation)
python main.py --fc -m "task"

# No interruptions (auto-execute everything)
python main.py --fc --confirm yes "task"

# Maximum safety (ask for everything)
python main.py --fc --confirm no "task"

# Fast mode (no memory, no overhead)
python main.py --fc "task"

# Interactive with memory
python main.py --fc -m

# Help
python main.py --help
```

---

## ✅ Verify Installation

```bash
# Check if everything works
python main.py --fc -m --confirm auto "halo, test memory"
```

**Expected output**:
```
🤖 Function Calling Mode (Claude-like)
   Pure LLM reasoning - no regex classification
   📚 Semantic memory: ENABLED
   ⚙️  Confirmation mode: auto

📚 Semantic memory enabled

🤖 Function Orchestrator initialized
   Functions available: 5
   Tools: file_system, terminal, web_generator, web_search, pentest
   Memory: ✓ Enabled
   Confirmation: auto

📥 User: halo, test memory

💭 [Iteration 1/10] LLM thinking...
✅ LLM finished reasoning (no more tools needed)

💾 Experience stored to semantic memory

📤 Response: Halo! Test memory berhasil...
```

If you see this, **everything is working!** ✅

---

## 🐛 Troubleshooting

### Issue 1: "Failed to initialize learning manager"
**Fix**: Learning manager already exists, this is a warning. Memory will work.

### Issue 2: No confirmation prompt appears
**Cause**: Operation is SAFE (read-only) in AUTO mode
**Fix**: Use `--confirm no` to force prompts for everything

### Issue 3: Memory not finding past tasks
**Cause**: Cold start - no experiences stored yet
**Fix**: Run 2-3 tasks, then memory will start working

---

## 📈 Next Steps

1. **Try your failing examples**:
   ```bash
   python main.py --fc -m "buatkan aplikasi kalkulator"
   python main.py --fc -m "buatkan halaman login"
   ```

2. **Build memory over time**:
   - Use daily for best results
   - Memory accumulates
   - Agent gets smarter

3. **Choose your mode**:
   - Development: `--confirm auto` (recommended)
   - Production: `--confirm yes` (fast)
   - Testing: `--confirm no` (safe)

**Ready to use!** 🚀
