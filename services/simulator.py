# """
# Trade simulation engine
# """
# import logging
# import time
# from typing import Dict, Any, Optional, List, Tuple
# from enum import Enum

# from data.market_data import OrderBook, MarketMetrics
# from models.slippage import SlippageModel
# from models.market_impact import AlmgrenChrissModel
# from models.fee_calculator import FeeCalculator, FeeTier
# from utils.performance import measure_latency, latency_tracker

# class OrderType(Enum):
#     """Order types"""
#     MARKET = "market"
#     LIMIT = "limit"

# class TradeSide(Enum):
#     """Trade sides"""
#     BUY = "buy"
#     SELL = "sell"

# class TradeSimulator:
#     """
#     Trade simulation engine
#     """
    
#     def __init__(self):
#         """Initialize trade simulator"""
#         self.logger = logging.getLogger(__name__)
#         self.slippage_model = SlippageModel()
#         self.market_impact_model = AlmgrenChrissModel()
#         self.fee_calculator = FeeCalculator()
        
#         # Track the latest data
#         self.latest_orderbook: Optional[OrderBook] = None
#         self.latest_metrics: Optional[MarketMetrics] = None
        
#         # Track performance
#         self.processing_times: List[float] = []
        
#     def update_market_data(self, orderbook: OrderBook, metrics: MarketMetrics) -> None:
#         """
#         Update market data for simulation
        
#         Args:
#             orderbook: Latest orderbook
#             metrics: Latest market metrics
#         """
#         self.latest_orderbook = orderbook
#         self.latest_metrics = metrics
        
#         # Update slippage model with new data
#         self.slippage_model.update(orderbook, 1.0)  # Update with a standard quantity
        
#     @measure_latency("trade_simulation")
#     def simulate_trade(self, params: Dict[str, Any]) -> Dict[str, Any]:
#         """
#         Simulate a trade with the given parameters
        
#         Args:
#             params: Trade parameters including:
#                 - exchange: Exchange name
#                 - symbol: Trading symbol
#                 - order_type: OrderType
#                 - side: TradeSide
#                 - quantity: Order quantity in base currency
#                 - quantity_quote: Order quantity in quote currency (alternative to quantity)
#                 - volatility: Market volatility override (optional)
#                 - fee_tier: FeeTier
                
#         Returns:
#             Dict[str, Any]: Simulation results
#         """
#         start_time = time.time()
        
#         # Validate inputs
#         if not self.latest_orderbook or not self.latest_metrics:
#             self.logger.error("Cannot simulate trade: no market data available")
#             return {
#                 "error": "No market data available for simulation"
#             }
            
#         # Extract parameters
#         exchange = params.get("exchange", "OKX")
#         symbol = params.get("symbol", self.latest_orderbook.symbol)
#         order_type = params.get("order_type", OrderType.MARKET)
#         side = params.get("side", TradeSide.BUY)
#         quantity = params.get("quantity", 0.0)
#         quantity_quote = params.get("quantity_quote", 0.0)
#         volatility = params.get("volatility", self.latest_metrics.volatility)
#         fee_tier = params.get("fee_tier", FeeTier.TIER1)
        
#         # Convert quantity if provided in quote currency
#         mid_price = self.latest_orderbook.mid_price()
#         if quantity <= 0 and quantity_quote > 0:
#             quantity = quantity_quote / mid_price
            
#         if quantity <= 0:
#             self.logger.error("Cannot simulate trade: invalid quantity")
#             return {
#                 "error": "Invalid quantity"
#             }
            
#         # Check if this is a buy or sell
#         is_buy = side == TradeSide.BUY
        
#         # Calculate order value in quote currency
#         order_value = quantity * mid_price
        
#         # 1. Calculate expected slippage
#         slippage_pct = self.slippage_model.predict_slippage_quantile(
#             self.latest_orderbook, quantity, is_buy, quantile=0.9
#         )
        
#         # 2. Calculate market impact using Almgren-Chriss model
#         # Override volatility if provided
#         if volatility != self.latest_metrics.volatility:
#             metrics_with_override = MarketMetrics(
#                 timestamp=self.latest_metrics.timestamp,
#                 symbol=self.latest_metrics.symbol,
#                 mid_price=self.latest_metrics.mid_price,
#                 spread=self.latest_metrics.spread,
#                 bid_depth=self.latest_metrics.bid_depth,
#                 ask_depth=self.latest_metrics.ask_depth,
#                 volatility=volatility
#             )
#         else:
#             metrics_with_override = self.latest_metrics
            
