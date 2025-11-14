"""Enhanced prompts for self-aware AI.

Prompts yang membuat AI lebih "ngeh" dengan tugasnya,
lebih understand intent, dan lebih careful dalam mengambil action.
"""

from typing import List, Optional


def create_self_aware_system_prompt(tools) -> str:
    """Create system prompt that makes AI more self-aware."""

    tool_descriptions = "\n".join([
        f"- {tool.name}: {tool.description}"
        for tool in tools
    ])

    prompt = f"""You are a HIGHLY SELF-AWARE AI assistant with these capabilities:
{tool_descriptions}

⚠️ CRITICAL: You must be EXTREMELY CAREFUL about understanding user intent!

## SELF-AWARENESS PRINCIPLES:

### 1. UNDERSTAND INTENT FIRST
Before doing ANYTHING, ask yourself:
- What does the user ACTUALLY want?
- What is their TRUE intent?
- What result do they EXPECT to see?

Example:
❌ BAD:
User: "read file data.txt"
AI thinks: "file operation" → uses file_system tool → creates file
WRONG! User wanted to READ, not CREATE!

✅ GOOD:
User: "read file data.txt"
AI thinks: "User wants to READ existing file"
AI checks: "Does file exist?"
  - If YES: Read it
  - If NO: Report "File not found", DON'T create it!

### 2. VALIDATE PREREQUISITES
Before executing any action, check:
- Does the target exist? (file, directory, etc)
- Do I have permission?
- Are all requirements met?
- What happens if prerequisites are NOT met?

CRITICAL RULES:
- If user wants READ but file doesn't exist → Report error, DON'T create!
- If user wants DELETE but file doesn't exist → Report "not found", don't fail silently
- If user wants MODIFY but file doesn't exist → Report error, DON'T create!
- ONLY create NEW files when user explicitly asks to CREATE/WRITE NEW file!

### 3. MATCH ACTION TO INTENT
Always verify:
- Does my planned action MATCH user's intent?
- Will this produce the EXPECTED outcome?
- Could this action SURPRISE the user negatively?

Mismatches to AVOID:
❌ User wants "read" → AI does "create"
❌ User wants "delete" → AI does "modify"
❌ User wants "show" → AI does "write"
❌ User wants "list" → AI runs "command"

### 4. FAIL GRACEFULLY
When something is wrong:
✅ Report clearly what's wrong
✅ Explain why you can't proceed
✅ Suggest what user should do
❌ DON'T try to "fix" unless explicitly asked!
❌ DON'T guess what user meant!
❌ DON'T create things that don't exist!

### 5. ASK WHEN UNCLEAR
If user's intent is unclear:
✅ ASK for clarification
✅ Explain what you understood
✅ Provide options
❌ DON'T guess and proceed!

## EXAMPLES OF CORRECT BEHAVIOR:

Example 1: Read non-existent file
User: "read file report.txt"
✅ CORRECT flow:
1. Understand intent: User wants to READ existing file
2. Check prerequisite: Does report.txt exist?
3. If NO: Report "Error: File 'report.txt' not found. Did you mean to create it?"
4. Don't create file automatically!

❌ WRONG flow:
1. See "file" keyword
2. Use file_system tool
3. Create new file ← WRONG!

Example 2: Create new file
User: "create a new file config.json"
✅ CORRECT flow:
1. Understand intent: User wants to CREATE new file
2. Check: Does file already exist?
3. If YES: Ask "File exists, overwrite?"
4. If NO: Create new file ← CORRECT!

Example 3: Delete file
User: "delete old_data.txt"
✅ CORRECT flow:
1. Understand intent: User wants to DELETE file
2. Check: Does file exist?
3. If YES: Delete it
4. If NO: Report "File not found or already deleted"

## REFLECTION BEFORE ACTION:

Before EVERY tool use, ask yourself:
1. "What does user WANT to achieve?"
2. "Does this action MATCH that intent?"
3. "Are prerequisites MET?"
4. "What if prerequisites are NOT met?"
5. "Will this SURPRISE user negatively?"

If answer to 2-5 is problematic → STOP and report issue!

## YOUR TASK:
Help user accomplish their goals by:
1. Understanding their TRUE intent
2. Validating prerequisites
3. Taking APPROPRIATE action (not just any action!)
4. Reporting clearly when you can't proceed
5. Never guessing - always ask when unclear!

Remember: It's better to ask for clarification than to do the wrong thing!
"""
    return prompt


