"""
Aegis: Crypto Trade Simulator - Main Application Entry Point
"""
import asyncio
import logging
import threading
import time
import tkinter as tk
import signal
import sys
from typing import Dict, Any, Optional, List
from datetime import datetime

from services.websocket_client import WebSocketClient, health_monitor
from services.data_processor import DataProcessor
from services.simulator import TradeSimulator, OrderType, TradeSide, SimulationMode
from ui.main_window import MainWindow
from models.market_impact import ImpactModelType
from utils.logging_setup import setup_logging
from config import (
    DEFAULT_SYMBOL,
    SUPPORTED_EXCHANGES,
    SUPPORTED_SYMBOLS,
    UI_UPDATE_INTERVAL,
    STATS_REPORTING_INTERVAL
)

class AppState:
    """Application state object for sharing between threads"""
    
    def __init__(self):
        """Initialize application state"""
        self.running = True
        self.latest_orderbook = None
        self.latest_metrics = None
        self.ui_update_count = 0
        self.performance_stats = {}
        self.connection_stats = {}
        self.error_log = []
        self.start_time = time.time()
        self.active_symbols = []
        
def update_ui(app_state, ui, simulator, clients, update_interval=0.5):
    """
    Update UI with latest data
    
    This runs in a separate thread to keep the UI responsive
    
    Args:
        app_state: Application state object
        ui: MainWindow instance
        simulator: TradeSimulator instance
        clients: List of WebSocket clients
        update_interval: Update interval in seconds
    """
    logger = logging.getLogger(__name__)
    logger.info("Starting UI update thread")
    
    while app_state.running:
        try:
            if app_state.latest_orderbook and app_state.latest_metrics:
                # Update market data on UI
                # Updating UI every 5th update to avoid overwhelming the UI thread.
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
                    if app_state.ui_update_count % 10 == 0:
                        # Get simulator performance metrics
                        perf_metrics = simulator.get_performance_metrics()
                        
                        # Add system stats
                        perf_metrics["uptime"] = time.time() - app_state.start_time

                        # Add these critical missing fields
                        perf_metrics["active_symbols"] = app_state.active_symbols if hasattr(app_state, 'active_symbols') else []
                        perf_metrics["error_count"] = len(app_state.error_log) if hasattr(app_state, 'error_log') else 0

                        # Get simulator threads - add the attribute to simulator if it doesn't exist
                        if hasattr(simulator, 'max_workers'):
                            perf_metrics["simulator_threads"] = simulator.max_workers
                        else:
                            perf_metrics["simulator_threads"] = 1  # Default value

                        # Update connection stats for dashboard
                        connection_stats = {}
                        for client in clients:
                            connection_stats[client.connection_id] = client.get_stats() 
                        
                        # Update app state with performance metrics
                        app_state.performance_stats = perf_metrics
                        
                        # Update UI with performance metrics
                        ui.root.after(0, ui.update_performance_metrics, perf_metrics)
                        ui.root.after(0, ui.update_connection_stats, connection_stats)
                        ui.root.after(0, ui.update_error_log, app_state.error_log)
                        
                        # Log metrics
                        logger.info(f"Performance metrics: active_symbols={len(perf_metrics.get('active_symbols', []))}, "
                                    f"errors={perf_metrics.get('error_count', 0)}, "
                                    f"threads={perf_metrics.get('simulator_threads', 1)}")
            # Wait a bit to avoid using too much CPU
            time.sleep(update_interval)
        except Exception as e:
            logger.error(f"Error in UI update thread: {e}", exc_info=True)
            
            # Track error
            app_state.error_log.append({
                "time": datetime.now().isoformat(),
                "source": "ui_update",
                "error": str(e)
            })
            
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
    try:
        # Process the orderbook
        metrics = data_processor.process_orderbook(orderbook)
        
        # Update application state
        app_state.latest_orderbook = orderbook
        app_state.latest_metrics = metrics

        # Add symbol to active symbols if not already there
        if not hasattr(app_state, 'active_symbols'):
            app_state.active_symbols = []
        
        # Make sure the symbol is in active symbols
        if orderbook.symbol not in app_state.active_symbols:
            app_state.active_symbols.append(orderbook.symbol)
        
        # Update simulator with new market data
        simulator.update_market_data(orderbook, metrics)
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Error in orderbook update: {e}", exc_info=True)
        
        # Track error
        app_state.error_log.append({
            "time": datetime.now().isoformat(),
            "source": "orderbook_update",
            "error": str(e)
        })
    
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
    
    try:
        logger.info(f"Running simulation with params: {params}")
        
        # Check if this is a batch simulation
        if params.get("batch_mode", False):
            # Create parameter variations
            base_params = {
                "exchange": params.get("exchange", "OKX"),
                "symbol": params.get("symbol", DEFAULT_SYMBOL),
                "order_type": params.get("order_type", "market"),
                "side": params.get("side", "buy"),
                "fee_tier": params.get("fee_tier", "TIER1"),
                "volatility": params.get("volatility", None)
            }
            
            # Get variations
            variations = []
            
            # Quantity variations
            if params.get("quantity_variations", False):
                qty = params.get("quantity", 0.1)
                qty_range = [qty * 0.1, qty * 0.5, qty, qty * 2, qty * 5, qty * 10]
                variations.extend([{"quantity": q} for q in qty_range])
            
            # Volatility variations
            if params.get("volatility_variations", False):
                vol = params.get("volatility", 2.5)
                vol_range = [vol * 0.5, vol, vol * 2, vol * 5]
                variations.extend([{"volatility": v} for v in vol_range])
                
            # Impact model variations
            if params.get("model_variations", False):
                model_types = [model_type.value for model_type in ImpactModelType]
                variations.extend([{"impact_model": m} for m in model_types])
                
            # Order type variations
            if params.get("order_type_variations", False):
                order_types = ["market", "limit"]
                variations.extend([{"order_type": ot} for ot in order_types])
                
            # If no variations specified, use a default set
            if not variations:
                qty = params.get("quantity", 0.1)
                variations = [
                    {"quantity": qty * 0.5},
                    {"quantity": qty},
                    {"quantity": qty * 2}
                ]
                
            # Start batch simulation
            batch_id = simulator.start_batch_simulation(base_params, variations)
            
            # Update UI with batch ID
            ui.root.after(0, ui.update_batch_status, {
                "batch_id": batch_id,
                "status": "running",
                "variations": len(variations)
            })
            
            # Poll for results
            def check_batch_results():
                if not simulator.is_batch_running():
                    results = simulator.get_batch_results()
                    if results and results.get("batch_id") == batch_id:
                        # Update UI with batch results
                        ui.root.after(0, ui.update_batch_results, results)
                    else:
                        # No results yet, check again later
                        ui.root.after(500, check_batch_results)
                else:
                    # Still running, check again later
                    ui.root.after(500, check_batch_results)
                    
            # Start polling
            ui.root.after(1000, check_batch_results)
                    
        else:
            # Single simulation
            results = simulator.simulate_trade(params)
            
            # Update UI with results
            ui.root.after(0, ui.update_simulation_results, results)
    except Exception as e:
        logger.error(f"Error in simulation request: {e}", exc_info=True)
        
        # Track error
        app_state.error_log.append({
            "time": datetime.now().isoformat(),
            "source": "simulation_request",
            "error": str(e)
        })
        
        # Update UI with error
        ui.root.after(0, ui.update_status, f"Simulation error: {e}")

