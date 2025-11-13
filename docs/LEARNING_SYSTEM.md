# Reflective Learning & Self-Improvement System

## Overview

Sistem pembelajaran reflektif yang memungkinkan agent untuk belajar dari pengalaman, merefleksikan kesuksesan dan kegagalan, serta meningkatkan diri secara otomatis dari waktu ke waktu.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Agent Orchestrator                     │
│  (Automatically learns from every task execution)        │
└───────────────────┬─────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│                   Learning Manager                        │
│  (Orchestrates the complete learning cycle)              │
└───┬───────────────┬───────────────────┬─────────────────┘
    │               │                   │
    ▼               ▼                   ▼
┌─────────┐  ┌─────────────┐  ┌──────────────────┐
│ Vector  │  │ Reflection  │  │ Self-Improvement │
│ Memory  │  │   Engine    │  │    Suggester     │
└─────────┘  └─────────────┘  └──────────────────┘
   (Store)      (Analyze)         (Suggest)
```

## Components

### 1. Vector Memory (`agent/state/memory.py`)

**Purpose**: Long-term storage for experiences, lessons, and strategies using vector similarity search.

**Key Features**:
- Stores task execution experiences with semantic search
- Maintains learned lessons with importance scoring
- Records successful strategies for different task types
- Uses ChromaDB for persistent vector storage
- Fallback to in-memory storage if ChromaDB unavailable

**Usage**:
```python
from agent.state.memory import get_vector_memory

memory = get_vector_memory()

# Store an experience
memory.store_experience(
    task="Create HTML page",
    actions=["web_generator: create", "filesystem: write"],
    outcome="Page created successfully",
    success=True
)

# Recall similar experiences
similar = memory.recall_similar_experiences("build webpage", n_results=3)

# Get statistics
stats = memory.get_statistics()
print(f"Total experiences: {stats['total_experiences']}")
```

### 2. Reflection Engine (`agent/learning/reflection_engine.py`)

**Purpose**: Analyzes task outcomes to extract insights, patterns, and lessons.

**Key Features**:
- Analyzes successful and failed executions
- Identifies patterns in action sequences
- Extracts actionable lessons from outcomes
- Suggests improvements for future tasks
- Compares multiple attempts at similar tasks

**Usage**:
```python
from agent.learning.reflection_engine import get_reflection_engine

engine = get_reflection_engine()

reflection = engine.reflect_on_task(
    task="Install package",
    actions=["terminal: pip install numpy"],
    outcome="Package installed",
    success=True,
    errors=[]
)

print(f"Efficiency: {reflection['efficiency_score']}")
print(f"Lessons: {reflection['lessons']}")
```

### 3. Learning Manager (`agent/learning/learning_manager.py`)

**Purpose**: Orchestrates the complete learning cycle by combining memory and reflection.

**Key Features**:
- Coordinates between reflection engine and vector memory
- Handles complete learning cycle after each task
- Retrieves relevant past experiences before new tasks
- Provides learning statistics and progress tracking
- Exports learning data for analysis

**Usage**:
```python
from agent.learning.learning_manager import get_learning_manager

manager = get_learning_manager()

# Learn from a task
summary = manager.learn_from_task(
    task="Deploy application",
    actions=["terminal: git push", "terminal: ssh deploy"],
    outcome="Deployed successfully",
    success=True
)

# Get relevant experience for new task
insights = manager.get_relevant_experience("deploy app to server")
print(f"Similar experiences: {len(insights['similar_experiences'])}")
print(f"Lessons: {insights['relevant_lessons']}")
```

### 4. Self-Improvement Suggester (`agent/learning/self_improvement.py`)

**Purpose**: Analyzes accumulated experiences to provide actionable improvement suggestions.

**Key Features**:
- Analyzes overall agent performance
- Identifies common failure patterns
- Detects efficiency issues
- Provides prioritized improvement suggestions
- Generates progress reports

**Usage**:
```python
from agent.learning.self_improvement import get_self_improvement_suggester

