"""
Data processor for market data
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from collections import deque

from data.market_data import OrderBook, MarketMetrics

class DataProcessor:
    """Processes raw orderbook data into usable metrics"""
    
    def __init__(self, history_size: int = 100):
        """
        Initialize data processor
        
        Args:
            history_size: Number of historical orderbooks to keep
        """
        self.orderbook_history = deque(maxlen=history_size)
        self.price_history = deque(maxlen=history_size)
        self.metrics_history = deque(maxlen=history_size)
        self.current_orderbook: Optional[OrderBook] = None
        self.logger = logging.getLogger(__name__)
    
    def process_orderbook(self, orderbook: OrderBook) -> MarketMetrics:
        """
        Process a new orderbook update
        
        Args:
            orderbook: New orderbook data
            
        Returns:
            MarketMetrics: Calculated market metrics
        """
        self.logger.debug(f"Processing orderbook: {orderbook}")
        
        # Store the orderbook
        self.current_orderbook = orderbook
        self.orderbook_history.append(orderbook)
        
        # Extract price and add to history
        mid_price = orderbook.mid_price()
        self.price_history.append((orderbook.timestamp, mid_price))
        
        # Calculate depths
        bid_depth = sum(level.quantity for level in orderbook.bids)
        ask_depth = sum(level.quantity for level in orderbook.asks)
        
        # Calculate short-term volatility if we have enough data
        volatility = 0.0
        if len(self.price_history) >= 2:
            # Simple volatility calculation based on recent price changes
            # In a real system, you'd use a more sophisticated method
            price_changes = []
            prev_price = None
            for _, price in self.price_history:
                if prev_price is not None:
                    price_changes.append(abs(price - prev_price) / prev_price)
                prev_price = price
            
            if price_changes:
                volatility = sum(price_changes) / len(price_changes) * 100  # As percentage
        
        # Create market metrics
        metrics = MarketMetrics(
            timestamp=orderbook.timestamp,
            symbol=orderbook.symbol,
            mid_price=mid_price,
            spread=orderbook.spread(),
            bid_depth=bid_depth,
            ask_depth=ask_depth,
            volatility=volatility
        )
        
        self.metrics_history.append(metrics)
        self.logger.debug(f"Calculated metrics: {metrics}")
        
        return metrics
    
    def get_current_metrics(self) -> Optional[MarketMetrics]:
        """
        Get the most recent market metrics
        
        Returns:
            MarketMetrics or None: Latest market metrics if available
        """
        if not self.metrics_history:
            return None
        return self.metrics_history[-1]
    
    def get_current_orderbook(self) -> Optional[OrderBook]:
        """
        Get the most recent orderbook
        
        Returns:
            OrderBook or None: Latest orderbook if available
        """
        return self.current_orderbook