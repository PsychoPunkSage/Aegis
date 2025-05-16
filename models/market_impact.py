"""
Almgren-Chriss market impact model implementation
"""
import numpy as np
import math
import logging
from typing import Dict, Any, Optional
from data.market_data import OrderBook, MarketMetrics
from utils.performance import measure_latency

class AlmgrenChrissModel:
    """
    Implementation of the Almgren-Chriss model for market impact estimation
    
    The model estimates both temporary and permanent market impact of a trade
    based on market characteristics and order parameters.
    """
    
    def __init__(self):
        """Initialize Almgren-Chriss model"""
        self.logger = logging.getLogger(__name__)
        
        # Model parameters - these would typically be calibrated to market data
        # Default values are set based on common ranges but should be tuned
        self.temporary_impact_factor = 0.1
        self.permanent_impact_factor = 0.02
        self.market_vol_scaling = 0.5
        
    def set_parameters(self, temporary_impact: float, permanent_impact: float, 
                      vol_scaling: float) -> None:
        """
        Set model parameters
        
        Args:
            temporary_impact: Factor for temporary impact calculation
            permanent_impact: Factor for permanent impact calculation
            vol_scaling: Volatility scaling factor
        """
        self.temporary_impact_factor = temporary_impact
        self.permanent_impact_factor = permanent_impact
        self.market_vol_scaling = vol_scaling
        
    def _calculate_market_parameters(self, orderbook: OrderBook, 
                                    metrics: MarketMetrics) -> Dict[str, float]:
        """
        Calculate market parameters for the model
        
        Args:
            orderbook: Current orderbook state
            metrics: Market metrics
            
        Returns:
            Dict[str, float]: Market parameters
        """
        # Extract mid price
        mid_price = orderbook.mid_price()
        
        # Calculate market volatility (annualized)
        # In a real implementation, this would use a time series of prices
        market_vol = metrics.volatility
        if market_vol <= 0:
            market_vol = 0.5  # Default value if not available
        
        # Convert from percentage to decimal
        market_vol = market_vol / 100.0
        
        # Annualize the volatility (assuming metrics.volatility is daily)
        annualized_vol = market_vol * math.sqrt(365)
        
        # Calculate average daily volume (ADV)
        # In a production system, this would come from historical data
        # Here we'll approximate using current orderbook depth
        bid_depth = sum(level.quantity for level in orderbook.bids)
        ask_depth = sum(level.quantity for level in orderbook.asks)
        
        # Simple proxy for daily volume - this is a simplification
        proxy_adv = (bid_depth + ask_depth) * 100
        
        # Market depth parameter
        market_depth = proxy_adv / annualized_vol if annualized_vol > 0 else proxy_adv / 0.01
        
        # Bid-ask spread in percentage
        spread_pct = orderbook.spread() / mid_price
        
        return {
            "mid_price": mid_price,
            "volatility": annualized_vol,
            "market_depth": market_depth,
            "spread_pct": spread_pct,
            "adv_proxy": proxy_adv
        }
        
    @measure_latency("market_impact_calculation")
    def calculate_impact(self, orderbook: OrderBook, metrics: MarketMetrics, 
                        quantity: float, execution_time: float = 1.0) -> Dict[str, float]:
        """
        Calculate market impact using the Almgren-Chriss model
        
        Args:
            orderbook: Current orderbook state
            metrics: Market metrics
            quantity: Order quantity in base currency
            execution_time: Time to execute the order in hours (default: instant execution)
            
        Returns:
            Dict[str, float]: Impact metrics including:
                - temporary_impact: Immediate price impact (in %)
                - permanent_impact: Long-term price impact (in %)
                - total_impact: Total market impact (in %)
                - impact_cost: Cost of impact in quote currency
        """
        # Get market parameters
        market_params = self._calculate_market_parameters(orderbook, metrics)
        
        # Extract key parameters
        mid_price = market_params["mid_price"]
        volatility = market_params["volatility"]
        market_depth = market_params["market_depth"]
        spread_pct = market_params["spread_pct"]
        adv_proxy = market_params["adv_proxy"]
        
        # Order size relative to market depth
        relative_size = quantity / market_depth if market_depth > 0 else 1.0
        
        # Order size as percentage of ADV
        pct_of_adv = (quantity / adv_proxy) * 100 if adv_proxy > 0 else 1.0
        
        # Temporary impact calculation
        # Almgren-Chriss model: temporary impact scales with square root of quantity/time
        # and is proportional to volatility
        if execution_time > 0:
            # For non-instantaneous execution
            temp_impact_factor = self.temporary_impact_factor * volatility * spread_pct
            temporary_impact = temp_impact_factor * math.sqrt(relative_size / execution_time)
        else:
            # For instantaneous execution (market order)
            # Include spread cost in temporary impact
            temporary_impact = spread_pct / 2 + self.temporary_impact_factor * volatility * math.sqrt(relative_size)
            
        # Permanent impact calculation 
        # Scales linearly with order size
        permanent_impact = self.permanent_impact_factor * volatility * relative_size
        
        # Apply volatility scaling
        temporary_impact *= (1 + self.market_vol_scaling * volatility)
        permanent_impact *= (1 + self.market_vol_scaling * volatility / 2)
        
        # Total impact
        total_impact = temporary_impact + permanent_impact
        
        # Convert impact percentage to cost in quote currency
        impact_cost = mid_price * quantity * total_impact / 100
        
        # Additional metrics for analysis
        half_spread_cost = mid_price * quantity * (spread_pct / 2) / 100
        
        # Log the calculation
        self.logger.debug(
            f"Market impact calculation: "
            f"size={quantity:.4f}, "
            f"rel_size={relative_size:.6f}, "
            f"pct_adv={pct_of_adv:.4f}%, "
            f"temp={temporary_impact:.6f}%, "
            f"perm={permanent_impact:.6f}%, "
            f"total={total_impact:.6f}%, "
            f"cost={impact_cost:.4f}"
        )
        
        return {
            "temporary_impact": temporary_impact,  # in percentage
            "permanent_impact": permanent_impact,  # in percentage
            "total_impact": total_impact,          # in percentage
            "impact_cost": impact_cost,            # in quote currency
            "half_spread_cost": half_spread_cost,  # in quote currency
            "relative_size": relative_size,
            "pct_of_adv": pct_of_adv
        }