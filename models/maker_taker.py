"""
Maker/Taker proportion estimator
"""
import numpy as np
import math
import logging
from typing import Dict, Any, List, Tuple, Optional
from data.market_data import OrderBook, MarketMetrics
from utils.performance import measure_latency

class MakerTakerEstimator:
    """
    Estimates the proportion of an order likely to be executed as maker vs taker
    """
    
    def __init__(self):
        """Initialize maker/taker estimator"""
        self.logger = logging.getLogger(__name__)
        
        # Model parameters
        self.params = {
            "base_maker_proportion": 0.7,  # Base maker proportion for limit orders
            "volatility_sensitivity": 0.5,  # How much volatility reduces maker proportion
            "spread_sensitivity": 0.3,     # How much spread increases maker proportion
            "depth_imbalance_sensitivity": 0.2,  # How much depth imbalance affects maker proportion
        }
        
        # History of estimates and features
        self.history = []
        
    def set_parameters(self, param_dict: Dict[str, float]) -> None:
        """
        Set model parameters
        
        Args:
            param_dict: Dictionary of parameter values
        """
        for key, value in param_dict.items():
            if key in self.params:
                self.params[key] = value
            else:
                self.logger.warning(f"Unknown parameter: {key}")
    
    def _extract_features(self, orderbook: OrderBook, metrics: MarketMetrics) -> Dict[str, float]:
        """
        Extract features for maker/taker estimation
        
        Args:
            orderbook: Current orderbook
            metrics: Market metrics
            
        Returns:
            Dict[str, float]: Extracted features
        """
        # Calculate mid price
        mid_price = orderbook.mid_price()
        
        # Calculate spread as percentage of price
        spread_pct = (orderbook.spread() / mid_price) if mid_price > 0 else 0.0
        
        # Normalize spread to a factor between 0 and 1
        # Assuming typical spread is around 5-10 bps (0.05-0.1%)
        spread_factor = min(1.0, spread_pct * 1000)  # Cap at 1.0
        
        # Normalize volatility to a factor between 0 and 1
        # Assuming typical volatility is around 1-5%
        volatility = metrics.volatility / 100.0  # Convert from percentage to decimal
        vol_factor = min(1.0, volatility / 0.05)  # Cap at 1.0
        
        # Calculate depth imbalance (positive means more bids than asks)
        bid_depth = metrics.bid_depth
        ask_depth = metrics.ask_depth
        
        depth_imbalance = 0.0
        if (bid_depth + ask_depth) > 0:
            depth_imbalance = (bid_depth - ask_depth) / (bid_depth + ask_depth)
            
        # Normalize depth imbalance to a factor between -1 and 1
        imbalance_factor = max(-1.0, min(1.0, depth_imbalance))
        
        return {
            "mid_price": mid_price,
            "spread_pct": spread_pct,
            "spread_factor": spread_factor,
            "volatility": volatility,
            "vol_factor": vol_factor,
            "depth_imbalance": depth_imbalance,
            "imbalance_factor": imbalance_factor
        }
    
    @measure_latency("maker_taker_estimation")
    def estimate_proportion(self, orderbook: OrderBook, metrics: MarketMetrics, 
                           is_buy: bool, is_limit: bool) -> Dict[str, float]:
        """
        Estimate maker/taker proportion
        
        Args:
            orderbook: Current orderbook
            metrics: Market metrics
            is_buy: True for buy orders, False for sell orders
            is_limit: True for limit orders, False for market orders
            
        Returns:
            Dict[str, float]: Maker/taker proportion and features
        """
        # For market orders, it's all taker
        if not is_limit:
            return {
                "maker_proportion": 0.0,
                "taker_proportion": 1.0,
                "features": {}
            }
            
        # Extract features
        features = self._extract_features(orderbook, metrics)
        
        # Calculate base maker proportion
        maker_proportion = self.params["base_maker_proportion"]
        
        # Adjust for volatility (higher volatility decreases maker proportion)
        maker_proportion *= (1 - self.params["volatility_sensitivity"] * features["vol_factor"])
        
        # Adjust for spread (wider spread increases maker proportion)
        maker_proportion *= (1 + self.params["spread_sensitivity"] * features["spread_factor"])
        
        # Adjust for depth imbalance
        # For buy orders: positive imbalance (more bids) decreases maker proportion
        # For sell orders: positive imbalance (more bids) increases maker proportion
        imbalance_effect = (
            -1 * features["imbalance_factor"] if is_buy else features["imbalance_factor"]
        )
        
        maker_proportion *= (1 + self.params["depth_imbalance_sensitivity"] * imbalance_effect)
        
        # Ensure maker proportion is between 0 and 1
        maker_proportion = max(0.0, min(1.0, maker_proportion))
        
        # Save to history
        self.history.append({
            "timestamp": orderbook.timestamp,
            "is_buy": is_buy,
            "is_limit": is_limit,
            "maker_proportion": maker_proportion,
            "features": features
        })
        
        # Keep history size in check
        if len(self.history) > 100:
            self.history.pop(0)
            
        return {
            "maker_proportion": maker_proportion,
            "taker_proportion": 1.0 - maker_proportion,
            "features": features
        }
        
    def update_with_actual_proportion(self, estimated_proportion: float, 
                                     actual_proportion: float) -> None:
        """
        Update model with observed proportion for accuracy tracking
        
        Args:
            estimated_proportion: Previously estimated maker proportion
            actual_proportion: Observed actual maker proportion
        """
        # This method would be used to fine-tune the model based on actual execution data
        # In a production system, this would involve a proper learning algorithm
        
        # For now, just log the comparison
        self.logger.info(
            f"Maker proportion accuracy: "
            f"estimated={estimated_proportion:.2f}, "
            f"actual={actual_proportion:.2f}, "
            f"error={(actual_proportion - estimated_proportion):.2f}"
        )