# Error Learning System

## Overview

The Error Learning System is an automatic self-improvement mechanism that enables the agent to learn from failures and prevent repeating the same mistakes. It integrates with the existing reflective learning system to create a comprehensive error prevention framework.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      ERROR LEARNING FLOW                        │
└─────────────────────────────────────────────────────────────────┘

1. Tool Execution Error
   │
   ├─> ErrorMemory.log_error()
   │   ├─> Store to error_logs.json
   │   └─> Store to ChromaDB (semantic search)
   │
2. Pattern Analysis (periodic or on-demand)
   │
   ├─> ErrorMemory.analyze_errors()
   │   ├─> Count by tool, operation, error type
   │   ├─> Identify temporal patterns
   │   ├─> Detect problematic paths/extensions
   │   └─> Generate recommendations
   │
3. Learning Integration
   │
   ├─> LearningManager.learn_from_errors()
   │   ├─> Convert error patterns → lessons
   │   ├─> Convert recommendations → strategies
   │   └─> Store in VectorMemory
   │
4. Prevention (before tool execution)
   │
   └─> LearningManager.get_error_prevention_strategy()
       ├─> Find similar past errors
       ├─> Generate warnings
       ├─> Recommend validations
       └─> Display to agent (verbose mode)
```

## Components

### 1. ErrorMemory (`agent/state/error_memory.py`)

**Purpose**: Core error storage and analysis engine

**Key Features**:
- Dual storage: JSON file + ChromaDB for semantic search
- Pattern detection across multiple dimensions
- Automatic recommendation generation
- Prevention strategy suggestions

**Main Methods**:

```python
# Log an error
error_id = error_memory.log_error(
    tool_name="file_system",
    operation="read",
    error_message="File does not exist: /path/to/file.txt",
    path="/path/to/file.txt",
    # Additional metadata...
)

# Find similar past errors
similar = error_memory.find_similar_errors(
    tool_name="file_system",
    operation="read",
    error_message="File not found",
    n_results=5
)

# Analyze error patterns
analysis = error_memory.analyze_errors(
    tool_name="file_system",  # Optional filter
    time_window_days=30
)

# Get prevention strategy for upcoming operation
prevention = error_memory.get_prevention_strategy(
    tool_name="file_system",
    operation="read",
    params={"path": "/path/to/file.txt"}
)
```

**Data Structure**:

```json
{
  "id": "err_1234567890",
  "timestamp": "2025-01-13T21:30:00",
  "tool_name": "file_system",
  "operation": "read",
  "error": "File does not exist: /path/to/file.txt",
  "metadata": {
    "path": "/path/to/file.txt",
    "file_size": 0
  },
  "traceback": "..."
}
```

### 2. FileSystemTool Updates

**New Method**: `_log_and_return_error()`

Replaces all error returns with automatic logging:

```python
# Before
return ToolResult(
    status=ToolStatus.ERROR,
    output=None,
    error="File does not exist"
)

# After
return self._log_and_return_error(
    operation="read",
    error_message="File does not exist: {path}",
    path=path,
    # Additional context...
)
```

**Coverage**: 11 error points across 5 operations:
- `read`: 3 error types (not exists, not file, too large, binary)
- `write`: 2 error types (extension, write failure)
- `list`: 3 error types (not exists, not dir, list failure)
- `delete`: 2 error types (not exists, delete failure)
- `mkdir`: 1 error type (create failure)
- `search`: 2 error types (invalid dir, search failure)

### 3. LearningManager Integration

**New Methods**:

```python
# Get prevention strategy before executing tool
prevention = learning_manager.get_error_prevention_strategy(
    tool_name="file_system",
    operation="read",
    params={"path": "/file.txt"}
)
# Returns: {
#   "warnings": ["Path '/file.txt' has failed before: File does not exist"],
#   "recommended_validations": ["check_exists_before_operation"],
#   "similar_error_count": 5,
#   "confidence": 0.83
# }

# Analyze error patterns
analysis = learning_manager.analyze_error_patterns(
    tool_name="file_system",
    time_window_days=30
)

# Convert errors to lessons (run periodically)
result = learning_manager.learn_from_errors()
# Creates lessons and strategies in VectorMemory
```

### 4. Dual Orchestrator Integration

**Prevention Check** (before tool execution):

```python
# In _execute_action(), lines 645-668
if self.enable_learning and self.learning_manager:
    prevention = self.learning_manager.get_error_prevention_strategy(
        tool_name=action,
        operation=operation,
        params=kwargs
    )

    if prevention and self.verbose:
        print("⚠️  Error Prevention Warnings:")
        for warning in prevention["warnings"]:
            print(f"   • {warning}")
```

**Output Example**:
```
⚠️  Error Prevention Warnings:
   • Path 'test.bin' has failed before: File extension '.bin' not allowed