def stats_reporter(app_state, clients, simulator, interval=STATS_REPORTING_INTERVAL):
    """
    Report system statistics periodically
    
    Args:
        app_state: Application state object
        clients: List of WebSocket clients
        simulator: TradeSimulator instance
        interval: Reporting interval in seconds
    """
    logger = logging.getLogger(__name__)
    
    while app_state.running:
        try:
            # Wait for the interval
            time.sleep(interval)
            
            # Collect stats
            now = time.time()
            uptime = now - app_state.start_time
            
            # WebSocket stats
            connection_stats = {}
            for client in clients:
                connection_stats[client.connection_id] = client.get_stats()
                
            # Update app state
            app_state.connection_stats = connection_stats
            
            # Log summary
            active_connections = sum(1 for stats in connection_stats.values() if stats["connected"])
            total_messages = sum(stats["messages_received"] for stats in connection_stats.values())
            
            logger.info(
                f"System stats: uptime={uptime:.1f}s, "
                f"active_connections={active_connections}/{len(clients)}, "
                f"total_messages={total_messages}, "
                f"active_symbols={len(app_state.active_symbols)}"
            )
            
            # Get health monitor status
            health_status = health_monitor.get_status()
            
            # Log any issues
            for conn_id, status in health_status.items():
                if status["status"] == "disconnected":
                    logger.warning(f"Connection {conn_id} is disconnected")
                elif status["last_message"] > 60:
                    logger.warning(f"Connection {conn_id} hasn't received messages for {status['last_message']:.1f}s")
        except Exception as e:
            logger.error(f"Error in stats reporter: {e}", exc_info=True)
            time.sleep(10)  # Shorter interval after error