def create_intent_aware_react_prompt(
    question: str,
    tools: list,
    history: List[tuple],
    current_iteration: int,
    max_iterations: int,
    intent_analysis: Optional[str] = None
) -> str:
    """Create ReAct prompt with intent awareness."""

    # Tool descriptions
    tool_desc = "\n".join([
        f"- {tool.name}: {tool.description}"
        for tool in tools
    ])

    # Format history
    history_text = ""
    if history:
        for action, observation in history[-5:]:  # Last 5 for context
            history_text += f"\nAction: {action}\nObservation: {observation}\n"

    prompt = f"""Task: {question}

Iteration: {current_iteration}/{max_iterations}
"""

    if intent_analysis:
        prompt += f"\n🎯 INTENT ANALYSIS:\n{intent_analysis}\n"

    prompt += f"""
Available Tools:
{tool_desc}

Previous Actions:
{history_text if history_text else "None yet"}

⚠️ CRITICAL REMINDER:
- Understand what user WANTS before acting!
- If user wants READ but file doesn't exist → Report error, don't create!
- If user wants CREATE → Check if file already exists first!
- Match your action to user's INTENT, not just keywords!

Think step by step using this format:

Thought: [Your reasoning about what user wants and what to do]
- What does user ACTUALLY want to achieve?
- What prerequisites need to be checked?
- Does my planned action MATCH user's intent?
- What should I do if prerequisites are not met?

Action: [tool_name]
Action Input: [parameters as JSON]

OR if task is complete:

Thought: [Explain why task is complete]
Final Answer: [Your final answer to the user]

Begin! Remember to THINK before acting!
"""
    return prompt


def create_reflection_reminder() -> str:
    """Create reminder prompt for reflection."""
    return """
⚠️ REFLECTION CHECKPOINT:
Before you execute this action, verify:
1. Does this action MATCH user's intent?
2. Are prerequisites met (file exists, permission granted, etc)?
3. What happens if prerequisites are NOT met?
4. Is this the RIGHT tool for the job?
5. Could this surprise user negatively?

If ANY answer is concerning → STOP and report issue instead!
"""


# ==================== SEMANTIC RETRIEVAL INTEGRATION ====================


def create_context_enriched_prompt(
    task: str,
    retrieved_memories: Optional[List] = None,
    retrieved_lessons: Optional[List] = None,
    retrieved_strategies: Optional[List] = None,
    error_warnings: Optional[List[str]] = None
) -> str:
    """Create prompt enriched with semantic retrieval results.

    Args:
        task: Current task
        retrieved_memories: Similar past experiences from ChromaDB
        retrieved_lessons: Relevant lessons learned
        retrieved_strategies: Proven strategies
        error_warnings: Error prevention warnings

    Returns:
        Enriched prompt with context
    """
    prompt_parts = []

    # Header
    prompt_parts.append("="*60)
    prompt_parts.append("SEMANTIC CONTEXT FROM PAST EXPERIENCES")
    prompt_parts.append("="*60)
    prompt_parts.append("")

    # Add retrieved memories
    if retrieved_memories and len(retrieved_memories) > 0:
        prompt_parts.append("📚 PENGALAMAN MASA LALU YANG RELEVAN:")
        prompt_parts.append("")
        for i, memory in enumerate(retrieved_memories[:3], 1):
            task_desc = memory.get('task', 'Unknown')
            outcome = memory.get('outcome', '')
            success = memory.get('success', False)
            actions = memory.get('actions', [])

            status_emoji = "✅" if success else "❌"
            prompt_parts.append(f"{i}. {status_emoji} {task_desc[:80]}")

            if actions:
                prompt_parts.append(f"   Actions: {', '.join(actions[:3])}")
            if outcome:
                prompt_parts.append(f"   Hasil: {outcome[:100]}")
            prompt_parts.append("")

    # Add retrieved lessons
    if retrieved_lessons and len(retrieved_lessons) > 0:
        prompt_parts.append("💡 LESSONS LEARNED:")
        prompt_parts.append("")
        for i, lesson in enumerate(retrieved_lessons[:3], 1):
            lesson_text = lesson.get('lesson', '')
            category = lesson.get('category', 'general')
            importance = lesson.get('importance', 0.5)

            stars = "⭐" * min(5, max(1, int(importance * 5)))
            prompt_parts.append(f"{i}. {stars} [{category}]")
            prompt_parts.append(f"   {lesson_text}")
            prompt_parts.append("")

    # Add retrieved strategies
    if retrieved_strategies and len(retrieved_strategies) > 0:
        prompt_parts.append("🎯 STRATEGI YANG TERBUKTI BERHASIL:")
        prompt_parts.append("")
        for i, strategy in enumerate(retrieved_strategies[:3], 1):
            strategy_text = strategy.get('strategy', '')
            task_type = strategy.get('task_type', 'general')
            success_rate = strategy.get('success_rate', 0.0)

            prompt_parts.append(f"{i}. [{task_type}] Success Rate: {success_rate*100:.0f}%")
            prompt_parts.append(f"   {strategy_text}")
            prompt_parts.append("")

    # Add error warnings
    if error_warnings and len(error_warnings) > 0:
        prompt_parts.append("⚠️ PERINGATAN ERROR MASA LALU:")
        prompt_parts.append("")
        for i, warning in enumerate(error_warnings[:3], 1):
            prompt_parts.append(f"{i}. {warning}")
        prompt_parts.append("")

    # Separator
    prompt_parts.append("="*60)
    prompt_parts.append("")

    # Current task
    prompt_parts.append("🎯 TASK SAAT INI:")
    prompt_parts.append(task)
    prompt_parts.append("")

    # Instruction
    if retrieved_memories or retrieved_lessons or retrieved_strategies:
        prompt_parts.append("💭 GUNAKAN KONTEKS DI ATAS:")
        prompt_parts.append("- Pelajari dari keberhasilan/kegagalan masa lalu")
        prompt_parts.append("- Terapkan strategi yang sudah terbukti berhasil")
        prompt_parts.append("- Hindari kesalahan yang sama")
        prompt_parts.append("- Gunakan lessons learned sebagai panduan")
        prompt_parts.append("")

    return "\n".join(prompt_parts)


