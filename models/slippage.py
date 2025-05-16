"""
Slippage estimation models for the Crypto Trade Simulator
"""
import numpy as np
import logging
from typing import List, Dict, Tuple, Optional
from data.market_data import OrderBook
from utils.performance import measure_latency

class SlippageModel:
    """
    Predicts slippage for market orders based on orderbook data
    Implements both linear and quantile regression approaches
    """
    
    def __init__(self, history_size: int = 100):
        """
        Initialize slippage model
        
        Args:
            history_size: Number of historical data points to maintain
        """
        self.logger = logging.getLogger(__name__)
        self.history_size = history_size
        self.price_impact_history = []  # List of (order_size, price_impact) tuples
        self.features_history = []  # List of feature vectors for regression
        self.slippage_history = []  # List of observed slippage values
        
    def _calculate_theoretical_price_impact(self, orderbook: OrderBook, quantity: float, is_buy: bool) -> float:
        """
        Calculate theoretical price impact based on orderbook liquidity
        
        Args:
            orderbook: Current orderbook state
            quantity: Order quantity in base currency
            is_buy: True for buy orders, False for sell orders
            
        Returns:
            float: Estimated price impact in percentage
        """
        if quantity <= 0:
            return 0.0
            
        remaining_quantity = quantity
        weighted_avg_price = 0.0
        base_price = orderbook.best_ask() if is_buy else orderbook.best_bid()
        
        # Use appropriate side of the orderbook
        levels = orderbook.asks if is_buy else orderbook.bids
        
        # Walk the orderbook to calculate weighted average execution price
        for level in levels:
            if remaining_quantity <= 0:
                break
                
            # How much can we execute at this level
            executable_quantity = min(remaining_quantity, level.quantity)
            weighted_avg_price += executable_quantity * level.price
            remaining_quantity -= executable_quantity
            
        # If we couldn't fill the entire order with visible liquidity
        if remaining_quantity > 0:
            # Assume some worst-case slippage for the remainder
            last_price = levels[-1].price if levels else base_price
            worst_case_slippage = 0.005  # 0.5% additional slippage beyond the book
            estimated_price = last_price * (1 + worst_case_slippage if is_buy else 1 - worst_case_slippage)
            weighted_avg_price += remaining_quantity * estimated_price
            
        # Calculate average execution price
        avg_price = weighted_avg_price / quantity
        
        # Calculate price impact as percentage
        price_impact = ((avg_price / base_price) - 1.0) * 100 if is_buy else (1.0 - (avg_price / base_price)) * 100
        
        return price_impact
    
    def _extract_features(self, orderbook: OrderBook, quantity: float) -> np.ndarray:
        """
        Extract features for regression model
        
        Args:
            orderbook: Current orderbook state
            quantity: Order quantity in base currency
            
        Returns:
            np.ndarray: Feature vector
        """
        # Basic features that affect slippage
        spread_bps = (orderbook.spread() / orderbook.mid_price()) * 10000  # Spread in basis points
        
        # Calculate depth metrics
        bid_depth = sum(level.quantity for level in orderbook.bids)
        ask_depth = sum(level.quantity for level in orderbook.asks)
        
        # Depth imbalance (positive means more bids than asks)
        depth_imbalance = (bid_depth - ask_depth) / (bid_depth + ask_depth) if (bid_depth + ask_depth) > 0 else 0
        
        # Order size relative to available liquidity
        relative_size_bids = quantity / bid_depth if bid_depth > 0 else 1.0
        relative_size_asks = quantity / ask_depth if ask_depth > 0 else 1.0
        
        # Create feature vector
        features = np.array([
            spread_bps,
            depth_imbalance,
            relative_size_bids,
            relative_size_asks,
            quantity
        ])
        
        return features
    
    def update(self, orderbook: OrderBook, quantity: float, observed_slippage: Optional[float] = None) -> None:
        """
        Update model with new data
        
        Args:
            orderbook: Current orderbook state
            quantity: Order quantity in base currency
            observed_slippage: Actual observed slippage if available
        """
        # Calculate theoretical price impact for both sides
        buy_impact = self._calculate_theoretical_price_impact(orderbook, quantity, True)
        sell_impact = self._calculate_theoretical_price_impact(orderbook, quantity, False)
        
        # Extract features for regression model
        features = self._extract_features(orderbook, quantity)
        
        # Store historical data
        self.price_impact_history.append((quantity, buy_impact, sell_impact))
        self.features_history.append(features)
        
        if observed_slippage is not None:
            self.slippage_history.append(observed_slippage)
        
        # Keep history size in check
        if len(self.price_impact_history) > self.history_size:
            self.price_impact_history.pop(0)
            
        if len(self.features_history) > self.history_size:
            self.features_history.pop(0)
            
        if len(self.slippage_history) > self.history_size:
            self.slippage_history.pop(0)
    
    @measure_latency("slippage_prediction_linear")
    def predict_slippage_linear(self, orderbook: OrderBook, quantity: float, is_buy: bool = True) -> float:
        """
        Predict slippage using linear regression based on orderbook features
        
        Args:
            orderbook: Current orderbook state
            quantity: Order quantity in base currency
            is_buy: True for buy orders, False for sell orders
            
        Returns:
            float: Predicted slippage in percentage
        """
        # If we don't have enough historical data, use theoretical model
        if len(self.price_impact_history) < 10:
            return self._calculate_theoretical_price_impact(orderbook, quantity, is_buy)
        
        # Extract features for current orderbook
        features = self._extract_features(orderbook, quantity)
        
        # Simple linear model: use coefficients based on historical correlations
        # This is a simplified approach - in a real system, you'd use proper linear regression
        weights = np.array([0.2, 0.3, 0.4, 0.3, 0.1])  # Example weights
        
        # Normalize features using history
        if self.features_history:
            hist_features = np.array(self.features_history)
            feature_means = np.mean(hist_features, axis=0)
            feature_stds = np.std(hist_features, axis=0)
            feature_stds[feature_stds == 0] = 1.0  # Avoid division by zero
            
            normalized_features = (features - feature_means) / feature_stds
        else:
            normalized_features = features
        
        # Predict slippage using simple linear combination
        base_slippage = np.dot(weights, normalized_features)
        
        # Theoretical price impact for reference
        theoretical_impact = self._calculate_theoretical_price_impact(orderbook, quantity, is_buy)
        
        # Combine model prediction with theoretical impact
        alpha = 0.7  # Weight between model and theoretical
        predicted_slippage = alpha * base_slippage + (1 - alpha) * theoretical_impact
        
        # Ensure prediction is positive
        return max(0.0, predicted_slippage)
    
    @measure_latency("slippage_prediction_quantile")
    def predict_slippage_quantile(self, orderbook: OrderBook, quantity: float, is_buy: bool = True, 
                                 quantile: float = 0.95) -> float:
        """
        Predict slippage using quantile regression (more conservative estimates)
        
        Args:
            orderbook: Current orderbook state
            quantity: Order quantity in base currency
            is_buy: True for buy orders, False for sell orders
            quantile: Quantile level (0.5 = median, 0.95 = 95th percentile)
            
        Returns:
            float: Predicted slippage at the specified quantile
        """
        # Get linear prediction as baseline
        base_prediction = self.predict_slippage_linear(orderbook, quantity, is_buy)
        
        # If we don't have enough history, scale the prediction with a safety factor
        if len(self.price_impact_history) < 20:
            if quantile > 0.5:
                # Scale up for higher quantiles
                safety_factor = 1.0 + (quantile - 0.5) * 2.0  # e.g., 1.9x for 95th percentile
                return base_prediction * safety_factor
            else:
                return base_prediction
        
        # Calculate quantile from historical data
        # Here we're approximating quantile regression with a scaling factor
        
        # Get historical price impacts for appropriate side
        historical_impacts = [impact[1] if is_buy else impact[2] for impact in self.price_impact_history]
        
        if not historical_impacts:
            return base_prediction
            
        # Calculate mean and standard deviation
        mean_impact = np.mean(historical_impacts)
        std_impact = np.std(historical_impacts)
        
        # Approximate quantile assuming normal distribution
        # This is a simplification - real quantile regression would be more complex
        z_score = {
            0.5: 0,
            0.75: 0.674,
            0.9: 1.282,
            0.95: 1.645,
            0.99: 2.326
        }.get(quantile, 0)
        
        if z_score == 0 and quantile != 0.5:
            # Interpolate for values not in the table
            # Find closest keys
            keys = sorted(list({0.5: 0, 0.75: 0.674, 0.9: 1.282, 0.95: 1.645, 0.99: 2.326}.keys()))
            
            # Find the keys that surround the target quantile
            idx = 0
            while idx < len(keys) and keys[idx] < quantile:
                idx += 1
                
            if idx == 0:
                z_score = 0
            elif idx == len(keys):
                z_score = 2.326
            else:
                # Linear interpolation
                lower_key = keys[idx - 1]
                upper_key = keys[idx]
                lower_z = {0.5: 0, 0.75: 0.674, 0.9: 1.282, 0.95: 1.645, 0.99: 2.326}[lower_key]
                upper_z = {0.5: 0, 0.75: 0.674, 0.9: 1.282, 0.95: 1.645, 0.99: 2.326}[upper_key]
                z_score = lower_z + (upper_z - lower_z) * (quantile - lower_key) / (upper_key - lower_key)
        
        # Calculate quantile estimate
        quantile_estimate = mean_impact + z_score * std_impact
        
        # Combine with base prediction
        alpha = 0.6  # Weight between historical quantile and current prediction
        predicted_slippage = alpha * quantile_estimate + (1 - alpha) * base_prediction
        
        # Ensure prediction is positive
        return max(0.0, predicted_slippage)