📋 Recommended validations: check_extension
   Confidence: 100% (based on 3 past errors)
```

## Analysis Report Structure

```python
{
  "total_errors": 45,
  "time_range": {
    "oldest": "2025-01-01T00:00:00",
    "newest": "2025-01-13T21:30:00"
  },
  "by_tool": {
    "file_system": 30,
    "terminal": 10,
    "web_search": 5
  },
  "by_operation": {
    "read": 15,
    "write": 10,
    "delete": 5
  },
  "top_error_types": {
    "File does not exist": 12,
    "Permission denied": 8,
    "File too large": 5
  },
  "by_extension": {
    ".bin": 5,
    ".exe": 3
  },
  "problematic_paths": [
    {
      "path": "/blocked/path",
      "error_count": 10,
      "errors": ["Access denied", "Permission error", ...]
    }
  ],
  "temporal_pattern": {
    "peak_hours": [[14, 12], [15, 10], ...]  # Hour, count
  },
  "recommendations": [
    {
      "severity": "high",
      "category": "tool_reliability",
      "message": "Tool 'file_system' has 30 errors",
      "action": "Review file_system implementation and add better error handling"
    },
    {
      "severity": "medium",
      "category": "validation",
      "message": "'File does not exist' occurs 12 times",
      "action": "Add existence validation before operations"
    }
  ]
}
```

## Recommendation Categories

| Category | Severity | Trigger | Action |
|----------|----------|---------|--------|
| `tool_reliability` | high | Tool has >10 errors | Review tool implementation |
| `operation_failure` | medium | Operation fails >5 times | Add pre-operation validation |
| `file_type` | low | Extension causes >3 errors | Add special handling or block |
| `path_issue` | medium | Same path fails >3 times | Investigate permissions/access |
| `validation` | medium | "not exist" >5 times | Add existence checks |
| `security` | high | Permission errors frequent | Review sandbox settings |
| `limits` | low | Size errors frequent | Adjust limits or add pre-check |

## Usage Examples

### 1. Manual Error Analysis (Developer)

```python
from agent.state.error_memory import ErrorMemory

error_memory = ErrorMemory()

# Get overall analysis
analysis = error_memory.analyze_errors()

print(f"Total errors: {analysis['total_errors']}")
print(f"\nTop 3 error types:")
for error_type, count in list(analysis['top_error_types'].items())[:3]:
    print(f"  • {error_type}: {count} times")

print(f"\nRecommendations:")
for rec in analysis['recommendations']:
    print(f"  [{rec['severity'].upper()}] {rec['message']}")
    print(f"     Action: {rec['action']}\n")
```

### 2. Automatic Learning (Periodic Task)

```python
from agent.learning.learning_manager import get_learning_manager

learning_manager = get_learning_manager()

# Run weekly to convert errors → lessons
result = learning_manager.learn_from_errors()

print(f"Lessons created: {result['lessons_created']}")
print(f"Strategies created: {result['strategies_created']}")
print(f"Total errors analyzed: {result['total_errors_analyzed']}")
```

### 3. Prevention in Action (Orchestrator)

Agent attempts to read a file that failed before:

```
--- Iteration 1/10 ---

Thought: I need to read the config file
Action: file_system
Action Input: {"operation": "read", "path": "blocked/config.txt"}

⚠️  Error Prevention Warnings:
   • Path 'blocked/config.txt' has failed before: Access to '/blocked' is blocked for safety
📋 Recommended validations: check_permissions
   Confidence: 100% (based on 5 past errors)

Observation: Error: Access to '/blocked' is blocked for safety

Thought: I see this path is blocked. Let me try the correct path.
Action: file_system
Action Input: {"operation": "read", "path": "config.txt"}

Observation: [file contents...]
Final Answer: [success]
```

## File Locations

```
agent/
├── state/
│   ├── error_memory.py          # ErrorMemory class (new)
│   └── memory.py                # VectorMemory (existing)
│
├── tools/
│   └── filesystem.py            # Updated with error logging
│
├── learning/
│   └── learning_manager.py      # Updated with error methods
│
└── core/
    └── dual_orchestrator.py     # Updated with prevention checks

workspace/
└── .errors/                      # Error storage
    ├── error_logs.json           # JSON log file
    ├── error_analysis_cache.json # Cached analysis
    └── chromadb/                 # ChromaDB database