def setup_signal_handlers(app_state):
    """
    Set up signal handlers for graceful shutdown
    
    Args:
        app_state: Application state object
    """
    def signal_handler(sig, frame):
        logging.info(f"Received signal {sig}, shutting down...")
        app_state.running = False
        
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

def setup_error_handling():
    """Set up global exception handler"""
    logger = logging.getLogger(__name__)
    
    def global_exception_handler(exc_type, exc_value, exc_traceback):
        """Handle uncaught exceptions"""
        if issubclass(exc_type, KeyboardInterrupt):
            # Let KeyboardInterrupt pass through
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
            
        # Log the exception
        logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
        
    # Set the exception hook
    sys.excepthook = global_exception_handler

def main():
    """Main application entry point"""
    # Setup error handling
    setup_error_handling()

    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting Crypto Trade Simulator - Day 3")
    
    # Create application state
    app_state = AppState()
    app_state.start_time = time.time()
    
    # Set up signal handlers
    setup_signal_handlers(app_state)
    
    # Create data processor
    data_processor = DataProcessor()
    
    # Create simulator with multiple worker threads
    simulator = TradeSimulator(num_threads=4)
    
    # Create UI
    ui = MainWindow(
        on_simulation_request=lambda params: on_simulation_request(params, app_state, simulator, ui)
    )
    
    # Setup WebSocket client callback
    def orderbook_callback(orderbook):
        on_orderbook_update(orderbook, app_state, data_processor, simulator)
    
    # Create and start WebSocket clients for multiple symbols
    clients = []
    for symbol in SUPPORTED_SYMBOLS[:2]:  # Start with just 2 symbols for now
        client = WebSocketClient(
            symbol, 
            on_message_callback=orderbook_callback,
            connection_id=f"main_{symbol}"
        )
        clients.append(client)
    
    # Start UI update thread
    ui_thread = threading.Thread(
        target=update_ui,
        args=(app_state, ui, simulator, clients),
        daemon=True
    )
    ui_thread.start()
    
    # Start stats reporter thread
    stats_thread = threading.Thread(
        target=stats_reporter,
        args=(app_state, clients, simulator),
        daemon=True
    )
    stats_thread.start()
    
    # Start WebSocket clients in separate threads
    websocket_threads = []
    for client in clients:
        thread = threading.Thread(
            target=lambda c=client: asyncio.run(c.connect_and_receive()),
            daemon=True
        )
        thread.start()
        websocket_threads.append(thread)
    
    # Start health monitor
    health_monitor_task = None
    
    async def run_health_monitor():
        await health_monitor.monitor_loop()
    
    def start_health_monitor():
        asyncio.run(run_health_monitor())
    
    health_thread = threading.Thread(
        target=start_health_monitor,
        daemon=True
    )
    health_thread.start()
    
    try:
        # Run UI main loop (blocks until UI is closed)
        ui.run()
    except KeyboardInterrupt:
        logger.info("Application terminated by user")
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
    finally:
        # Cleanup
        logger.info("Shutting down...")
        app_state.running = False
        
        # Stop health monitor
        health_monitor.stop()
        
        # Stop simulator
        simulator.shutdown()
        
        # Stop UI
        ui.stop()
        
        # Log final stats
        for client in clients:
            stats = client.get_stats()
            logger.info(f"Final stats for {client.connection_id}: messages={stats['messages_received']}")
        
        logger.info("Crypto Trade Simulator shutdown complete")

if __name__ == "__main__":
    main()