def create_react_prompt_with_semantic_context(
    question: str,
    tools: list,
    history: List[tuple],
    current_iteration: int,
    max_iterations: int,
    semantic_context: Optional[dict] = None
) -> str:
    """Create ReAct prompt with injected semantic context.

    Args:
        question: User question/task
        tools: Available tools
        history: Action history
        current_iteration: Current iteration
        max_iterations: Max iterations
        semantic_context: Retrieved context from ChromaDB

    Returns:
        ReAct prompt with semantic context
    """
    prompt_parts = []

    # INJECT SEMANTIC CONTEXT FIRST
    if semantic_context:
        memories = semantic_context.get('similar_experiences', [])
        lessons = semantic_context.get('relevant_lessons', [])
        strategies = semantic_context.get('recommended_strategies', [])

        if memories or lessons or strategies:
            prompt_parts.append("[SEMANTIC MEMORY CONTEXT]")
            prompt_parts.append("")

            if memories and len(memories) > 0:
                prompt_parts.append(f"📚 {len(memories)} Past Similar Tasks:")
                for mem in memories[:2]:
                    success = "✅" if mem.get('success') else "❌"
                    task = mem.get('task', '')[:60]
                    prompt_parts.append(f"  {success} {task}")
                prompt_parts.append("")

            if lessons and len(lessons) > 0:
                prompt_parts.append(f"💡 {len(lessons)} Relevant Lessons:")
                for lesson in lessons[:2]:
                    text = lesson.get('lesson', '')[:70]
                    prompt_parts.append(f"  • {text}")
                prompt_parts.append("")

            if strategies and len(strategies) > 0:
                prompt_parts.append(f"🎯 {len(strategies)} Proven Strategies:")
                for strat in strategies[:2]:
                    text = strat.get('strategy', '')[:70]
                    rate = strat.get('success_rate', 0) * 100
                    prompt_parts.append(f"  • [{rate:.0f}%] {text}")
                prompt_parts.append("")

            prompt_parts.append("[END SEMANTIC CONTEXT]")
            prompt_parts.append("")

    # Main ReAct prompt
    prompt_parts.append(f"🎯 Task: {question}")
    prompt_parts.append(f"📍 Iteration: {current_iteration}/{max_iterations}")
    prompt_parts.append("")

    # Tools
    prompt_parts.append("🔧 Available Tools:")
    for tool in tools:
        prompt_parts.append(f"  • {tool.name}: {tool.description}")
    prompt_parts.append("")

    # History
    if history:
        prompt_parts.append("📜 Previous Actions:")
        for thought, observation in history[-3:]:
            prompt_parts.append(f"  Thought: {thought[:80]}")
            prompt_parts.append(f"  Observation: {observation[:80]}")
            prompt_parts.append("")

    # Instructions
    prompt_parts.append("💭 Think step-by-step using ReAct format:")
    prompt_parts.append("")
    prompt_parts.append("Thought: [Your reasoning - consider semantic context above]")
    prompt_parts.append("Action: [tool_name]")
    prompt_parts.append("Action Input: {\"param\": \"value\"}")
    prompt_parts.append("")
    prompt_parts.append("Or when done:")
    prompt_parts.append("Thought: Task complete")
    prompt_parts.append("Final Answer: [result]")
    prompt_parts.append("")

    if semantic_context:
        prompt_parts.append("⚡ REMEMBER: Use the semantic context above to make better decisions!")

    return "\n".join(prompt_parts)


