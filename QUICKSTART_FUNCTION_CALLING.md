# Quick Start: Function Calling Mode

## 🚀 Test Sekarang Juga!

### Test 1: Contoh Kamu yang Gagal (Now Fixed!)

```bash
python main.py --fc "buatkan aplikasi kalkulator dengan nama kal.py"
```

**Expected output**:
```
🤖 Function Calling Mode (Claude-like)
   Pure LLM reasoning - no regex classification

📥 User: buatkan aplikasi kalkulator dengan nama kal.py

💭 [Iteration 1/10] LLM thinking...
🔧 LLM decided to call 1 tool(s)
   🔧 Calling: file_system
      Args: {'operation': 'write', 'path': 'kal.py', 'content': '...'}
      ✅ Success: File written...

💭 [Iteration 2/10] LLM thinking...
✅ LLM finished reasoning (no more tools needed)
   Total iterations: 2
   Total tool calls: 1

═══════════════════════════════════════════════════════════
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Result                                                  ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
Aplikasi kalkulator telah berhasil dibuat di kal.py!
File berisi program Python dengan fungsi penjumlahan,
pengurangan, perkalian, dan pembagian.
```

✅ **File kal.py dibuat!** (Check dengan `ls kal.py`)

---

### Test 2: Halaman Login HTML

```bash
python main.py --fc "buatkan saya halaman login dengan html dan css"
```

**Expected**: Creates login.html and styles.css files

---

### Test 3: Interactive Mode

```bash
python main.py --fc
```

Then try:
```
Task: buatkan kalkulator python sederhana
Task: baca file README.md
Task: halo apa kabar?
Task: exit
```

---

## 📊 Compare: Old vs New

### Old Mode (Regex):
```bash
python main.py "buatkan aplikasi kalkulator dengan nama kal.py"
```

**Result**: ❌ Classified as "conversational" → No file created

### New Mode (Function Calling):
```bash
python main.py --fc "buatkan aplikasi kalkulator dengan nama kal.py"
```

**Result**: ✅ Understands intent → Creates kal.py file

---

## 🎯 Quick Commands

```bash
# Interactive mode (function calling)
python main.py --fc

# Single task (function calling)
python main.py --fc "your task here"

# Interactive mode (old regex mode)
python main.py

# Show help
python main.py --help
```

---

## ✅ Verification Checklist

After running the tests:

- [ ] File `kal.py` exists and contains calculator code
- [ ] LLM shows thinking process in logs
- [ ] Tool calls are logged
- [ ] Final response is natural and helpful
- [ ] No "conversational" misclassification

If all checked, **Function Calling works!** 🎉

---

## 🐛 Quick Fixes

### If you see "ImportError":
```bash
# Make sure you're in the project directory
cd H:\Projek\ai-agent-vps
python main.py --fc "test"
```

### If you see "GroqClient error":
Check your `.env` file has valid Groq API key:
```bash
GROQ_API_KEY=your_actual_key_here
GROQ_MODEL=llama-3.1-70b-versatile
```

### If tools are not found:
The error might show up during runtime. Make sure all tools are imported in main.py (they already are).

---

## 📈 What Changed?

| Aspect | Before | After |
|--------|--------|-------|
| Classification | Regex patterns | LLM reasoning |
| "buatkan aplikasi X" | ❌ Fails | ✅ Works |
| "buatkan halaman X" | ❌ Fails | ✅ Works |
| Natural language | ❌ Limited | ✅ Fully supported |
| Thinking visible | ❌ Hidden | ✅ Shows reasoning |

---

## 🎊 Ready!

Your agent now thinks like Claude. Test it now:

```bash
python main.py --fc "buatkan aplikasi kalkulator dengan nama kal.py"
```

**Enjoy!** 🚀
