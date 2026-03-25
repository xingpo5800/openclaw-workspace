"""Memory profiling utilities for debugging memory issues."""

import logging
import tracemalloc
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class MemoryProfiler:
    """Memory profiler for tracking allocations and detecting leaks.
    
    Uses Python's tracemalloc module to track memory allocations
    and provide detailed profiling information.
    """
    
    def __init__(self):
        """Initialize the memory profiler."""
        self._started = False
        self._snapshots: List[tracemalloc.Snapshot] = []
    
    def start(self) -> None:
        """Start memory profiling.
        
        This must be called before any memory tracking can occur.
        """
        if not self._started:
            tracemalloc.start()
            self._started = True
            logger.info("Memory profiling started")
    
    def stop(self) -> None:
        """Stop memory profiling."""
        if self._started:
            tracemalloc.stop()
            self._started = False
            logger.info("Memory profiling stopped")
    
    def take_snapshot(self) -> tracemalloc.Snapshot:
        """Take a memory snapshot.
        
        Returns:
            Memory snapshot
            
        Raises:
            RuntimeError: If profiling is not started
        """
        if not self._started:
            raise RuntimeError("Memory profiling not started. Call start() first.")
        
        snapshot = tracemalloc.take_snapshot()
        self._snapshots.append(snapshot)
        logger.debug(f"Took memory snapshot #{len(self._snapshots)}")
        return snapshot
    
    def get_current_memory(self) -> Tuple[int, int]:
        """Get current memory usage.
        
        Returns:
            Tuple of (current_bytes, peak_bytes)
            
        Raises:
            RuntimeError: If profiling is not started
        """
        if not self._started:
            raise RuntimeError("Memory profiling not started. Call start() first.")
        
        current, peak = tracemalloc.get_traced_memory()
        return current, peak
    
    def get_top_allocations(self, limit: int = 10) -> List[Dict[str, any]]:
        """Get top memory allocations.
        
        Args:
            limit: Number of top allocations to return (default 10)
            
        Returns:
            List of allocation info dictionaries
            
        Raises:
            RuntimeError: If profiling is not started or no snapshots taken
        """
        if not self._started:
            raise RuntimeError("Memory profiling not started. Call start() first.")
        
        if not self._snapshots:
            raise RuntimeError("No snapshots taken. Call take_snapshot() first.")
        
        snapshot = self._snapshots[-1]
        top_stats = snapshot.statistics('lineno')
        
        allocations = []
        for stat in top_stats[:limit]:
            allocations.append({
                "filename": stat.traceback.format()[0] if stat.traceback else "unknown",
                "size_bytes": stat.size,
                "size_mb": stat.size / (1024 * 1024),
                "count": stat.count,
            })
        
        return allocations
    
    def compare_snapshots(self, index1: int = -2, index2: int = -1) -> List[Dict[str, any]]:
        """Compare two snapshots to detect memory growth.
        
        Args:
            index1: Index of first snapshot (default -2 = second to last)
            index2: Index of second snapshot (default -1 = last)
            
        Returns:
            List of differences showing memory growth
            
        Raises:
            RuntimeError: If not enough snapshots available
        """
        if len(self._snapshots) < 2:
            raise RuntimeError("Need at least 2 snapshots to compare")
        
        snapshot1 = self._snapshots[index1]
        snapshot2 = self._snapshots[index2]
        
        top_stats = snapshot2.compare_to(snapshot1, 'lineno')
        
        differences = []
        for stat in top_stats[:10]:
            differences.append({
                "filename": stat.traceback.format()[0] if stat.traceback else "unknown",
                "size_diff_bytes": stat.size_diff,
                "size_diff_mb": stat.size_diff / (1024 * 1024),
                "count_diff": stat.count_diff,
            })
        
        return differences
    
    def get_summary(self) -> Dict[str, any]:
        """Get memory profiling summary.
        
        Returns:
            Summary dictionary with current state and statistics
        """
        if not self._started:
            return {
                "started": False,
                "message": "Memory profiling not started"
            }
        
        current, peak = self.get_current_memory()
        
        summary = {
            "started": True,
            "current_bytes": current,
            "current_mb": current / (1024 * 1024),
            "peak_bytes": peak,
            "peak_mb": peak / (1024 * 1024),
            "snapshots_count": len(self._snapshots),
        }
        
        if self._snapshots:
            summary["last_snapshot_time"] = "recent"
        
        return summary
    
    def clear_snapshots(self) -> None:
        """Clear all stored snapshots to free memory."""
        self._snapshots.clear()
        logger.debug("Cleared all memory snapshots")