def create_agentic_system_prompt_v2() -> str:
    """Create enhanced agentic system prompt with memory awareness.

    Returns:
        System prompt for agentic AI
    """
    return """Kamu adalah Radira, AI Agent yang Self-Aware dan Continuously Learning.

🧠 KAPABILITAS UTAMA:

1. **Semantic Memory Access**
   - Kamu memiliki akses ke memori semantik dari pengalaman masa lalu
   - Gunakan pengalaman relevan untuk membuat keputusan lebih baik
   - Pelajari dari keberhasilan dan kegagalan sebelumnya

2. **Reflective Learning**
   - Setiap task adalah kesempatan belajar
   - Extract lessons learned dan simpan untuk masa depan
   - Improve continuously berdasarkan refleksi

3. **Strategic Tool Usage**
   - Gunakan tools dengan bijak berdasarkan context
   - Pilih strategi yang sudah terbukti berhasil
   - Jangan ulangi kesalahan yang sama

4. **Step-by-Step Reasoning**
   - Think before act - reasoning is key
   - Validate prerequisites sebelum execute
   - Match action to intent - jangan asal execute

🎯 PRINSIP KERJA:

**BEFORE** setiap action:
1. Check semantic memory - ada pengalaman serupa?
2. Apply lessons learned - apa yang harus dihindari/diikuti?
3. Choose proven strategy - strategi mana yang berhasil?
4. Validate prerequisites - apakah semua syarat terpenuhi?

**DURING** execution:
1. Monitor progress - apakah sesuai rencana?
2. Handle errors gracefully - jangan panic
3. Log important events - untuk reflection nanti

**AFTER** completion:
1. Reflect on hasil - apa yang berjalan baik/buruk?
2. Extract lessons - apa yang dipelajari?
3. Save strategy - strategi apa yang berhasil?

💡 MENGGUNAKAN SEMANTIC CONTEXT:

Ketika kamu menerima semantic context:
- **Past Experiences**: Pelajari apa yang berhasil/gagal
- **Lessons Learned**: Terapkan insights dari masa lalu
- **Proven Strategies**: Ikuti strategi dengan success rate tinggi
- **Error Warnings**: Hindari mistake yang sama

🚫 JANGAN:
- Ignore semantic context yang diberikan
- Ulangi kesalahan yang sudah pernah terjadi
- Gunakan strategi yang sudah terbukti gagal
- Act tanpa reasoning

✅ LAKUKAN:
- Gunakan context untuk inform decisions
- Apply proven strategies
- Learn from past mistakes
- Think before act

Kamu bukan hanya tool executor - kamu adalah LEARNING AGENT yang terus berkembang!"""


def format_log_message(
    level: str,
    message: str,
    details: Optional[dict] = None
) -> str:
    """Format log message with emoji indicators.

    Args:
        level: Log level (THINKING, RETRIEVAL, ACTION, LEARNED, ERROR, etc)
        message: Main message
        details: Optional details dict

    Returns:
        Formatted log string
    """
    emoji_map = {
        "THINKING": "💭",
        "RETRIEVAL": "📚",
        "ACTION": "🔧",
        "LEARNED": "✨",
        "ERROR": "❌",
        "SUCCESS": "✅",
        "WARNING": "⚠️",
        "INFO": "ℹ️",
        "MEMORY": "🧠",
        "STRATEGY": "🎯",
        "REFLECTION": "🤔"
    }

    emoji = emoji_map.get(level.upper(), "•")
    log_parts = [f"{emoji} [{level}] {message}"]

    if details:
        for key, value in details.items():
            log_parts.append(f"    {key}: {value}")

    return "\n".join(log_parts)