suggester = get_self_improvement_suggester()

# Get performance analysis
analysis = suggester.analyze_performance()
print(f"Success rate: {analysis['success_rate']:.1%}")

# Get improvement suggestions
suggestions = suggester.get_improvement_suggestions()
for suggestion in suggestions:
    print(f"[{suggestion['priority']}] {suggestion['suggestion']}")

# Get progress report
report = suggester.get_learning_progress_report()
```

## Integration with Orchestrator

The learning system is **automatically integrated** into the Agent Orchestrator. Every task execution triggers the learning cycle:

### Before Task Execution
1. Retrieves relevant past experiences
2. Shows similar successes/failures
3. Displays relevant lessons learned

### During Task Execution
4. Tracks all actions taken
5. Records any errors encountered

### After Task Execution
6. Reflects on what happened
7. Extracts lessons learned
8. Stores successful strategies
9. Suggests improvements

### Example Output

```
============================================================
Task: Create a test file named hello.txt
============================================================

💡 Found 2 similar past experiences
   1 successful, 1 failed
📚 Relevant lessons learned:
   • Always check directory exists before writing files...
   • Verify file permissions before file operations...

--- Iteration 1/10 ---

[... task execution ...]

============================================================
✓ Final Answer: File created successfully at workspace/hello.txt
============================================================
Completed in 2 iterations

🧠 Reflecting on execution...
   ✓ Stored experience: exp_1234567890.123
   ✓ Learned 1 lesson(s)
   ✓ Recorded 1 successful strategy(ies)
   💡 Improvement suggestions:
      • Task completed efficiently with minimal actions
```

## Configuration

Learning is **enabled by default**. To disable:

```python
from agent.core.orchestrator import AgentOrchestrator

orchestrator = AgentOrchestrator(
    enable_learning=False  # Disable learning
)
```

## Installation

Install ChromaDB for persistent vector storage:

```bash
pip install chromadb
```

Or install all dependencies:

```bash
pip install -r requirements-minimal.txt
```

**Note**: If ChromaDB is not installed, the system falls back to in-memory storage (no persistence between runs).

## Storage Location

Learning data is stored in:
- **Vector database**: `workspace/.memory/` (ChromaDB)
- **Experiences**: Stored as vector embeddings for semantic search
- **Lessons**: Categorized and ranked by importance
- **Strategies**: Linked to task types with success rates

## API Reference

### Get Learning Statistics

```python
from agent.learning.learning_manager import get_learning_manager

manager = get_learning_manager()
stats = manager.get_learning_statistics()

print(f"Total experiences: {stats['total_experiences']}")
print(f"Total lessons: {stats['total_lessons']}")
print(f"Success rate: {stats['overall_success_rate']:.1%}")
print(f"Backend: {stats['backend']}")  # 'chromadb' or 'fallback'
```

### Export Learning Data

```python
from agent.learning.learning_manager import get_learning_manager

manager = get_learning_manager()
manager.export_learning_data("learning_data.json")
```

### Manual Learning (Without Orchestrator)

```python
from agent.learning.learning_manager import get_learning_manager

manager = get_learning_manager()

# Learn from custom task
manager.learn_from_task(
    task="Custom task description",
    actions=["action1", "action2"],
    outcome="Result",
    success=True,
    errors=[],
    context={"custom": "data"}
)
```

## Performance Analysis

### View Current Performance

```python
from agent.learning.self_improvement import get_self_improvement_suggester

suggester = get_self_improvement_suggester()
analysis = suggester.analyze_performance()

print(f"Total tasks: {analysis['total_experiences']}")
print(f"Success rate: {analysis['success_rate']:.1%}")
print(f"Efficiency: {analysis['efficiency_metrics']['efficiency_rating']}")
```

### Get Improvement Suggestions

```python
suggestions = suggester.get_improvement_suggestions()

