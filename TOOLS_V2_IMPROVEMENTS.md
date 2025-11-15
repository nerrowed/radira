# Tools V2 - LLM-Friendly Improvements

## Overview

This update improves the file system and terminal tools to be more LLM-friendly, reducing errors and confusion when LLMs interact with the system.

## Key Improvements

### 1. **Modular File System Tools** (`agent/tools/filesystem_v2.py`)

**Problem**: The old `FileSystemTool` used a single tool with an `operation` parameter that could be one of many values (read, write, list, delete, mkdir, exists, search). This was confusing for LLMs and led to errors in parameter selection.

**Solution**: Split into **7 separate, focused tools**, each with a single clear purpose:

| Tool Name | Purpose | Key Parameters |
|-----------|---------|----------------|
| `read_file` | Read file contents | `path` |
| `write_file` | Write content to file | `path`, `content` |
| `list_directory` | List directory contents | `path` |
| `create_directory` | Create new directory | `path` |
| `delete_file` | Delete file or directory | `path` |
| `search_files` | Search files by pattern | `path`, `pattern` |
| `check_file_exists` | Check if path exists | `path` |

**Benefits**:
- ✅ Each tool has ONE clear purpose
- ✅ Simpler parameter structure (no operation field)
- ✅ Better descriptions with use cases
- ✅ More intuitive for LLMs to select the right tool
- ✅ Reduced chance of using wrong operation type

### 2. **Enhanced Terminal Tool** (`agent/tools/terminal_v2.py`)

**Problem**: The old `TerminalTool` had minimal descriptions and unhelpful error messages that didn't guide LLMs on what commands are allowed.

**Solution**: Enhanced with:

#### Better Descriptions
- Detailed description of what the tool does
- Clear examples of common use cases
- List of allowed command categories
- Explanation of safety restrictions

#### Improved Error Messages
Error messages now include:
- ❌ Clear indication of what went wrong
- 💡 Helpful suggestions for alternatives
- ⚠️ Context-aware guidance

Example error messages:
```
❌ Command blocked for safety: 'rm' is a dangerous command and is not allowed

💡 Suggestion: Use the 'delete_file' tool instead to safely delete files or directories.
```

#### Context-Aware Error Enhancement
For common errors, the tool adds helpful context:

- **Git errors**: Explains repository initialization, staging, etc.
- **Package manager errors**: Suggests checking package names or internet connection
- **Python errors**: Guides on file paths and module installation
- **File not found**: Reminds to check paths and existence

### 3. **Comprehensive Tool Descriptions**

All V2 tools now include:

1. **Clear purpose statement**: "Use this when you need to..."
2. **Common use cases**: Bulleted list of scenarios
3. **Parameter descriptions**: Detailed explanation of each parameter
4. **Multiple examples**: Real-world usage patterns
5. **Important warnings**: Highlighted cautions (e.g., "WARNING: This will overwrite existing files")

Example from `write_file`:
```
Write content to a file (creates new file or overwrites existing).

Use this when you need to:
- Create a new file with content
- Update/overwrite an existing file
- Save generated code or configuration
- Write output to a file

The file will be created if it doesn't exist. Parent directories will be created automatically.
WARNING: This will overwrite existing files without warning!
```

## Backward Compatibility

The old tools (`FileSystemTool`, `TerminalTool`) are **still registered** and available for backward compatibility. This means:
- Existing code continues to work
- New LLM interactions benefit from V2 tools
- Gradual migration is possible

## Tool Registration

Updated `main.py` to register both V2 and legacy tools:

```python
# V2 tools (LLM-friendly)
ReadFileTool(...)
WriteFileTool(...)
ListDirectoryTool(...)
CreateDirectoryTool(...)
DeleteFileTool(...)
SearchFilesTool(...)
CheckFileExistsTool(...)
TerminalToolV2(...)

# Legacy tools (backward compatibility)
FileSystemTool(...)
TerminalTool(...)
```

## Expected Impact

### For LLMs
- ✅ Clearer tool selection (fewer mistakes)
- ✅ Better understanding of what each tool does
- ✅ Helpful error recovery suggestions
- ✅ More successful task completions

### For Users
- ✅ Fewer errors in automated tasks
- ✅ More reliable file operations
- ✅ Better error messages for debugging
- ✅ Smoother experience overall

## Examples

### Before (FileSystemTool)
```python
# Confusing - need to remember operation types
tool.execute(operation="read", path="file.txt")
tool.execute(operation="write", path="file.txt", content="...")
tool.execute(operation="list", path=".")
```

### After (V2 Tools)
```python
# Clear - each tool has obvious purpose
read_file.execute(path="file.txt")
write_file.execute(path="file.txt", content="...")
list_directory.execute(path=".")
```

## Testing

All V2 tools have been validated for:
- ✅ Syntax correctness (Python compilation)
- ✅ Import structure
- ✅ Parameter definitions
- ✅ Error handling
- ✅ Integration with existing registry

Test file: `test_tools_v2.py` (comprehensive test suite)

## Files Changed

1. **New Files**:
   - `agent/tools/filesystem_v2.py` - Modular file system tools
   - `agent/tools/terminal_v2.py` - Enhanced terminal tool
   - `test_tools_v2.py` - Test suite for V2 tools
   - `TOOLS_V2_IMPROVEMENTS.md` - This documentation

2. **Modified Files**:
   - `main.py` - Updated tool registration

## Migration Guide

To use V2 tools in your LLM prompts:

### File Operations
**Old way**:
```
Use file_system tool with operation='read' and path='...'
```

**New way**:
```
Use read_file tool with path='...'
```

### Terminal Commands
**Old way**:
```
Use terminal tool to run: ls -la
```

**New way**:
```
Use run_terminal_command to execute: ls -la
```

The new tools will provide better guidance if parameters are missing or incorrect.

## Future Enhancements

Potential future improvements:
- [ ] Add file editing tool (partial updates)
- [ ] Add file copying/moving tools
- [ ] Add file permissions checking tool
- [ ] Add more terminal command helpers (git-specific, npm-specific)
- [ ] Add command history/suggestions based on context
- [ ] Interactive command building for complex operations

## Summary

The V2 tools make the system **significantly more LLM-friendly** by:
1. **Splitting complex tools** into simple, focused operations
2. **Improving descriptions** with clear use cases and examples
3. **Enhancing error messages** with helpful recovery suggestions
4. **Maintaining backward compatibility** with existing tools

This should result in **fewer errors** and **more successful automated tasks** when LLMs interact with the file system and terminal.
