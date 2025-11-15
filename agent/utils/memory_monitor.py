"""Memory monitoring and resource management utilities.

Provides tools for tracking memory usage and preventing memory leaks in long-running sessions.
"""

import logging
import psutil
from typing import Dict, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class MemoryStats:
    """Memory usage statistics."""

    process_memory_mb: float
    system_memory_percent: float
    available_memory_mb: float
    timestamp: datetime

    def __str__(self) -> str:
        return (
            f"Process: {self.process_memory_mb:.1f}MB | "
            f"System: {self.system_memory_percent:.1f}% | "
            f"Available: {self.available_memory_mb:.1f}MB"
        )


class MemoryMonitor:
    """Monitor memory usage and detect potential leaks."""

    def __init__(self, warning_threshold_mb: float = 500.0):
        """Initialize memory monitor.

        Args:
            warning_threshold_mb: Warn if process memory exceeds this threshold
        """
        self.warning_threshold_mb = warning_threshold_mb
        self.process = psutil.Process()
        self.baseline: Optional[MemoryStats] = None
        self.history: list[MemoryStats] = []
        self.max_history = 100

    def get_current_stats(self) -> MemoryStats:
        """Get current memory statistics.

        Returns:
            MemoryStats object with current memory usage
        """
        mem_info = self.process.memory_info()
        process_mb = mem_info.rss / (1024 * 1024)  # Convert to MB

        system_mem = psutil.virtual_memory()
        available_mb = system_mem.available / (1024 * 1024)

        stats = MemoryStats(
            process_memory_mb=process_mb,
            system_memory_percent=system_mem.percent,
            available_memory_mb=available_mb,
            timestamp=datetime.now()
        )

        # Add to history
        self.history.append(stats)
        if len(self.history) > self.max_history:
            self.history.pop(0)

        # Set baseline if not set
        if self.baseline is None:
            self.baseline = stats

        return stats

    def check_memory_health(self) -> Dict[str, any]:
        """Check memory health and detect potential issues.

        Returns:
            Dict with status and recommendations
        """
        stats = self.get_current_stats()

        issues = []
        recommendations = []

        # Check if process memory exceeds threshold
        if stats.process_memory_mb > self.warning_threshold_mb:
            issues.append(f"Process memory ({stats.process_memory_mb:.1f}MB) exceeds threshold ({self.warning_threshold_mb}MB)")
            recommendations.append("Consider clearing conversation history or restarting session")

        # Check memory growth
        if self.baseline and len(self.history) > 10:
            growth = stats.process_memory_mb - self.baseline.process_memory_mb
            if growth > 200:  # 200MB growth
                issues.append(f"Memory grew by {growth:.1f}MB since baseline")
                recommendations.append("Potential memory leak detected - review session cleanup")

        # Check system memory
        if stats.system_memory_percent > 90:
            issues.append(f"System memory usage critical ({stats.system_memory_percent:.1f}%)")
            recommendations.append("System memory low - consider closing other applications")

        return {
            "healthy": len(issues) == 0,
            "stats": stats,
            "issues": issues,
            "recommendations": recommendations
        }

    def log_memory_status(self, verbose: bool = False) -> None:
        """Log current memory status.

        Args:
            verbose: Include detailed information
        """
        health = self.check_memory_health()
        stats = health["stats"]

        if health["healthy"]:
            if verbose:
                logger.info(f"Memory healthy: {stats}")
        else:
            logger.warning(f"Memory issues detected: {stats}")
            for issue in health["issues"]:
                logger.warning(f"  - {issue}")
            for rec in health["recommendations"]:
                logger.info(f"  ⚡ {rec}")

    def reset_baseline(self) -> None:
        """Reset memory baseline to current usage."""
        self.baseline = self.get_current_stats()
        logger.info(f"Memory baseline reset: {self.baseline}")

    def get_memory_trend(self) -> str:
        """Analyze memory trend from history.

        Returns:
            Trend description (growing/stable/decreasing)
        """
        if len(self.history) < 5:
            return "insufficient_data"

        recent = self.history[-5:]
        oldest = recent[0].process_memory_mb
        newest = recent[-1].process_memory_mb

        diff = newest - oldest

        if diff > 50:  # Growing by >50MB
            return "growing"
        elif diff < -50:  # Decreasing by >50MB
            return "decreasing"
        else:
            return "stable"


# Global singleton
_monitor: Optional[MemoryMonitor] = None


def get_memory_monitor() -> MemoryMonitor:
    """Get or create global memory monitor.

    Returns:
        MemoryMonitor instance
    """
    global _monitor
    if _monitor is None:
        _monitor = MemoryMonitor()
    return _monitor
