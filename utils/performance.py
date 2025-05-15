"""
Performance measurement utilities
"""
import time
import logging
from functools import wraps
from typing import Callable, Dict, Any

class LatencyTracker:
    """
    Tracks operation latency for performance monitoring
    """
    
    def __init__(self):
        self.measurements: Dict[str, list] = {}
        self.logger = logging.getLogger(__name__)
    
    def measure(self, operation: str, duration_ms: float) -> None:
        """
        Record a latency measurement
        
        Args:
            operation: Name of the operation being measured
            duration_ms: Duration in milliseconds
        """
        if operation not in self.measurements:
            self.measurements[operation] = []
        
        self.measurements[operation].append(duration_ms)
        
        # Keep only the most recent 1000 measurements
        if len(self.measurements[operation]) > 1000:
            self.measurements[operation].pop(0)
    
    def get_average(self, operation: str) -> float:
        """
        Get average latency for an operation
        
        Args:
            operation: Name of the operation
            
        Returns:
            float: Average latency in milliseconds, or 0 if no measurements
        """
        if not self.measurements.get(operation):
            return 0.0
        
        return sum(self.measurements[operation]) / len(self.measurements[operation])
    
    def get_percentile(self, operation: str, percentile: float) -> float:
        """
        Get a specific percentile of latency measurements
        
        Args:
            operation: Name of the operation
            percentile: Percentile to calculate (0-100)
            
        Returns:
            float: Percentile latency value in milliseconds, or 0 if no measurements
        """
        if not self.measurements.get(operation):
            return 0.0
        
        sorted_measurements = sorted(self.measurements[operation])
        index = int(len(sorted_measurements) * (percentile / 100))
        return sorted_measurements[index]
    
    def report(self) -> None:
        """
        Log a performance report
        """
        for operation, measurements in self.measurements.items():
            if not measurements:
                continue
                
            avg = self.get_average(operation)
            p50 = self.get_percentile(operation, 50)
            p95 = self.get_percentile(operation, 95)
            p99 = self.get_percentile(operation, 99)
            
            self.logger.info(
                f"Latency for {operation}: "
                f"avg={avg:.2f}ms, p50={p50:.2f}ms, p95={p95:.2f}ms, p99={p99:.2f}ms"
            )

# Global latency tracker instance
latency_tracker = LatencyTracker()

def measure_latency(operation_name: str) -> Callable:
    """
    Decorator to measure function execution time
    
    Args:
        operation_name: Name of the operation to record
        
    Returns:
        Callable: Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            
            # Calculate duration in milliseconds
            duration_ms = (end_time - start_time) * 1000
            
            # Record measurement
            latency_tracker.measure(operation_name, duration_ms)
            
            return result
        return wrapper
    return decorator