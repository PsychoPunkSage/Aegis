# """
# Configuration settings for the Crypto Trade Simulator
# """

# # WebSocket Configuration
# WEBSOCKET_URL = "wss://ws.gomarket-cpp.goquant.io/ws/l2-orderbook/okx/{symbol}"
# WEBSOCKET_PING_INTERVAL = 10  # seconds
# WEBSOCKET_RECONNECT_DELAY = 5  # seconds
# WEBSOCKET_MAX_RECONNECT_ATTEMPTS = 5

# # Data Processing Configuration
# ORDERBOOK_DEPTH = 20  # Number of price levels to maintain
# PROCESSING_BATCH_SIZE = 10  # Number of updates to process in one batch

# # Logging Configuration
# LOG_LEVEL = "INFO"
# LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
# LOG_FILE = "aegis.log"

# # Performance Monitoring
# ENABLE_PERFORMANCE_MONITORING = True
# LATENCY_SAMPLE_RATE = 100  # Measure latency every N messages

"""
Enhanced configuration settings for the Crypto Trade Simulator
"""

# WebSocket Configuration
WEBSOCKET_URL = "wss://ws.gomarket-cpp.goquant.io/ws/l2-orderbook/okx/{symbol}"
WEBSOCKET_PING_INTERVAL = 30  # seconds
WEBSOCKET_RECONNECT_DELAY = 5  # seconds
WEBSOCKET_MAX_RECONNECT_ATTEMPTS = 10
WEBSOCKET_BACKOFF_FACTOR = 1.5  # Exponential backoff factor

# Data Processing Configuration
ORDERBOOK_DEPTH = 20  # Number of price levels to maintain
PROCESSING_BATCH_SIZE = 10  # Number of updates to process in one batch
CACHE_SIZE = 1000  # Maximum number of entries in data caches

# Logging Configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = "crypto_simulator.log"
LOG_MAX_SIZE = 10 * 1024 * 1024  # 10 MB
LOG_BACKUP_COUNT = 5  # Number of backup logs to keep

# Performance Monitoring
ENABLE_PERFORMANCE_MONITORING = True
LATENCY_SAMPLE_RATE = 100  # Measure latency every N messages
STATS_REPORTING_INTERVAL = 300  # seconds

# Simulation Configuration
DEFAULT_VOLATILITY = 2.5  # Default volatility in percentage
DEFAULT_FEE_TIER = "TIER1"
DEFAULT_SYMBOL = "BTC-USDT-SWAP"
MAX_BATCH_SIZE = 1000  # Maximum number of simulations in a batch
SIMULATION_WORKERS = 4  # Number of worker threads for simulations

# Markets Configuration
SUPPORTED_EXCHANGES = ["OKX"]
SUPPORTED_SYMBOLS = ["BTC-USDT-SWAP", "ETH-USDT-SWAP", "BTC-USDT", "ETH-USDT"]
MARKET_OPEN_HOURS = 24  # Crypto markets are 24/7

# UI Configuration
UI_UPDATE_INTERVAL = 0.5  # seconds
UI_MAX_HISTORY = 100  # Maximum number of data points in charts