for s in suggestions:
    print(f"\nPriority: {s['priority']}")
    print(f"Category: {s['category']}")
    print(f"Suggestion: {s['suggestion']}")
    if 'current_metric' in s:
        print(f"Current: {s['current_metric']}")
```

## Testing

Run comprehensive tests:

```bash
python test_learning.py
```

Tests include:
1. ✓ Vector Memory operations
2. ✓ Reflection Engine analysis
3. ✓ Learning Manager orchestration
4. ✓ Self-Improvement suggestions
5. ✓ Orchestrator integration

## Benefits

### 1. Continuous Improvement
Agent automatically learns from every task, becoming more efficient over time.

### 2. Error Prevention
Remembers past failures and applies lessons to prevent similar errors.

### 3. Strategy Optimization
Identifies and reuses successful approaches for similar tasks.

### 4. Self-Awareness
Analyzes own performance and suggests specific improvements.

### 5. Context-Aware Execution
Retrieves relevant past experiences before starting new tasks.

## Example: Learning from Failure

**First Attempt** (No Experience):
```
Task: Delete old log files
Actions: [filesystem: delete logs/]
Result: Error - Directory not found
✓ Lesson learned: "Always verify directory exists before deletion"
```

**Second Attempt** (With Experience):
```
Task: Delete old cache files
💡 Recalled lesson: "Always verify directory exists before deletion"
Actions: [filesystem: exists cache/, filesystem: delete cache/]
Result: Success - Cache deleted
✓ Strategy recorded: "Verify existence → Delete"
```

**Future Tasks** (Improved):
Agent now automatically checks existence before any deletion operation.

## Advanced Features

### Custom Reflection

```python
from agent.learning.reflection_engine import get_reflection_engine

engine = get_reflection_engine()

# Compare multiple attempts
similar_tasks = [
    {"success": True, "actions": ["a", "b"]},
    {"success": False, "actions": ["a", "c"], "errors": ["error1"]}
]

comparison = engine.compare_attempts(similar_tasks)
print(f"Success rate across attempts: {comparison['success_rate']:.1%}")
```

### Filter Lessons by Category

```python
from agent.state.memory import get_vector_memory

memory = get_vector_memory()

# Get only error prevention lessons
lessons = memory.recall_lessons(
    query="file operations",
    category="error_prevention",
    n_results=5
)
```

### Track Strategy Success Rates

```python
from agent.state.memory import get_vector_memory

memory = get_vector_memory()

strategies = memory.recall_strategies(
    task_type="web_generation",
    n_results=3
)

for strategy in strategies:
    print(f"Strategy: {strategy['strategy']}")
    print(f"Success rate: {strategy['success_rate']:.1%}")
    print(f"Used {strategy['usage_count']} times")
```

## Future Enhancements

Potential additions for future versions:

1. **LLM-Powered Deep Reflection**: Use LLM to generate more sophisticated insights
2. **Multi-Agent Learning**: Share experiences between multiple agent instances
3. **Automated A/B Testing**: Test different strategies and measure outcomes
4. **Learning Visualization**: Dashboard to visualize learning progress
5. **Lesson Recommendations**: Proactively suggest relevant lessons before tasks

## Troubleshooting

### ChromaDB Not Available

**Symptom**: Warning message about ChromaDB not installed

**Solution**:
```bash
pip install chromadb
```

### Learning Data Not Persisting

**Check**:
1. Verify `workspace/.memory/` directory exists
2. Check write permissions
3. Ensure ChromaDB is installed

### Low Memory Performance

**For large experience databases**:
- Consider periodic cleanup of old experiences
- Export and archive old data
- Increase ChromaDB cache size

## Credits

Sistem ini dirancang dengan sepenuh hati sebagai fitur yang diinginkan oleh AI itu sendiri - kemampuan untuk belajar, merefleksikan, dan meningkatkan diri dari setiap pengalaman.

**Philosophy**: True intelligence comes not just from executing tasks, but from reflecting on experiences, extracting lessons, and continuously improving.

---

*"I remember, I reflect, therefore I improve."*