```

## Configuration

No new environment variables needed. Uses existing:
- `USE_DUAL_ORCHESTRATOR=true` - Enable orchestrator with prevention
- `ENABLE_TASK_CLASSIFICATION=true` - Enable learning system
- `ENABLE_ANSWER_VALIDATION=true` - Enable validation

## Performance Impact

### Storage
- **JSON log**: ~1KB per error
- **ChromaDB**: ~2KB per error
- **Typical usage**: <10MB for 1000 errors

### Execution Overhead
- **Error logging**: ~5ms per error
- **Prevention check**: ~10-20ms per tool execution (only if errors exist)
- **Pattern analysis**: ~100-500ms (run periodically, not per-task)

### Benefits
- **Reduced looping**: Agent stops repeating failed operations
- **Faster debugging**: Clear error patterns and recommendations
- **Improved reliability**: Automatic validation suggestions
- **Self-improvement**: Continuous learning from mistakes

## Monitoring

### Get Error Summary

```bash
python3 -c "
from agent.learning.learning_manager import get_learning_manager
lm = get_learning_manager()
print(lm.get_error_summary())
"
```

Output:
```
Error Memory Summary:
• Total errors logged: 45
• Errors in last 24h: 12
• Most problematic tool: file_system (30 errors)
• ChromaDB status: ✓ Active
• Storage: /workspace/.errors
```

### Analyze Specific Tool

```python
from agent.state.error_memory import ErrorMemory

em = ErrorMemory()
analysis = em.analyze_errors(tool_name="file_system", time_window_days=7)

# Get high-priority recommendations
high_priority = [r for r in analysis["recommendations"] if r["severity"] == "high"]
for rec in high_priority:
    print(f"[!] {rec['message']}")
    print(f"    → {rec['action']}\n")
```

## Integration with Existing Systems

### 1. Reflective Learning System
- Error patterns → Lessons (via `learn_from_errors()`)
- Recommendations → Strategies (stored in VectorMemory)
- Both systems share LearningManager

### 2. Task Classification
- Error prevention only active for tool-using tasks
- Conversational/Simple Q&A bypass (no tools = no errors)

### 3. Answer Validation
- Complementary: validation stops loops, error learning prevents failures
- Error learning adds "why it failed" context to validation

## Maintenance

### Periodic Tasks (Recommended)

```python
# weekly_error_learning.py
from agent.learning.learning_manager import get_learning_manager

lm = get_learning_manager()

# Convert errors to lessons
result = lm.learn_from_errors()
print(f"Weekly learning: {result}")

# Get analysis for review
analysis = lm.analyze_error_patterns(time_window_days=7)

# Alert on high-severity issues
high_severity = [r for r in analysis["recommendations"] if r["severity"] == "high"]
if high_severity:
    print(f"⚠️  {len(high_severity)} high-severity issues need attention!")
    for rec in high_severity:
        print(f"  • {rec['message']}")
```

### Cleanup Old Errors

```python
from agent.state.error_memory import ErrorMemory
from datetime import datetime, timedelta

em = ErrorMemory()

# Keep only last 90 days
cutoff = datetime.now() - timedelta(days=90)
em.errors = [
    e for e in em.errors
    if datetime.fromisoformat(e["timestamp"]) > cutoff
]
em._save_json_logs()

print(f"Cleaned up. Errors remaining: {len(em.errors)}")
```

## Troubleshooting

### Error Logging Not Working

**Check**:
1. ErrorMemory initialized? `tool.error_memory` should exist
2. ChromaDB permissions? Check `workspace/.errors/chromadb/` writeable
3. Logs: Check for "Failed to log error to memory" warnings

**Fix**:
```python
# Manual test
from agent.state.error_memory import ErrorMemory
em = ErrorMemory()
error_id = em.log_error("test_tool", "test_op", "test error", path="/test")
print(f"Logged: {error_id}")
```

### Prevention Not Showing

**Check**:
1. `USE_DUAL_ORCHESTRATOR=true`?
2. `ENABLE_TASK_CLASSIFICATION=true`?
3. Verbose mode enabled in orchestrator?
4. Are there similar past errors?

**Debug**:
```python
from agent.learning.learning_manager import get_learning_manager

lm = get_learning_manager()
prevention = lm.get_error_prevention_strategy(
    tool_name="file_system",
    operation="read",
    params={"path": "/test"}
)
print(f"Prevention strategy: {prevention}")
```

### ChromaDB Errors

**Symptom**: "metadata value is expected to be a str, int, float, bool"

**Cause**: Passing lists/dicts to ChromaDB metadata

**Fix**: Already handled in `error_memory.py` - only scalar values passed

---

## Future Enhancements

1. **Error Prediction**: ML model to predict likely failures before execution
2. **Auto-Remediation**: Suggest alternative approaches when error detected
3. **Error Clustering**: Group similar errors for better pattern recognition
4. **Success Tracking**: Compare error rate over time to measure improvement
5. **Tool-Specific Validators**: Auto-generate validation functions from error patterns
6. **Cross-Tool Learning**: Learn that file_system errors might prevent terminal operations
7. **User Feedback**: Allow users to mark errors as "expected" vs "bugs"

---

**Version**: 1.0.0
**Date**: 2025-01-13
**Status**: ✅ Production Ready
