"""
Trade simulation engine
"""
import logging
import time
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum

from data.market_data import OrderBook, MarketMetrics
from models.slippage import SlippageModel
from models.market_impact import AlmgrenChrissModel
from models.fee_calculator import FeeCalculator, FeeTier
from utils.performance import measure_latency, latency_tracker

class OrderType(Enum):
    """Order types"""
    MARKET = "market"
    LIMIT = "limit"

class TradeSide(Enum):
    """Trade sides"""
    BUY = "buy"
    SELL = "sell"

class TradeSimulator:
    """
    Trade simulation engine
    """
    
    def __init__(self):
        """Initialize trade simulator"""
        self.logger = logging.getLogger(__name__)
        self.slippage_model = SlippageModel()
        self.market_impact_model = AlmgrenChrissModel()
        self.fee_calculator = FeeCalculator()
        
        # Track the latest data
        self.latest_orderbook: Optional[OrderBook] = None
        self.latest_metrics: Optional[MarketMetrics] = None
        
        # Track performance
        self.processing_times: List[float] = []
        
    def update_market_data(self, orderbook: OrderBook, metrics: MarketMetrics) -> None:
        """
        Update market data for simulation
        
        Args:
            orderbook: Latest orderbook
            metrics: Latest market metrics
        """
        self.latest_orderbook = orderbook
        self.latest_metrics = metrics
        
        # Update slippage model with new data
        self.slippage_model.update(orderbook, 1.0)  # Update with a standard quantity
        
    @measure_latency("trade_simulation")
    def simulate_trade(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulate a trade with the given parameters
        
        Args:
            params: Trade parameters including:
                - exchange: Exchange name
                - symbol: Trading symbol
                - order_type: OrderType
                - side: TradeSide
                - quantity: Order quantity in base currency
                - quantity_quote: Order quantity in quote currency (alternative to quantity)
                - volatility: Market volatility override (optional)
                - fee_tier: FeeTier
                
        Returns:
            Dict[str, Any]: Simulation results
        """
        start_time = time.time()
        
        # Validate inputs
        if not self.latest_orderbook or not self.latest_metrics:
            self.logger.error("Cannot simulate trade: no market data available")
            return {
                "error": "No market data available for simulation"
            }
            
        # Extract parameters
        exchange = params.get("exchange", "OKX")
        symbol = params.get("symbol", self.latest_orderbook.symbol)
        order_type = params.get("order_type", OrderType.MARKET)
        side = params.get("side", TradeSide.BUY)
        quantity = params.get("quantity", 0.0)
        quantity_quote = params.get("quantity_quote", 0.0)
        volatility = params.get("volatility", self.latest_metrics.volatility)
        fee_tier = params.get("fee_tier", FeeTier.TIER1)
        
        # Convert quantity if provided in quote currency
        mid_price = self.latest_orderbook.mid_price()
        if quantity <= 0 and quantity_quote > 0:
            quantity = quantity_quote / mid_price
            
        if quantity <= 0:
            self.logger.error("Cannot simulate trade: invalid quantity")
            return {
                "error": "Invalid quantity"
            }
            
        # Check if this is a buy or sell
        is_buy = side == TradeSide.BUY
        
        # Calculate order value in quote currency
        order_value = quantity * mid_price
        
        # 1. Calculate expected slippage
        slippage_pct = self.slippage_model.predict_slippage_quantile(
            self.latest_orderbook, quantity, is_buy, quantile=0.9
        )
        
        # 2. Calculate market impact using Almgren-Chriss model
        # Override volatility if provided
        if volatility != self.latest_metrics.volatility:
            metrics_with_override = MarketMetrics(
                timestamp=self.latest_metrics.timestamp,
                symbol=self.latest_metrics.symbol,
                mid_price=self.latest_metrics.mid_price,
                spread=self.latest_metrics.spread,
                bid_depth=self.latest_metrics.bid_depth,
                ask_depth=self.latest_metrics.ask_depth,
                volatility=volatility
            )
        else:
            metrics_with_override = self.latest_metrics
            
        impact_results = self.market_impact_model.calculate_impact(
            self.latest_orderbook, metrics_with_override, quantity
        )
        
        # 3. Estimate maker/taker proportion
        # For market orders, it's all taker
        if order_type == OrderType.MARKET:
            maker_proportion = 0.0
        else:
            # For limit orders, estimate based on market conditions
            # This is a simple model - in reality, it would depend on limit price
            spread = self.latest_orderbook.spread()
            if spread <= 0:
                maker_proportion = 0.5  # Default when spread is unknown
            else:
                # Higher volatility or wider spread tends to increase maker proportion
                spread_factor = min(1.0, spread / mid_price * 1000)  # Normalize spread
                vol_factor = min(1.0, volatility / 5.0)  # Normalize volatility
                
                # Simple logistic model to estimate maker proportion
                maker_base = 0.7  # Base maker proportion for limit orders
                maker_proportion = maker_base * (1 - vol_factor * 0.5) * (1 + spread_factor * 0.3)
                maker_proportion = max(0.0, min(1.0, maker_proportion))
        
        # 4. Calculate fees
        fee_results = self.fee_calculator.calculate_fees(
            order_value, fee_tier, maker_proportion
        )
        
        # 5. Calculate net cost
        slippage_cost = order_value * slippage_pct / 100
        impact_cost = impact_results["impact_cost"]
        fee_cost = fee_results["total_fee"]
        
        net_cost = slippage_cost + impact_cost + fee_cost
        net_cost_pct = (net_cost / order_value) * 100 if order_value > 0 else 0.0
        
        # Record processing latency
        end_time = time.time()
        processing_time_ms = (end_time - start_time) * 1000
        self.processing_times.append(processing_time_ms)
        
        # Keep only the most recent 100 measurements
        if len(self.processing_times) > 100:
            self.processing_times.pop(0)
        
        # Create result
        result = {
            # Input parameters
            "exchange": exchange,
            "symbol": symbol,
            "order_type": order_type.value,
            "side": side.value,
            "quantity": quantity,
            "order_value": order_value,
            "fee_tier": fee_tier.name,
            
            # Market conditions
            "mid_price": mid_price,
            "spread": self.latest_orderbook.spread(),
            "spread_bps": (self.latest_orderbook.spread() / mid_price) * 10000,
            "volatility": volatility,
            
            # Simulation results
            "expected_slippage_pct": slippage_pct,
            "expected_slippage_cost": slippage_cost,
            
            "market_impact": {
                "temporary_impact_pct": impact_results["temporary_impact"],
                "permanent_impact_pct": impact_results["permanent_impact"],
                "total_impact_pct": impact_results["total_impact"],
                "impact_cost": impact_results["impact_cost"],
                "relative_size": impact_results["relative_size"],
                "pct_of_adv": impact_results["pct_of_adv"]
            },
            
            "fees": {
                "maker_proportion": maker_proportion,
                "taker_proportion": 1.0 - maker_proportion,
                "maker_fee_rate": fee_results["maker_fee_rate"],
                "taker_fee_rate": fee_results["taker_fee_rate"],
                "maker_fee": fee_results["maker_fee"],
                "taker_fee": fee_results["taker_fee"],
                "total_fee": fee_results["total_fee"],
                "effective_fee_rate": fee_results["effective_fee_rate"]
            },
            
            "net_cost": net_cost,
            "net_cost_pct": net_cost_pct,
            
            # Performance metrics
            "internal_latency_ms": processing_time_ms,
            "avg_latency_ms": sum(self.processing_times) / len(self.processing_times) if self.processing_times else 0.0
        }
        
        self.logger.info(
            f"Trade simulation: {symbol} {side.value} {quantity:.4f} - "
            f"Slippage: {slippage_pct:.4f}%, Impact: {impact_results['total_impact']:.4f}%, "
            f"Fees: {fee_results['total_fee']:.4f}, Net: {net_cost:.4f} ({net_cost_pct:.4f}%)"
        )
        
        return result
    
    def get_performance_metrics(self) -> Dict[str, float]:
        """
        Get performance metrics for the simulator
        
        Returns:
            Dict[str, float]: Performance metrics
        """
        metrics = {}
        
        # Include latency stats from the latency tracker
        metrics["slippage_prediction_latency"] = latency_tracker.get_average("slippage_prediction_linear")
        metrics["market_impact_latency"] = latency_tracker.get_average("market_impact_calculation")
        metrics["fee_calculation_latency"] = latency_tracker.get_average("fee_calculation")
        metrics["trade_simulation_latency"] = latency_tracker.get_average("trade_simulation")
        
        # Calculate simulator-specific metrics
        if self.processing_times:
            metrics["avg_processing_time"] = sum(self.processing_times) / len(self.processing_times)
            metrics["max_processing_time"] = max(self.processing_times)
            metrics["min_processing_time"] = min(self.processing_times)
            
            # Sort for percentiles
            sorted_times = sorted(self.processing_times)
            metrics["p50_processing_time"] = sorted_times[len(sorted_times) // 2]
            metrics["p95_processing_time"] = sorted_times[int(len(sorted_times) * 0.95)]
            metrics["p99_processing_time"] = sorted_times[int(len(sorted_times) * 0.99)]
        
        return metrics