#         impact_results = self.market_impact_model.calculate_impact(
#             self.latest_orderbook, metrics_with_override, quantity
#         )
        
#         # 3. Estimate maker/taker proportion
#         # For market orders, it's all taker
#         if order_type == OrderType.MARKET:
#             maker_proportion = 0.0
#         else:
#             # For limit orders, estimate based on market conditions
#             # This is a simple model - in reality, it would depend on limit price
#             spread = self.latest_orderbook.spread()
#             if spread <= 0:
#                 maker_proportion = 0.5  # Default when spread is unknown
#             else:
#                 # Higher volatility or wider spread tends to increase maker proportion
#                 spread_factor = min(1.0, spread / mid_price * 1000)  # Normalize spread
#                 vol_factor = min(1.0, volatility / 5.0)  # Normalize volatility
                
#                 # Simple logistic model to estimate maker proportion
#                 maker_base = 0.7  # Base maker proportion for limit orders
#                 maker_proportion = maker_base * (1 - vol_factor * 0.5) * (1 + spread_factor * 0.3)
#                 maker_proportion = max(0.0, min(1.0, maker_proportion))
        
#         # 4. Calculate fees
#         fee_results = self.fee_calculator.calculate_fees(
#             order_value, fee_tier, maker_proportion
#         )
        
#         # 5. Calculate net cost
#         slippage_cost = order_value * slippage_pct / 100
#         impact_cost = impact_results["impact_cost"]
#         fee_cost = fee_results["total_fee"]
        
#         net_cost = slippage_cost + impact_cost + fee_cost
#         net_cost_pct = (net_cost / order_value) * 100 if order_value > 0 else 0.0
        
#         # Record processing latency
#         end_time = time.time()
#         processing_time_ms = (end_time - start_time) * 1000
#         self.processing_times.append(processing_time_ms)
        
#         # Keep only the most recent 100 measurements
#         if len(self.processing_times) > 100:
#             self.processing_times.pop(0)
        
#         # Create result
#         result = {
#             # Input parameters
#             "exchange": exchange,
#             "symbol": symbol,
#             "order_type": order_type.value,
#             "side": side.value,
#             "quantity": quantity,
#             "order_value": order_value,
#             "fee_tier": fee_tier.name,
            
#             # Market conditions
#             "mid_price": mid_price,
#             "spread": self.latest_orderbook.spread(),
#             "spread_bps": (self.latest_orderbook.spread() / mid_price) * 10000,
#             "volatility": volatility,
            
#             # Simulation results
#             "expected_slippage_pct": slippage_pct,
#             "expected_slippage_cost": slippage_cost,
            
#             "market_impact": {
#                 "temporary_impact_pct": impact_results["temporary_impact"],
#                 "permanent_impact_pct": impact_results["permanent_impact"],
#                 "total_impact_pct": impact_results["total_impact"],
#                 "impact_cost": impact_results["impact_cost"],
#                 "relative_size": impact_results["relative_size"],
#                 "pct_of_adv": impact_results["pct_of_adv"]
#             },
            
#             "fees": {
#                 "maker_proportion": maker_proportion,
#                 "taker_proportion": 1.0 - maker_proportion,
#                 "maker_fee_rate": fee_results["maker_fee_rate"],
#                 "taker_fee_rate": fee_results["taker_fee_rate"],
#                 "maker_fee": fee_results["maker_fee"],
#                 "taker_fee": fee_results["taker_fee"],
#                 "total_fee": fee_results["total_fee"],
#                 "effective_fee_rate": fee_results["effective_fee_rate"]
#             },
            
#             "net_cost": net_cost,
#             "net_cost_pct": net_cost_pct,
            
#             # Performance metrics
#             "internal_latency_ms": processing_time_ms,
#             "avg_latency_ms": sum(self.processing_times) / len(self.processing_times) if self.processing_times else 0.0
#         }
        
#         self.logger.info(
#             f"Trade simulation: {symbol} {side.value} {quantity:.4f} - "
#             f"Slippage: {slippage_pct:.4f}%, Impact: {impact_results['total_impact']:.4f}%, "
#             f"Fees: {fee_results['total_fee']:.4f}, Net: {net_cost:.4f} ({net_cost_pct:.4f}%)"
#         )
        
#         return result
    
