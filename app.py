"""
Aegis: Crypto Trade Simulator - Main Application Entry Point
"""

# import asyncio
# import logging
# from services.websocket_client import WebSocketClient
# from utils.logging_setup import setup_logging
# import sys

# def main():
#     """Main application entry point"""
#     # Setup logging
#     setup_logging()
#     logger = logging.getLogger(__name__)
#     logger.info("Starting Crypto Trade Simulator")
    
#     # Print Python version for debugging
#     logger.info(f"Python version: {sys.version}")
    
#     # Create and start WebSocket client
#     symbol = "BTC-USDT-SWAP"
#     logger.info(f"Initializing WebSocket client for symbol: {symbol}")
#     client = WebSocketClient(symbol)
    
#     try:
#         # Start the WebSocket client in a simple synchronous way for testing
#         logger.info("Starting WebSocket client...")
#         asyncio.run(client.connect_and_receive())
#     except KeyboardInterrupt:
#         logger.info("Application terminated by user")
#     except Exception as e:
#         logger.error(f"Application error: {str(e)}", exc_info=True)
    
#     logger.info("Crypto Trade Simulator shutting down")

# if __name__ == "__main__":
#     main()

#!/usr/bin/env python3
"""
Crypto Trade Simulator - Main Application Entry Point
Day 2: Model implementation and basic UI
"""

import asyncio
import logging
import threading
import time
import tkinter as tk
from enum import Enum
from typing import Dict, Any, Optional, List

from services.websocket_client import WebSocketClient
from services.data_processor import DataProcessor
from services.simulator import TradeSimulator
from ui.main_window import MainWindow
from utils.logging_setup import setup_logging

class AppState:
    """Application state object for sharing between threads"""
    
    def __init__(self):
        """Initialize application state"""
        self.running = True
        self.latest_orderbook = None
        self.latest_metrics = None
        self.ui_update_count = 0
        
def update_ui(app_state, ui, simulator, update_interval=0.5):
    """
    Update UI with latest data
    
    This runs in a separate thread to keep the UI responsive
    
    Args:
        app_state: Application state object
        ui: MainWindow instance
        simulator: TradeSimulator instance
        update_interval: Update interval in seconds
    """
    logger = logging.getLogger(__name__)
    logger.info("Starting UI update thread")
    
    while app_state.running:
        try:
            if app_state.latest_orderbook and app_state.latest_metrics:
                # Update market data on UI
                # Only update UI every 5th update to avoid overwhelming the UI thread
                app_state.ui_update_count += 1
                if app_state.ui_update_count % 5 == 0:
                    # Extract top orderbook levels
                    orderbook = app_state.latest_orderbook
                    metrics = app_state.latest_metrics
                    
                    # Prepare summary data for UI
                    orderbook_summary = {
                        "symbol": orderbook.symbol,
                        "mid_price": orderbook.mid_price(),
                        "spread": orderbook.spread(),
                        "volatility": metrics.volatility,
                        "bid_depth": metrics.bid_depth,
                        "ask_depth": metrics.ask_depth,
                        "bids": [
                            {"price": level.price, "quantity": level.quantity}
                            for level in orderbook.bids[:5]
                        ],
                        "asks": [
                            {"price": level.price, "quantity": level.quantity}
                            for level in orderbook.asks[:5]
                        ]
                    }
                    
                    # Update UI from the main thread
                    ui.root.after(0, ui.update_market_data, orderbook_summary)
                    
                    # Log performance metrics occasionally
                    if app_state.ui_update_count % 50 == 0:
                        perf_metrics = simulator.get_performance_metrics()
                        logger.info(f"Performance metrics: {perf_metrics}")
                        
            # Wait a bit to avoid using too much CPU
            time.sleep(update_interval)
        except Exception as e:
            logger.error(f"Error in UI update thread: {e}", exc_info=True)
            time.sleep(update_interval)
            
def on_orderbook_update(orderbook, app_state, data_processor, simulator):
    """
    Process orderbook update
    
    Args:
        orderbook: New orderbook data
        app_state: Application state object
        data_processor: DataProcessor instance
        simulator: TradeSimulator instance
    """
    # Process the orderbook
    metrics = data_processor.process_orderbook(orderbook)
    
    # Update application state
    app_state.latest_orderbook = orderbook
    app_state.latest_metrics = metrics
    
    # Update simulator with new market data
    simulator.update_market_data(orderbook, metrics)
    
def on_simulation_request(params, app_state, simulator, ui):
    """
    Handle simulation request from UI
    
    Args:
        params: Simulation parameters
        app_state: Application state object
        simulator: TradeSimulator instance
        ui: MainWindow instance
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Running simulation with params: {params}")
    
    # Run simulation
    results = simulator.simulate_trade(params)
    
    # Update UI with results
    ui.root.after(0, ui.update_simulation_results, results)

def main():
    """Main application entry point"""
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting Crypto Trade Simulator - Day 2")
    
    # Create application state
    app_state = AppState()
    
    # Create data processor
    data_processor = DataProcessor()
    
    # Create simulator
    simulator = TradeSimulator()
    
    # Create UI
    ui = MainWindow(
        on_simulation_request=lambda params: on_simulation_request(params, app_state, simulator, ui)
    )
    
    # Setup WebSocket client callback
    def orderbook_callback(orderbook):
        on_orderbook_update(orderbook, app_state, data_processor, simulator)
    
    # Create and start WebSocket client
    symbol = "BTC-USDT-SWAP"
    client = WebSocketClient(symbol, on_message_callback=orderbook_callback)
    
    # Start UI update thread
    ui_thread = threading.Thread(
        target=update_ui,
        args=(app_state, ui, simulator),
        daemon=True
    )
    ui_thread.start()
    
    # Start WebSocket client in a separate thread
    websocket_thread = threading.Thread(
        target=lambda: asyncio.run(client.connect_and_receive()),
        daemon=True
    )
    websocket_thread.start()
    
    try:
        # Run UI main loop (blocks until UI is closed)
        ui.run()
    except KeyboardInterrupt:
        logger.info("Application terminated by user")
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
    finally:
        # Cleanup
        app_state.running = False
        ui.stop()
        logger.info("Crypto Trade Simulator shutting down")

if __name__ == "__main__":
    main()