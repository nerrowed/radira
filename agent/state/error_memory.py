"""Error memory system for automatic learning from failures."""

import json
import logging
import traceback
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from collections import Counter, defaultdict

import chromadb
from chromadb.config import Settings as ChromaSettings

from config.settings import settings

logger = logging.getLogger(__name__)


class ErrorMemory:
    """Manage error logging, storage, and pattern analysis."""

    def __init__(self, storage_dir: Optional[str] = None):
        """Initialize error memory system.

        Args:
            storage_dir: Directory for error logs (default: workspace/.errors)
        """
        self.storage_dir = Path(storage_dir or settings.working_directory) / ".errors"
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        self.json_log_file = self.storage_dir / "error_logs.json"
        self.analysis_cache_file = self.storage_dir / "error_analysis_cache.json"

        # Initialize ChromaDB for semantic error search
        self.chroma_client = None
        self.error_collection = None
        self._init_chromadb()

        # Load existing logs
        self.errors = self._load_json_logs()

        logger.info(f"Error memory initialized at {self.storage_dir}")

    def _init_chromadb(self):
        """Initialize ChromaDB collection for error memory."""
        try:
            chroma_dir = self.storage_dir / "chromadb"
            chroma_dir.mkdir(parents=True, exist_ok=True)

            self.chroma_client = chromadb.PersistentClient(
                path=str(chroma_dir),
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )

            # Create or get error collection
            self.error_collection = self.chroma_client.get_or_create_collection(
                name="error_memory",
                metadata={"description": "Tool execution errors for learning"}
            )

            logger.info(f"Error memory ChromaDB initialized: {self.error_collection.count()} errors stored")

        except Exception as e:
            logger.warning(f"ChromaDB initialization failed, using file-only storage: {e}")
            self.chroma_client = None
            self.error_collection = None

    def _load_json_logs(self) -> List[Dict[str, Any]]:
        """Load errors from JSON log file.

        Returns:
            List of error records
        """
        if not self.json_log_file.exists():
            return []

        try:
            with open(self.json_log_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load error logs: {e}")
            return []

    def _save_json_logs(self):
        """Save errors to JSON log file."""
        try:
            with open(self.json_log_file, 'w', encoding='utf-8') as f:
                json.dump(self.errors, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save error logs: {e}")

    def log_error(
        self,
        tool_name: str,
        operation: str,
        error_message: str,
        **metadata
    ) -> str:
        """Log an error from tool execution.

        Args:
            tool_name: Name of the tool
            operation: Operation that failed
            error_message: Error description
            **metadata: Additional context (path, params, etc.)

        Returns:
            Error ID
        """
        timestamp = datetime.now().isoformat()
        error_id = f"err_{int(datetime.now().timestamp() * 1000)}"

        # Build error record
        error_record = {
            "id": error_id,
            "timestamp": timestamp,
            "tool_name": tool_name,
            "operation": operation,
            "error": error_message,
            "metadata": metadata
        }

        # Capture traceback if available
        try:
            tb = traceback.format_exc()
            if tb and "NoneType: None" not in tb:
                error_record["traceback"] = tb[:1000]  # Limit size
        except:
            pass

        # Generate auto-remediation suggestion
        remediation = self.get_remediation_suggestion(error_record)
        if remediation:
            error_record["remediation"] = remediation

        # Store in JSON
        self.errors.append(error_record)
        self._save_json_logs()

        # Store in ChromaDB for semantic search
        if self.error_collection:
            try:
                # Create searchable document
                doc = f"{tool_name} {operation}: {error_message}"
                if metadata:
                    doc += f" | Context: {' '.join(f'{k}={v}' for k, v in metadata.items())}"

                # ChromaDB metadata (only scalars)
                chroma_metadata = {
                    "tool_name": tool_name[:100],
                    "operation": operation[:100],
                    "error": error_message[:500],
                    "timestamp": timestamp
                }

                # Add scalar metadata
                for key, value in metadata.items():
                    if isinstance(value, (str, int, float, bool)):
                        chroma_metadata[key] = str(value)[:500] if isinstance(value, str) else value

                self.error_collection.add(
                    documents=[doc],
                    metadatas=[chroma_metadata],
                    ids=[error_id]
                )

            except Exception as e:
                logger.warning(f"Failed to store error in ChromaDB: {e}")

        logger.debug(f"Logged error {error_id}: {tool_name}.{operation}")
        return error_id

    def find_similar_errors(
        self,
        tool_name: str,
        operation: str,
        error_message: str,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """Find similar past errors using semantic search.

        Args:
            tool_name: Tool name
            operation: Operation
            error_message: Error message
            n_results: Number of results

        Returns:
            List of similar error records
        """
        if not self.error_collection or self.error_collection.count() == 0:
            return []

        try:
            query = f"{tool_name} {operation}: {error_message}"

            results = self.error_collection.query(
                query_texts=[query],
                n_results=min(n_results, self.error_collection.count())
            )

            if not results["documents"] or not results["documents"][0]:
                return []

            similar_errors = []
            for i, doc in enumerate(results["documents"][0]):
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                distance = results["distances"][0][i] if results.get("distances") else 0

                similar_errors.append({
                    "id": results["ids"][0][i],
                    "document": doc,
                    "metadata": metadata,
                    "similarity": 1 - distance  # Convert distance to similarity
                })

            return similar_errors

        except Exception as e:
            logger.error(f"Similar error search failed: {e}")
            return []

    def analyze_errors(
        self,
        tool_name: Optional[str] = None,
        time_window_days: Optional[int] = None
    ) -> Dict[str, Any]:
        """Analyze error patterns and generate insights.

        Args:
            tool_name: Filter by tool name (None = all tools)
            time_window_days: Only analyze errors from last N days

        Returns:
            Analysis report with patterns and recommendations
        """
        # Filter errors
        filtered_errors = self.errors

        if tool_name:
            filtered_errors = [e for e in filtered_errors if e.get("tool_name") == tool_name]

        if time_window_days:
            cutoff = datetime.now().timestamp() - (time_window_days * 86400)
            filtered_errors = [
                e for e in filtered_errors
                if datetime.fromisoformat(e["timestamp"]).timestamp() > cutoff
            ]

        if not filtered_errors:
            return {
                "total_errors": 0,
                "message": "No errors found matching criteria"
            }

        # Pattern analysis
        tool_counter = Counter(e["tool_name"] for e in filtered_errors)
        operation_counter = Counter(e["operation"] for e in filtered_errors)
        error_type_counter = Counter(e["error"][:100] for e in filtered_errors)  # First 100 chars

        # Path analysis (for filesystem errors)
        path_errors = defaultdict(list)
        extension_errors = Counter()

        for error in filtered_errors:
            if "path" in error.get("metadata", {}):
                path = error["metadata"]["path"]
                path_errors[path].append(error["error"])

                # Extract extension
                if "." in path:
                    ext = Path(path).suffix
                    if ext:
                        extension_errors[ext] += 1

        # Temporal analysis
        hourly_errors = Counter()
        for error in filtered_errors:
            hour = datetime.fromisoformat(error["timestamp"]).hour
            hourly_errors[hour] += 1

        # Identify top problematic areas
        top_paths = sorted(
            path_errors.items(),
            key=lambda x: len(x[1]),
            reverse=True
        )[:5]

        # Generate recommendations
        recommendations = self._generate_recommendations(
            tool_counter,
            operation_counter,
            error_type_counter,
            extension_errors,
            top_paths
        )

        # Build analysis report
        analysis = {
            "total_errors": len(filtered_errors),
            "time_range": {
                "oldest": filtered_errors[0]["timestamp"] if filtered_errors else None,
                "newest": filtered_errors[-1]["timestamp"] if filtered_errors else None
            },
            "by_tool": dict(tool_counter.most_common()),
            "by_operation": dict(operation_counter.most_common(10)),
            "top_error_types": dict(error_type_counter.most_common(10)),
            "by_extension": dict(extension_errors.most_common(10)) if extension_errors else {},
            "problematic_paths": [
                {"path": path, "error_count": len(errors), "errors": errors[:3]}
                for path, errors in top_paths
            ],
            "temporal_pattern": {
                "peak_hours": sorted(hourly_errors.items(), key=lambda x: x[1], reverse=True)[:5]
            },
            "recommendations": recommendations
        }

        # Cache analysis
        self._cache_analysis(analysis)

        return analysis

    def _generate_recommendations(
        self,
        tool_counter: Counter,
        operation_counter: Counter,
        error_type_counter: Counter,
        extension_errors: Counter,
        top_paths: List[Tuple[str, List[str]]]
    ) -> List[Dict[str, str]]:
        """Generate actionable recommendations based on error patterns.

        Returns:
            List of recommendations with severity and action
        """
        recommendations = []

        # High-frequency tool errors
        if tool_counter:
            most_problematic_tool = tool_counter.most_common(1)[0]
            if most_problematic_tool[1] > 10:
                recommendations.append({
                    "severity": "high",
                    "category": "tool_reliability",
                    "message": f"Tool '{most_problematic_tool[0]}' has {most_problematic_tool[1]} errors",
                    "action": f"Review {most_problematic_tool[0]} implementation and add better error handling"
                })

        # High-frequency operation errors
        if operation_counter:
            most_problematic_op = operation_counter.most_common(1)[0]
            if most_problematic_op[1] > 5:
                recommendations.append({
                    "severity": "medium",
                    "category": "operation_failure",
                    "message": f"Operation '{most_problematic_op[0]}' fails frequently ({most_problematic_op[1]} times)",
                    "action": f"Add validation before '{most_problematic_op[0]}' operations"
                })

        # Extension-specific errors
        if extension_errors:
            for ext, count in extension_errors.most_common(3):
                if count > 3:
                    recommendations.append({
                        "severity": "low",
                        "category": "file_type",
                        "message": f"Files with extension '{ext}' cause {count} errors",
                        "action": f"Add special handling for {ext} files or block them if unsupported"
                    })

        # Path-specific errors
        for path, errors in top_paths[:3]:
            if len(errors) > 3:
                recommendations.append({
                    "severity": "medium",
                    "category": "path_issue",
                    "message": f"Path '{path}' causes {len(errors)} errors",
                    "action": f"Investigate path '{path}' - possible permission or access issues"
                })

        # Common error patterns
        for error_msg, count in error_type_counter.most_common(3):
            if count > 5:
                # Pattern detection
                if "not exist" in error_msg.lower():
                    recommendations.append({
                        "severity": "medium",
                        "category": "validation",
                        "message": f"'{error_msg[:50]}...' occurs {count} times",
                        "action": "Add existence validation before operations"
                    })
                elif "permission" in error_msg.lower():
                    recommendations.append({
                        "severity": "high",
                        "category": "security",
                        "message": f"Permission errors occur {count} times",
                        "action": "Review file permissions and sandbox settings"
                    })
                elif "size" in error_msg.lower() or "large" in error_msg.lower():
                    recommendations.append({
                        "severity": "low",
                        "category": "limits",
                        "message": f"File size errors occur {count} times",
                        "action": "Adjust max_file_size setting or add pre-check"
                    })

        return recommendations

    def _cache_analysis(self, analysis: Dict[str, Any]):
        """Cache analysis results for quick access.

        Args:
            analysis: Analysis report
        """
        try:
            cache_data = {
                "timestamp": datetime.now().isoformat(),
                "analysis": analysis
            }
            with open(self.analysis_cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"Failed to cache analysis: {e}")

    def get_prevention_strategy(
        self,
        tool_name: str,
        operation: str,
        params: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Get prevention strategy based on past errors.

        Args:
            tool_name: Tool name
            operation: Operation to perform
            params: Operation parameters

        Returns:
            Prevention strategy or None
        """
        # Find similar past errors
        error_query = f"{tool_name} {operation}"
        similar = self.find_similar_errors(tool_name, operation, "", n_results=10)

        if not similar:
            return None

        # Extract common failure patterns
        warnings = []
        validations = []

        for error in similar:
            error_msg = error.get("metadata", {}).get("error", "")

            # Path-based warnings
            if "path" in params:
                error_path = error.get("metadata", {}).get("path", "")
                if error_path and error_path == params["path"]:
                    warnings.append(f"Path '{error_path}' has failed before: {error_msg[:100]}")

            # Operation validations
            if "not exist" in error_msg.lower():
                validations.append("check_exists_before_operation")
            if "permission" in error_msg.lower():
                validations.append("check_permissions")
            if "size" in error_msg.lower():
                validations.append("check_file_size")

        if not warnings and not validations:
            return None

        return {
            "warnings": warnings,
            "recommended_validations": list(set(validations)),
            "similar_error_count": len(similar),
            "confidence": min(len(similar) / 10.0, 1.0)  # 0-1 confidence score
        }

    def get_remediation_suggestion(self, error_record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate automatic fix suggestion based on error pattern.

        Args:
            error_record: Error record with tool_name, operation, error, metadata

        Returns:
            Remediation dict with suggestion, severity, and action_type
        """
        error_msg = error_record.get('error', '').lower()
        tool_name = error_record.get('tool_name', '')
        operation = error_record.get('operation', '')
        metadata = error_record.get('metadata', {})

        # Pattern-based remediation using comprehensive library
        remediation_patterns = self._get_remediation_patterns()

        for pattern in remediation_patterns:
            # Check if pattern matches
            if all(keyword in error_msg for keyword in pattern['keywords']):
                # Optional: Check tool/operation filter
                if pattern.get('tool') and pattern['tool'] != tool_name:
                    continue
                if pattern.get('operation') and pattern['operation'] != operation:
                    continue

                # Build suggestion with context
                suggestion = pattern['suggestion']

                # Inject context variables
                if '{path}' in suggestion and 'path' in metadata:
                    suggestion = suggestion.replace('{path}', str(metadata['path']))
                if '{extension}' in suggestion and 'extension' in metadata:
                    suggestion = suggestion.replace('{extension}', str(metadata['extension']))
                if '{max_size}' in suggestion and 'max_size' in metadata:
                    max_mb = metadata['max_size'] / (1024 * 1024)
                    suggestion = suggestion.replace('{max_size}', f'{max_mb:.0f}MB')
                if '{file_size}' in suggestion and 'file_size' in metadata:
                    file_mb = metadata['file_size'] / (1024 * 1024)
                    suggestion = suggestion.replace('{file_size}', f'{file_mb:.1f}MB')

                return {
                    'suggestion': suggestion,
                    'severity': pattern.get('severity', 'medium'),
                    'action_type': pattern.get('action_type', 'manual'),
                    'category': pattern.get('category', 'general'),
                    'auto_fixable': pattern.get('auto_fixable', False)
                }

        # Fallback: Generic suggestion based on tool
        return self._get_generic_remediation(tool_name, operation, error_msg)

    def _get_remediation_patterns(self) -> List[Dict[str, Any]]:
        """Comprehensive library of error patterns and remediations.

        Returns:
            List of pattern dictionaries
        """
        return [
            # File existence errors
            {
                'keywords': ['does not exist', 'not exist', 'no such file'],
                'suggestion': 'Create the missing file first, or verify the path is correct: {path}',
                'severity': 'medium',
                'action_type': 'create',
                'category': 'file_system',
                'auto_fixable': True
            },
            {
                'keywords': ['file not found', 'cannot find'],
                'suggestion': 'Check if the file path is correct. Use "list" operation to see available files.',
                'severity': 'medium',
                'action_type': 'validate',
                'category': 'file_system',
                'auto_fixable': False
            },

            # Permission errors
            {
                'keywords': ['permission', 'denied', 'access denied'],
                'suggestion': 'Check file permissions or disable sandbox mode if path is intentionally outside workspace',
                'severity': 'high',
                'action_type': 'permission',
                'category': 'security',
                'auto_fixable': False
            },
            {
                'keywords': ['blocked', 'safety'],
                'suggestion': 'Path {path} is in blocked_paths. Remove from BLOCKED_PATHS setting if access is needed.',
                'severity': 'high',
                'action_type': 'config',
                'category': 'security',
                'auto_fixable': False
            },

            # File size errors
            {
                'keywords': ['too large', 'file size', 'exceeds'],
                'tool': 'file_system',
                'suggestion': 'File is {file_size}, max is {max_size}. Either split file or increase MAX_FILE_SIZE_MB in settings',
                'severity': 'medium',
                'action_type': 'config',
                'category': 'limits',
                'auto_fixable': False
            },

            # Extension errors
            {
                'keywords': ['extension', 'not allowed', 'allowed extensions'],
                'tool': 'file_system',
                'suggestion': 'Extension {extension} not allowed. Add to ALLOWED_EXTENSIONS setting or convert to allowed format (.txt, .py, .json, etc.)',
                'severity': 'low',
                'action_type': 'config',
                'category': 'validation',
                'auto_fixable': False
            },

            # Directory errors
            {
                'keywords': ['not a directory', 'is not a directory'],
                'suggestion': 'The path points to a file, not a directory. Use parent directory path instead.',
                'severity': 'medium',
                'action_type': 'validate',
                'category': 'file_system',
                'auto_fixable': False
            },
            {
                'keywords': ['not a file', 'is a directory'],
                'suggestion': 'The path points to a directory, not a file. Specify a file path instead.',
                'severity': 'medium',
                'action_type': 'validate',
                'category': 'file_system',
                'auto_fixable': False
            },

            # Binary file errors
            {
                'keywords': ['binary', 'not text-readable', 'unicode', 'decode'],
                'suggestion': 'File is binary, not text. Use binary-compatible tools or convert to text format first.',
                'severity': 'low',
                'action_type': 'manual',
                'category': 'file_system',
                'auto_fixable': False
            },

            # Terminal errors
            {
                'keywords': ['command not found', 'not recognized'],
                'tool': 'terminal',
                'suggestion': 'Command not installed. Install it first or check if command name is correct.',
                'severity': 'medium',
                'action_type': 'install',
                'category': 'terminal',
                'auto_fixable': False
            },
            {
                'keywords': ['timeout', 'timed out'],
                'tool': 'terminal',
                'suggestion': 'Command took too long. Increase COMMAND_TIMEOUT_SECONDS or optimize the command.',
                'severity': 'medium',
                'action_type': 'config',
                'category': 'terminal',
                'auto_fixable': False
            },

            # Network/web errors
            {
                'keywords': ['connection', 'refused', 'network'],
                'suggestion': 'Network error. Check internet connection or if target server is accessible.',
                'severity': 'high',
                'action_type': 'manual',
                'category': 'network',
                'auto_fixable': False
            },
            {
                'keywords': ['404', 'not found'],
                'tool': 'web_search',
                'suggestion': 'Resource not found. Verify URL is correct or search for alternative sources.',
                'severity': 'medium',
                'action_type': 'validate',
                'category': 'network',
                'auto_fixable': False
            },

            # Sandbox errors
            {
                'keywords': ['outside workspace', 'sandbox'],
                'suggestion': 'Path is outside workspace. Set SANDBOX_MODE=false to allow (use with caution).',
                'severity': 'high',
                'action_type': 'config',
                'category': 'security',
                'auto_fixable': False
            },
        ]

    def _get_generic_remediation(
        self,
        tool_name: str,
        operation: str,
        error_msg: str
    ) -> Optional[Dict[str, Any]]:
        """Fallback generic remediation when no pattern matches.

        Args:
            tool_name: Tool name
            operation: Operation
            error_msg: Error message

        Returns:
            Generic remediation or None
        """
        # Tool-specific generic advice
        generic_advice = {
            'file_system': {
                'read': 'Verify file exists and is readable before attempting to read',
                'write': 'Ensure directory exists and you have write permissions',
                'delete': 'Check if file/directory exists before attempting deletion',
                'list': 'Verify the path is a valid directory',
                'search': 'Check directory exists and search pattern is valid'
            },
            'terminal': {
                'default': 'Verify command syntax and that required tools are installed'
            },
            'web_search': {
                'default': 'Check internet connection and search query format'
            },
            'pentest': {
                'default': 'Verify target is accessible and tool is installed correctly'
            }
        }

        tool_advice = generic_advice.get(tool_name, {})
        suggestion = tool_advice.get(operation) or tool_advice.get('default')

        if suggestion:
            return {
                'suggestion': suggestion,
                'severity': 'low',
                'action_type': 'validate',
                'category': 'general',
                'auto_fixable': False
            }

        return None

    def get_summary(self) -> str:
        """Get human-readable summary of error memory.

        Returns:
            Summary string
        """
        total = len(self.errors)
        if total == 0:
            return "No errors logged yet."

        recent = [e for e in self.errors if
                  datetime.now().timestamp() - datetime.fromisoformat(e["timestamp"]).timestamp() < 86400]

        tool_counter = Counter(e["tool_name"] for e in self.errors)
        most_common = tool_counter.most_common(1)[0] if tool_counter else ("N/A", 0)

        summary = f"""Error Memory Summary:
• Total errors logged: {total}
• Errors in last 24h: {len(recent)}
• Most problematic tool: {most_common[0]} ({most_common[1]} errors)
• ChromaDB status: {'✓ Active' if self.error_collection else '✗ Disabled'}
• Storage: {self.storage_dir}
"""
        return summary
