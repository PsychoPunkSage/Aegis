"""
Advanced volatility calculations for market data
"""
import numpy as np
import math
import logging
from typing import List, Tuple, Optional, Dict
from datetime import datetime, timedelta
from collections import deque
from utils.performance import measure_latency

class VolatilityCalculator:
    """
    Advanced volatility calculator using multiple methods
    """
    
    def __init__(self, window_sizes: List[int] = [10, 30, 60, 120]):
        """
        Initialize volatility calculator
        
        Args:
            window_sizes: List of window sizes for volatility calculation
        """
        self.logger = logging.getLogger(__name__)
        self.window_sizes = window_sizes # in mins
        
        # Price history as (timestamp, price) tuples
        self.price_history = deque(maxlen=max(window_sizes) + 10) # Max length - slightly longer than the largest window.
        
        # Return history for different window sizes
        self.returns = {size: deque(maxlen=100) for size in window_sizes}
        
        # Volatility estimates
        self.volatility_estimates = {size: 0.0 for size in window_sizes}
        
        # EWMA (Exponentially Weighted Moving Average) parameters
        self.ewma_lambda = 0.94  # Decay factor (slow decay)
        self.ewma_variance = 0.0
        
    def add_price(self, timestamp: datetime, price: float) -> None:
        """
        Add a new price observation
        
        Args:
            timestamp: Observation timestamp
            price: Price value
        """
        # Add to price history
        self.price_history.append((timestamp, price))
        
        # Calculate returns for each window size
        self._calculate_returns()
        
        # Update volatility estimates
        self._update_volatility_estimates()
        
    def _calculate_returns(self) -> None:
        """Calculate log returns for each window size"""
        if len(self.price_history) < 2:
            return
            
        # Get current price
        current_time, current_price = self.price_history[-1]
        
        # Calculate returns for each window size
        for window_size in self.window_sizes:
            if len(self.price_history) >= window_size + 1:
                # Get price at window_size intervals ago
                past_time, past_price = self.price_history[-window_size - 1]
                
                # Calculate log return
                if past_price > 0 and current_price > 0:
                    log_return = math.log(current_price / past_price)
                    self.returns[window_size].append(log_return)
                    
                    # Update EWMA variance if this is the shortest window
                    if window_size == min(self.window_sizes):
                        if self.ewma_variance == 0.0:
                            # Initialize with sample variance if first observation
                            if len(self.returns[window_size]) > 1:
                                self.ewma_variance = np.var(list(self.returns[window_size]))
                        else:
                            # Update EWMA variance
                            self.ewma_variance = (
                                self.ewma_lambda * self.ewma_variance + 
                                (1 - self.ewma_lambda) * log_return**2
                            )
    
    def _update_volatility_estimates(self) -> None:
        """Update volatility estimates for each window size"""
        for window_size in self.window_sizes:
            if len(self.returns[window_size]) > 1:
                # Calculate standard deviation of returns
                returns_array = np.array(list(self.returns[window_size]))
                std_dev = np.std(returns_array, ddof=1)  # Use n-1 for sample std dev
                
                # Annualize volatility (assuming data frequency and converting to percentage)
                # For example, if window_size represents 1-minute intervals:
                trading_days_per_year = 365
                minutes_per_day = 24 * 60
                annualization_factor = math.sqrt(trading_days_per_year * minutes_per_day / window_size)
                annualized_vol = std_dev * annualization_factor * 100  # Convert to percentage
                
                self.volatility_estimates[window_size] = annualized_vol
    
    @measure_latency("volatility_calculation")
    def get_volatility(self, method: str = "ewma") -> Dict[str, float]:
        """
        Get current volatility estimate
        
        Args:
            method: Volatility calculation method (std, ewma, garch)
            
        Returns:
            Dict[str, float]: Volatility estimates
        """
        results = {}
        
        # Standard volatility (based on rolling windows)
        if method == "std" or method == "all":
            for window_size in self.window_sizes:
                results[f"std_{window_size}"] = self.volatility_estimates[window_size]
        
        # EWMA volatility
        if method == "ewma" or method == "all":
            # Convert EWMA variance to annualized volatility
            trading_days_per_year = 365
            minutes_per_day = 24 * 60
            shortest_window = min(self.window_sizes)
            annualization_factor = math.sqrt(trading_days_per_year * minutes_per_day / shortest_window)
            
            ewma_vol = math.sqrt(self.ewma_variance) * annualization_factor * 100
            results["ewma"] = ewma_vol
            
            # Also include a 'current' estimate that's our best single number
            results["current"] = ewma_vol
        
        # Add blended estimate (average of available methods)
        if len(results) > 0:
            results["blended"] = sum(results.values()) / len(results)
            
        return results
    
    def get_current_volatility(self) -> float:
        """
        Get a single current volatility estimate (best available)
        
        Returns:
            float: Current volatility estimate as percentage
        """
        volatility = self.get_volatility(method="ewma")
        return volatility.get("current", 2.0)  # Default to 2% if no estimate available