#     def get_performance_metrics(self) -> Dict[str, float]:
#         """
#         Get performance metrics for the simulator
        
#         Returns:
#             Dict[str, float]: Performance metrics
#         """
#         metrics = {}
        
#         # Include latency stats from the latency tracker
#         metrics["slippage_prediction_latency"] = latency_tracker.get_average("slippage_prediction_linear")
#         metrics["market_impact_latency"] = latency_tracker.get_average("market_impact_calculation")
#         metrics["fee_calculation_latency"] = latency_tracker.get_average("fee_calculation")
#         metrics["trade_simulation_latency"] = latency_tracker.get_average("trade_simulation")
        
#         # Calculate simulator-specific metrics
#         if self.processing_times:
#             metrics["avg_processing_time"] = sum(self.processing_times) / len(self.processing_times)
#             metrics["max_processing_time"] = max(self.processing_times)
#             metrics["min_processing_time"] = min(self.processing_times)
            
#             # Sort for percentiles
#             sorted_times = sorted(self.processing_times)
#             metrics["p50_processing_time"] = sorted_times[len(sorted_times) // 2]
#             metrics["p95_processing_time"] = sorted_times[int(len(sorted_times) * 0.95)]
#             metrics["p99_processing_time"] = sorted_times[int(len(sorted_times) * 0.99)]
        
#         return metrics

"""
Enhanced trade simulation engine
"""
import logging
import time
import threading
import multiprocessing
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, Optional, List, Tuple, Callable
from queue import Queue
from enum import Enum
from datetime import datetime

from models.slippage import SlippageModel
from utils.caching import memoize, LRUCache
from data.market_data import OrderBook, MarketMetrics
from models.market_impact import MarketImpactModel, ImpactModelType
from models.fee_calculator import FeeCalculator, FeeTier
from models.maker_taker import MakerTakerEstimator
from models.volatility import VolatilityCalculator
from utils.performance import measure_latency, latency_tracker

