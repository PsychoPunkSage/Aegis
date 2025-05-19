"""
Enhanced market impact models
"""
import math
import logging
from enum import Enum
from typing import Dict, Any
from data.market_data import OrderBook, MarketMetrics
from utils.performance import measure_latency

class ImpactModelType(Enum):
    """Market impact model types"""
    ALMGREN_CHRISS = "almgren-chriss"
    SQUARE_ROOT = "square-root"
    LINEAR = "linear"
    CUSTOM = "custom"

class MarketImpactModel:
    """
    Enhanced market impact model with multiple implementations
    """
    
    def __init__(self, model_type: ImpactModelType = ImpactModelType.ALMGREN_CHRISS):
        """
        Initialize market impact model
        
        Args:
            model_type: Type of impact model to use
        """
        self.logger = logging.getLogger(__name__)
        self.model_type = model_type
        
        # Model parameters - can be calibrated
        self.params = {
            # Almgren-Chriss parameters
            "ac_temporary_impact": 0.1,
            "ac_permanent_impact": 0.02,
            "ac_volatility_scaling": 0.5,
            
            # Square-root model parameters
            "sqrt_impact_factor": 0.1,
            
            # Linear model parameters
            "linear_impact_factor": 0.01,
            
            # Common parameters
            "spread_cost_factor": 0.5,  # Half of spread as baseline cost
            "min_impact": 0.0001,  # Minimum impact in percentage
        }
        
        # Market parameter estimates (updated with each calculation)
        self.market_estimates = {
            "volatility": 0.0,
            "adv": 0.0,  # Average daily volume
            "market_depth": 0.0,
        }
        
        # Model performance tracking
        self.prediction_accuracy = []  # Track prediction accuracy if actual impact observed
        
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
                
    def _extract_market_parameters(self, orderbook: OrderBook, metrics: MarketMetrics) -> Dict[str, float]:
        """
        Extract market parameters from data
        
        Args:
            orderbook: Current orderbook
            metrics: Market metrics
            
        Returns:
            Dict[str, float]: Market parameters
        """
        # Extract basic parameters
        mid_price = orderbook.mid_price()
        volatility = metrics.volatility / 100.0  # Convert from percentage to decimal
        
        # Estimate market depth from orderbook
        bid_depth = sum(level.quantity for level in orderbook.bids)
        ask_depth = sum(level.quantity for level in orderbook.asks)
        total_depth = bid_depth + ask_depth
        
        # Estimate average daily volume (ADV)
        # This would typically come from external data in a real system
        # Here we'll approximate using current orderbook depth
        proxy_adv = total_depth * 1000  # Rough estimate: assume 1000x the visible liquidity trades daily
        
        # Calculate spread as percentage
        spread_pct = (orderbook.spread() / mid_price) if mid_price > 0 else 0.0
        
        # Update market estimates
        self.market_estimates["volatility"] = volatility
        self.market_estimates["adv"] = proxy_adv
        self.market_estimates["market_depth"] = total_depth
        
        return {
            "mid_price": mid_price,
            "volatility": volatility,
            "bid_depth": bid_depth,
            "ask_depth": ask_depth,
            "total_depth": total_depth,
            "spread_pct": spread_pct,
            "adv_proxy": proxy_adv
        }
    
    def _almgren_chriss_impact(self, market_params: Dict[str, float],
                              quantity: float, is_buy: bool) -> Dict[str, float]:
        """
        Calculate impact using Almgren-Chriss model
        
        Args:
            market_params: Market parameters
            quantity: Order quantity
            is_buy: True for buy orders, False for sell orders
            
        Returns:
            Dict[str, float]: Impact results
        """
        # Extract parameters
        mid_price = market_params["mid_price"]
        volatility = market_params["volatility"]
        spread_pct = market_params["spread_pct"]
        market_depth = market_params["total_depth"]
        
        # Order size relative to market depth
        relative_size = quantity / market_depth if market_depth > 0 else 1.0
        
        # Order size as percentage of ADV
        pct_of_adv = (quantity / market_params["adv_proxy"]) * 100 if market_params["adv_proxy"] > 0 else 1.0
        
        # Temporary impact calculation
        # Includes half the spread as a baseline cost
        spread_cost = spread_pct * self.params["spread_cost_factor"]
        
        # Factor in volatility and order size for temporary impact
        temp_impact_factor = (
            self.params["ac_temporary_impact"] * 
            volatility * 
            (1 + relative_size) *
            (1 + self.params["ac_volatility_scaling"] * volatility)
        )
        
        # Square root model for temporary impact
        temporary_impact = spread_cost + temp_impact_factor * math.sqrt(relative_size)
        
        # Permanent impact calculation (linear with order size)
        permanent_impact = (
            self.params["ac_permanent_impact"] * 
            volatility * 
            relative_size *
            (1 + self.params["ac_volatility_scaling"] * volatility / 2)
        )
        
        # Total impact
        total_impact = temporary_impact + permanent_impact
        
        # Ensure minimum impact
        total_impact = max(total_impact, self.params["min_impact"])
        
        # Convert impact percentage to cost
        impact_cost = mid_price * quantity * total_impact
        
        return {
            "temporary_impact": temporary_impact * 100,  # Convert to percentage
            "permanent_impact": permanent_impact * 100,  # Convert to percentage
            "total_impact": total_impact * 100,          # Convert to percentage
            "impact_cost": impact_cost,
            "relative_size": relative_size,
            "pct_of_adv": pct_of_adv,
            "spread_cost_pct": spread_cost * 100         # Convert to percentage
        }
    
    def _square_root_impact(self, market_params: Dict[str, float],
                           quantity: float, is_buy: bool) -> Dict[str, float]:
        """
        Calculate impact using square root model
        
        Args:
            market_params: Market parameters
            quantity: Order quantity
            is_buy: True for buy orders, False for sell orders
            
        Returns:
            Dict[str, float]: Impact results
        """
        # Extract parameters
        mid_price = market_params["mid_price"]
        volatility = market_params["volatility"]
        spread_pct = market_params["spread_pct"]
        market_depth = market_params["total_depth"]
        
        # Order size relative to market depth
        relative_size = quantity / market_depth if market_depth > 0 else 1.0
        
        # Order size as percentage of ADV
        pct_of_adv = (quantity / market_params["adv_proxy"]) * 100 if market_params["adv_proxy"] > 0 else 1.0
        
        # Spread cost
        spread_cost = spread_pct * self.params["spread_cost_factor"]
        
        # Simple square root model: impact = factor * volatility * sqrt(relative_size)
        impact_factor = self.params["sqrt_impact_factor"] * (1 + volatility)
        
        # Total impact (no separate temporary/permanent distinction)
        total_impact = spread_cost + impact_factor * math.sqrt(relative_size)
        
        # Ensure minimum impact
        total_impact = max(total_impact, self.params["min_impact"])
        
        # Convert impact percentage to cost
        impact_cost = mid_price * quantity * total_impact
        
        return {
            "temporary_impact": total_impact * 100,    # Convert to percentage
            "permanent_impact": 0.0,                   # No permanent impact in this model
            "total_impact": total_impact * 100,        # Convert to percentage
            "impact_cost": impact_cost,
            "relative_size": relative_size,
            "pct_of_adv": pct_of_adv,
            "spread_cost_pct": spread_cost * 100       # Convert to percentage
        }
    
    def _linear_impact(self, market_params: Dict[str, float],
                      quantity: float, is_buy: bool) -> Dict[str, float]:
        """
        Calculate impact using linear model
        
        Args:
            market_params: Market parameters
            quantity: Order quantity
            is_buy: True for buy orders, False for sell orders
            
        Returns:
            Dict[str, float]: Impact results
        """
        # Extract parameters
        mid_price = market_params["mid_price"]
        volatility = market_params["volatility"]
        spread_pct = market_params["spread_pct"]
        market_depth = market_params["total_depth"]
        
        # Order size relative to market depth
        relative_size = quantity / market_depth if market_depth > 0 else 1.0
        
        # Order size as percentage of ADV
        pct_of_adv = (quantity / market_params["adv_proxy"]) * 100 if market_params["adv_proxy"] > 0 else 1.0
        
        # Spread cost
        spread_cost = spread_pct * self.params["spread_cost_factor"]
        
        # Linear model: impact = factor * volatility * relative_size
        impact_factor = self.params["linear_impact_factor"] * (1 + volatility)
        
        # Total impact
        total_impact = spread_cost + impact_factor * relative_size
        
        # Ensure minimum impact
        total_impact = max(total_impact, self.params["min_impact"])
        
        # Convert impact percentage to cost
        impact_cost = mid_price * quantity * total_impact
        
        return {
            "temporary_impact": total_impact * 100,    # Convert to percentage
            "permanent_impact": 0.0,                   # No permanent impact in this model
            "total_impact": total_impact * 100,        # Convert to percentage
            "impact_cost": impact_cost,
            "relative_size": relative_size,
            "pct_of_adv": pct_of_adv,
            "spread_cost_pct": spread_cost * 100       # Convert to percentage
        }
    
    @measure_latency("market_impact_calculation")
    def calculate_impact(self, orderbook: OrderBook, metrics: MarketMetrics,
                        quantity: float, is_buy: bool = True) -> Dict[str, float]:
        """
        Calculate market impact
        
        Args:
            orderbook: Current orderbook
            metrics: Market metrics
            quantity: Order quantity
            is_buy: True for buy orders, False for sell orders
            
        Returns:
            Dict[str, float]: Impact results
        """
        # Extract market parameters
        market_params = self._extract_market_parameters(orderbook, metrics)
        
        # Calculate impact based on selected model
        if self.model_type == ImpactModelType.ALMGREN_CHRISS:
            results = self._almgren_chriss_impact(market_params, quantity, is_buy)
        elif self.model_type == ImpactModelType.SQUARE_ROOT:
            results = self._square_root_impact(market_params, quantity, is_buy)
        elif self.model_type == ImpactModelType.LINEAR:
            results = self._linear_impact(market_params, quantity, is_buy)
        else:
            # Default to Almgren-Chriss
            results = self._almgren_chriss_impact(market_params, quantity, is_buy)
            
        self.logger.debug(
            f"Market impact calculation ({self.model_type.value}): "
            f"size={quantity:.4f}, "
            f"rel_size={results['relative_size']:.6f}, "
            f"impact={results['total_impact']:.4f}%, "
            f"cost={results['impact_cost']:.2f}"
        )
            
        return results
    
    def update_with_actual_impact(self, predicted_impact: float, actual_impact: float) -> None:
        """
        Update model with observed impact for accuracy tracking
        
        Args:
            predicted_impact: Previously predicted impact
            actual_impact: Observed actual impact
        """
        if predicted_impact > 0 and actual_impact > 0:
            # Calculate prediction error
            error = (actual_impact - predicted_impact) / predicted_impact
            
            # Add to accuracy tracking
            self.prediction_accuracy.append((predicted_impact, actual_impact, error))
            
            # Keep list size in check
            if len(self.prediction_accuracy) > 100:
                self.prediction_accuracy.pop(0)
                
            # Log accuracy statistics
            errors = [item[2] for item in self.prediction_accuracy]
            mean_error = sum(errors) / len(errors) if errors else 0
            
            self.logger.info(
                f"Impact prediction accuracy: "
                f"mean_error={mean_error:.2%}, "
                f"samples={len(errors)}"
            )
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model
        
        Returns:
            Dict[str, Any]: Model information
        """
        return {
            "model_type": self.model_type.value,
            "parameters": self.params,
            "market_estimates": self.market_estimates,
            "prediction_accuracy": {
                "sample_count": len(self.prediction_accuracy),
                "mean_error": (
                    sum([item[2] for item in self.prediction_accuracy]) / 
                    len(self.prediction_accuracy) if self.prediction_accuracy else 0
                )
            }
        }