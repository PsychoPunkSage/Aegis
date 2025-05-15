"""
Aegis: Crypto Trade Simulator - Main Application Entry Point
"""

import asyncio
import logging
from services.websocket_client import WebSocketClient
from utils.logging_setup import setup_logging
import sys

def main():
    """Main application entry point"""
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting Crypto Trade Simulator")
    
    # Print Python version for debugging
    logger.info(f"Python version: {sys.version}")
    
    # Create and start WebSocket client
    symbol = "BTC-USDT-SWAP"
    logger.info(f"Initializing WebSocket client for symbol: {symbol}")
    client = WebSocketClient(symbol)
    
    try:
        # Start the WebSocket client in a simple synchronous way for testing
        logger.info("Starting WebSocket client...")
        asyncio.run(client.connect_and_receive())
    except KeyboardInterrupt:
        logger.info("Application terminated by user")
    except Exception as e:
        logger.error(f"Application error: {str(e)}", exc_info=True)
    
    logger.info("Crypto Trade Simulator shutting down")

if __name__ == "__main__":
    main()