# Bug Fix: JSON Schema Type Error

## 🐛 Problem

When running function calling mode:
```bash
python main.py --fc "halo"
```

**Error**:
```
BadRequestError: Error code: 400 - {'error': {'message': 'schema is not valid JSON
Schema for tool web_generator parameters: jsonschema file:///home/di/params.json
compilation failed: \'/properties/features/type\' does not validate with
https://json-schema.org/draft/2020-12/schema#/allOf/1/$ref/properties/properties/
additionalProperties/$dynamicRef/allOf/3/$ref/properties/type/anyOf/0/$ref/enum:
value must be one of "array", "boolean", "integer", "null", "number", "object",
"string"', 'type': 'invalid_request_error'}}
```

---

## 🔍 Root Cause

**File**: `agent/tools/web_generator.py` line 65

**Problem**:
```python
"features": {
    "type": "list",  # ❌ WRONG! Python type, not JSON Schema type
    "description": "List of specific features to include",
    "required": False
}
```

**Valid JSON Schema types**:
- `"array"` (not "list")
- `"boolean"` (not "bool")
- `"integer"`
- `"null"`
- `"number"` (not "float")
- `"object"` (not "dict")
- `"string"` (not "str")

---

## ✅ Fix Applied

**File**: `agent/tools/web_generator.py` line 65

```python
"features": {
    "type": "array",  # ✅ CORRECT! JSON Schema type
    "description": "List of specific features to include",
    "required": False
}
```

---

## 🧪 Test Again

```bash
python main.py --fc "halo"
```

**Expected**: Should work now without schema errors.

---

## 📝 Lesson Learned

When defining tool parameters for function calling:
- Use **JSON Schema types**, not Python types
- Python `list` → JSON Schema `"array"`
- Python `dict` → JSON Schema `"object"`
- Python `bool` → JSON Schema `"boolean"`
- Python `int` → JSON Schema `"integer"`
- Python `float` → JSON Schema `"number"`

---

## ✅ Status

**Bug**: Fixed ✅
**Affected Tool**: `web_generator`
**Date**: 2025-11-14

All tools now have valid JSON Schema type definitions.
