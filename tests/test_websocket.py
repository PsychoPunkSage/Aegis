"""
Tests for the WebSocket client
"""
import asyncio
import json
import unittest
from datetime import datetime

from services.websocket_client import WebSocketClient
from data.market_data import OrderBook, OrderBookLevel

class TestWebSocketClient(unittest.TestCase):
    """Tests for the WebSocket client"""
    
    def test_orderbook_creation(self):
        """Test creating an OrderBook from JSON data"""
        # Sample orderbook data
        sample_data = {
            "timestamp": "2025-05-04T10:39:13Z",
            "exchange": "OKX",
            "symbol": "BTC-USDT-SWAP",
            "asks": [
                ["95445.5", "9.06"],
                ["95448", "2.05"]
            ],
            "bids": [
                ["95445.4", "1104.23"],
                ["95445.3", "0.02"]
            ]
        }
        
        # Convert to JSON string
        json_data = json.dumps(sample_data)
        
        # Create OrderBook from JSON
        orderbook = OrderBook.from_json(json_data)
        
        # Verify orderbook properties
        self.assertEqual(orderbook.exchange, "OKX")
        self.assertEqual(orderbook.symbol, "BTC-USDT-SWAP")
        self.assertEqual(len(orderbook.asks), 2)
        self.assertEqual(len(orderbook.bids), 2)
        
        # Verify ask levels
        self.assertAlmostEqual(orderbook.asks[0].price, 95445.5)
        self.assertAlmostEqual(orderbook.asks[0].quantity, 9.06)
        
        # Verify bid levels
        self.assertAlmostEqual(orderbook.bids[0].price, 95445.4)
        self.assertAlmostEqual(orderbook.bids[0].quantity, 1104.23)
        
        # Verify calculated values
        self.assertAlmostEqual(orderbook.best_ask(), 95445.5)
        self.assertAlmostEqual(orderbook.best_bid(), 95445.4)
        self.assertAlmostEqual(orderbook.mid_price(), 95445.45)
        self.assertAlmostEqual(orderbook.spread(), 0.1)

if __name__ == "__main__":
    unittest.main()