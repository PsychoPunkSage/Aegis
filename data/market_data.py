"""
Market data structures for the Crypto Trade Simulator
"""
from dataclasses import dataclass, field
from typing import Dict, List, Tuple
from datetime import datetime
import json

@dataclass
class OrderBookLevel:
    """Represents a single level in the order book"""
    price: float
    quantity: float
    
    @classmethod
    def from_list(cls, data: List) -> 'OrderBookLevel':
        """Create from [price, quantity] list"""
        return cls(float(data[0]), float(data[1]))
    
    def __repr__(self) -> str:
        return f"Level(price={self.price:.2f}, qty={self.quantity:.4f})"

@dataclass
class OrderBook:
    """Represents a full L2 order book"""
    timestamp: datetime
    exchange: str
    symbol: str
    asks: List[OrderBookLevel] = field(default_factory=list)
    bids: List[OrderBookLevel] = field(default_factory=list)
    
    @classmethod
    def from_json(cls, json_data: str) -> 'OrderBook':
        """Create OrderBook from JSON string"""
        data = json.loads(json_data)
        
        # Convert timestamp string to datetime
        timestamp = datetime.fromisoformat(data["timestamp"].replace('Z', '+00:00'))
        
        # Create OrderBook instance
        orderbook = cls(
            timestamp=timestamp,
            exchange=data["exchange"],
            symbol=data["symbol"]
        )
        
        # Add ask levels
        for ask_data in data["asks"]:
            orderbook.asks.append(OrderBookLevel.from_list(ask_data))
            
        # Add bid levels
        for bid_data in data["bids"]:
            orderbook.bids.append(OrderBookLevel.from_list(bid_data))
            
        return orderbook
    
    def best_ask(self) -> float:
        """Return the best (lowest) ask price"""
        if not self.asks:
            return float('inf')
        return self.asks[0].price
    
    def best_bid(self) -> float:
        """Return the best (highest) bid price"""
        if not self.bids:
            return 0.0
        return self.bids[0].price
    
    def mid_price(self) -> float:
        """Return the mid price between best bid and ask"""
        return (self.best_ask() + self.best_bid()) / 2
    
    def spread(self) -> float:
        """Return the bid-ask spread"""
        return self.best_ask() - self.best_bid()
    
    def depth_at_price(self, price: float, side: str) -> float:
        """Return the total quantity available at a given price level"""
        if side.lower() == 'ask':
            levels = [level for level in self.asks if level.price <= price]
        else:  # bid side
            levels = [level for level in self.bids if level.price >= price]
            
        return sum(level.quantity for level in levels)
    
    def __repr__(self) -> str:
        return (
            f"OrderBook(exchange={self.exchange}, symbol={self.symbol}, "
            f"timestamp={self.timestamp.isoformat()}, "
            f"best_bid={self.best_bid():.2f}, best_ask={self.best_ask():.2f}, "
            f"mid={self.mid_price():.2f}, spread={self.spread():.2f})"
        )

@dataclass
class MarketMetrics:
    """Calculated market metrics from order book data"""
    timestamp: datetime
    symbol: str
    mid_price: float
    spread: float
    bid_depth: float  # Total quantity on bid side
    ask_depth: float  # Total quantity on ask side
    volatility: float = 0.0  # Short-term price volatility estimate
    
    def __repr__(self) -> str:
        return (
            f"MarketMetrics(symbol={self.symbol}, mid={self.mid_price:.2f}, "
            f"spread={self.spread:.2f}, vol={self.volatility:.4f})"
        )