class OrderType(Enum):
    """Order types"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"

class TradeSide(Enum):
    """Trade sides"""
    BUY = "buy"
    SELL = "sell"

class SimulationMode(Enum):
    """Simulation modes"""
    STANDARD = "standard"
    ADVANCED = "advanced"
    BATCH = "batch"

class TradeSimulator:
    """
    Enhanced trade simulation engine
    """
    
    def __init__(self, num_threads: int = 2):
        """
        Initialize trade simulator
        
        Args:
            num_threads: Number of threads for parallel simulation
        """
        self.logger = logging.getLogger(__name__)
        
        # Initialize models
        self.slippage_model = SlippageModel()
        self.impact_model = MarketImpactModel()
        self.fee_calculator = FeeCalculator()
        self.maker_taker_estimator = MakerTakerEstimator()
        self.volatility_calculator = VolatilityCalculator()
        self.result_cache = LRUCache(max_size=100)
        
        # Track the latest data
        self.latest_orderbook: Optional[OrderBook] = None
        self.latest_metrics: Optional[MarketMetrics] = None
        
        # Thread pool for parallel simulations
        self.executor = ThreadPoolExecutor(max_workers=num_threads)
        
        # Queue for batch simulations
        self.batch_queue = Queue()
        self.batch_results = Queue()
        
        # Flags
        self.running = True
        self.batch_running = False
        
        # Start batch processing thread
        self.batch_thread = threading.Thread(target=self._batch_processor, daemon=True)
        self.batch_thread.start()
        
        # Track performance
        self.processing_times: List[float] = []
        
        self.logger.info(f"Trade simulator initialized with {num_threads} threads")
        
    def _batch_processor(self) -> None:
        """Background thread for processing batch simulations"""
        while self.running:
            try:
                if not self.batch_queue.empty():
                    self.batch_running = True
                    
                    # Get batch simulation request
                    batch_id, base_params, param_variations = self.batch_queue.get()
                    self.logger.info(f"Processing batch simulation {batch_id} with {len(param_variations)} variations")
                    
                    # Run simulations
                    results = []
                    start_time = time.time()
                    
                    # Process each variation
                    futures = []
                    for variation in param_variations:
                        # Create parameter set for this variation
                        params = base_params.copy()
                        params.update(variation)
                        
                        # Submit to thread pool
                        future = self.executor.submit(self.simulate_trade, params)
                        futures.append((variation, future))
                    
                    # Collect results
                    for variation, future in futures:
                        result = future.result()
                        results.append({
                            "variation": variation,
                            "result": result
                        })
                    
                    # Calculate total time
                    total_time = time.time() - start_time
                    
                    # Put results in the output queue
                    self.batch_results.put({
                        "batch_id": batch_id,
                        "count": len(results),
                        "processing_time": total_time,
                        "results": results
                    })
                    
                    self.logger.info(f"Completed batch simulation {batch_id} in {total_time:.2f} seconds")
                    self.batch_running = False
                else:
                    # No work to do, sleep briefly
                    time.sleep(0.1)
            except Exception as e:
                self.logger.error(f"Error in batch processor: {e}", exc_info=True)
                self.batch_running = False
        
    def update_market_data(self, orderbook: OrderBook, metrics: MarketMetrics) -> None:
        """
        Update market data for simulation
        
        Args:
            orderbook: Latest orderbook
            metrics: Latest market metrics
        """
        self.latest_orderbook = orderbook
        self.latest_metrics = metrics
        
        # Update models with new data
        self.slippage_model.update(orderbook, 1.0)  # Update with a standard quantity
        
        # Update volatility calculator
        self.volatility_calculator.add_price(orderbook.timestamp, orderbook.mid_price())
        
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
                - impact_model: Impact model type (optional)
                - simulation_mode: Simulation mode (optional)
                
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
        
        # Handle order type
        order_type_str = params.get("order_type", "market")
        if isinstance(order_type_str, OrderType):
            order_type = order_type_str
        else:
            try:
                order_type = OrderType(order_type_str)
            except ValueError:
                order_type = OrderType.MARKET
                
        # Handle trade side
        side_str = params.get("side", "buy")
        if isinstance(side_str, TradeSide):
            side = side_str
        else:
            try:
                side = TradeSide(side_str)
            except ValueError:
                side = TradeSide.BUY
                
        # Handle quantities
        quantity = params.get("quantity", 0.0)
        quantity_quote = params.get("quantity_quote", 0.0)
        
        # Handle other parameters
        volatility = params.get("volatility", None)  # None means use calculated value
        fee_tier_str = params.get("fee_tier", "TIER1")
        
        # Convert fee tier string to enum if needed
        if isinstance(fee_tier_str, FeeTier):
            fee_tier = fee_tier_str
        else:
            try:
                fee_tier = FeeTier[fee_tier_str]
            except KeyError:
                fee_tier = FeeTier.TIER1
                
        # Handle impact model type
        impact_model_str = params.get("impact_model", "almgren-chriss")
        try:
            impact_model_type = ImpactModelType(impact_model_str)
        except ValueError:
            impact_model_type = ImpactModelType.ALMGREN_CHRISS
        
        # Set impact model type    
        self.impact_model.model_type = impact_model_type
        
        # Handle simulation mode
        mode_str = params.get("simulation_mode", "standard")
        try:
            simulation_mode = SimulationMode(mode_str)
        except ValueError:
            simulation_mode = SimulationMode.STANDARD
            
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
        
        # Check if this is a limit order
        is_limit = order_type in [OrderType.LIMIT, OrderType.STOP_LIMIT]
        
        # Calculate order value in quote currency
        order_value = quantity * mid_price
        
        # Get actual volatility from calculator or use override
        if volatility is None:
            volatility = self.volatility_calculator.get_current_volatility()
            
        # Use new volatility with metrics
        metrics_with_override = MarketMetrics(
            timestamp=self.latest_metrics.timestamp,
            symbol=self.latest_metrics.symbol,
            mid_price=self.latest_metrics.mid_price,
            spread=self.latest_metrics.spread,
            bid_depth=self.latest_metrics.bid_depth,
            ask_depth=self.latest_metrics.ask_depth,
            volatility=volatility
        )
        
        # 1. Calculate expected slippage
        slippage_pct = self.slippage_model.predict_slippage_quantile(
            self.latest_orderbook, quantity, is_buy, quantile=0.9
        )
        slippage_cost = order_value * slippage_pct / 100
        
        # 2. Calculate market impact using selected model
        impact_results = self.impact_model.calculate_impact(
            self.latest_orderbook, metrics_with_override, quantity, is_buy
        )
        
        # 3. Estimate maker/taker proportion
        maker_taker_results = self.maker_taker_estimator.estimate_proportion(
            self.latest_orderbook, metrics_with_override, is_buy, is_limit
        )
        maker_proportion = maker_taker_results["maker_proportion"]
        
        # 4. Calculate fees
        fee_results = self.fee_calculator.calculate_fees(
            order_value, fee_tier, maker_proportion
        )
        
        # 5. Calculate net cost
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
            "impact_model": impact_model_type.value,
            
            # Market conditions
            "mid_price": mid_price,
            "spread": self.latest_orderbook.spread(),
            "spread_bps": (self.latest_orderbook.spread() / mid_price) * 10000 if mid_price > 0 else 0,
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
            "avg_latency_ms": sum(self.processing_times) / len(self.processing_times) if self.processing_times else 0.0,
            "timestamp": datetime.now().isoformat()
        }
        
        # Add additional info for advanced mode
        if simulation_mode == SimulationMode.ADVANCED:
            result["advanced"] = {
                "maker_taker_features": maker_taker_results["features"],
                "volatility_estimates": self.volatility_calculator.get_volatility("all"),
                "impact_model_info": self.impact_model.get_model_info()
            }
        
        self.logger.info(
            f"Trade simulation: {symbol} {side.value} {quantity:.4f} - "
            f"Slippage: {slippage_pct:.4f}%, Impact: {impact_results['total_impact']:.4f}%, "
            f"Fees: {fee_results['total_fee']:.4f}, Net: {net_cost:.4f} ({net_cost_pct:.4f}%)"
        )
        
        return result
    
    def start_batch_simulation(self, base_params: Dict[str, Any], 
                             param_variations: List[Dict[str, Any]]) -> str:
        """
        Start a batch simulation with parameter variations
        
        Args:
            base_params: Base parameters for all simulations
            param_variations: List of parameter variations to apply
            
        Returns:
            str: Batch ID
        """
        batch_id = f"batch_{int(time.time())}"
        
        self.logger.info(f"Queueing batch simulation {batch_id} with {len(param_variations)} variations")

        # Run simulations in parallel
        futures = []
        results = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            for variation in param_variations:
                # Create parameter set for this variation
                params = base_params.copy()
                params.update(variation)
                
                # Submit to thread pool
                future = executor.submit(self.simulate_trade, params)
                futures.append((variation, future))
            
            # Process results as they complete
            for variation, future in futures:
                try:
                    result = future.result()
                    results.append({
                        "variation": variation,
                        "result": result
                    })
                except Exception as e:
                    self.logger.error(f"Error in batch simulation: {e}")
                    results.append({
                        "variation": variation,
                        "error": str(e)
                    })
        
        # Store batch results
        batch_result = {
            "batch_id": batch_id,
            "count": len(results),
            "processing_time": time.time() - int(batch_id.split('_')[1]),
            "results": results
        }
        
        self.batch_results.put(batch_result)
        self.batch_running = False
        
        return batch_id
    
    def get_batch_results(self) -> Optional[Dict[str, Any]]:
        """
        Get results from a completed batch simulation
        
        Returns:
            Optional[Dict[str, Any]]: Batch results if available, None otherwise
        """
        if not self.batch_results.empty():
            return self.batch_results.get()
        return None
    
    def is_batch_running(self) -> bool:
        """
        Check if a batch simulation is currently running
        
        Returns:
            bool: True if batch is running, False otherwise
        """
        return self.batch_running
    
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
        metrics["maker_taker_latency"] = latency_tracker.get_average("maker_taker_estimation")
        metrics["volatility_latency"] = latency_tracker.get_average("volatility_calculation")
        
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
    
    @memoize(maxsize=50, ttl=60)  # Cache for 60 seconds
    def _calculate_base_metrics(self, orderbook, metrics, quantity, is_buy):
        """
        Calculate base metrics for simulation with caching
        """
        # Calculate market parameters that are reused
        market_params = {
            "mid_price": orderbook.mid_price(),
            "spread": orderbook.spread(),
            "spread_bps": (orderbook.spread() / orderbook.mid_price()) * 10000 if orderbook.mid_price() > 0 else 0,
            "volatility": metrics.volatility,
            "bid_depth": metrics.bid_depth,
            "ask_depth": metrics.ask_depth,
        }

        return market_params

    def shutdown(self) -> None:
        """Shut down the simulator and release resources"""
        self.logger.info("Shutting down trade simulator")
        self.running = False
        
        # Wait for batch thread to finish
        if self.batch_thread.is_alive():
            self.batch_thread.join(timeout=1.0)
            
        # Shut down thread pool
        self.executor.shutdown(wait=False)