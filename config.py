"""
Configuration settings for the Crypto Trade Simulator
"""

# WebSocket Configuration
WEBSOCKET_URL = "wss://ws.gomarket-cpp.goquant.io/ws/l2-orderbook/okx/{symbol}"
WEBSOCKET_PING_INTERVAL = 10  # seconds
WEBSOCKET_RECONNECT_DELAY = 5  # seconds
WEBSOCKET_MAX_RECONNECT_ATTEMPTS = 5

# Data Processing Configuration
ORDERBOOK_DEPTH = 20  # Number of price levels to maintain
PROCESSING_BATCH_SIZE = 10  # Number of updates to process in one batch

# Logging Configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = "aegis.log"

# Performance Monitoring
ENABLE_PERFORMANCE_MONITORING = True
LATENCY_SAMPLE_RATE = 100  # Measure latency every N messages