"""
WebSocket client for connecting to market data streams
"""

import json
import time
import random
import logging
import asyncio
import websockets
from typing import Optional, Callable, Dict, Any
from websockets.exceptions import ConnectionClosed

from config import (
    WEBSOCKET_URL, 
    WEBSOCKET_PING_INTERVAL, 
    WEBSOCKET_RECONNECT_DELAY,
    WEBSOCKET_MAX_RECONNECT_ATTEMPTS,
    WEBSOCKET_BACKOFF_FACTOR
)
from data.market_data import OrderBook
from utils.performance import measure_latency

class WebSocketHealthMonitor:
    """Monitor health of websocket connections"""
    
    def __init__(self, check_interval: float = 5.0):
        """
        Initialize health monitor
        
        Args:
            check_interval: Interval in seconds between checks
        """
        self.logger = logging.getLogger(__name__)
        self.check_interval = check_interval
        self.connections = {}
        self.running = True
        
    def register_connection(self, connection_id: str, client: 'WebSocketClient') -> None:
        """
        Register a connection to monitor
        
        Args:
            connection_id: Connection identifier
            client: WebSocket client to monitor
        """
        self.connections[connection_id] = {
            "client": client,
            "last_check": time.time(),
            "status": "connected" if client.is_connected else "disconnected"
        }
        self.logger.info(f"Registered connection {connection_id} for monitoring")
        
    def unregister_connection(self, connection_id: str) -> None:
        """
        Unregister a connection
        
        Args:
            connection_id: Connection identifier
        """
        if connection_id in self.connections:
            del self.connections[connection_id]
            self.logger.info(f"Unregistered connection {connection_id}")
            
    async def monitor_loop(self) -> None:
        """Monitor connections and take action if needed"""
        self.logger.info("Starting WebSocket health monitor")
        
        while self.running:
            now = time.time()
            
            for conn_id, conn_info in list(self.connections.items()):
                try:
                    client = conn_info["client"]
                    
                    # Check if it's time to check this connection
                    if now - conn_info["last_check"] >= self.check_interval:
                        self.connections[conn_id]["last_check"] = now
                        
                        # Check connection status
                        if client.is_connected:
                            # Check if we've received messages recently
                            if now - client.last_message_time > self.check_interval * 2:
                                self.logger.warning(
                                    f"Connection {conn_id} hasn't received messages for "
                                    f"{now - client.last_message_time:.1f} seconds"
                                )
                                
                                # If it's been too long, trigger reconnection
                                if now - client.last_message_time > self.check_interval * 4:
                                    self.logger.warning(f"Triggering reconnection for {conn_id}")
                                    client.is_connected = False
                        else:
                            self.logger.info(f"Connection {conn_id} is disconnected")
                            
                        # Update status
                        self.connections[conn_id]["status"] = (
                            "connected" if client.is_connected else "disconnected"
                        )
                except Exception as e:
                    self.logger.error(f"Error monitoring connection {conn_id}: {e}")
            
            # Sleep until next check
            await asyncio.sleep(1.0)
            
    def get_status(self) -> Dict[str, Any]:
        """
        Get status of all monitored connections
        
        Returns:
            Dict[str, Any]: Connection statuses
        """
        now = time.time()
        
        return {
            conn_id: {
                "status": info["status"],
                "last_check": now - info["last_check"],
                "connected": info["client"].is_connected,
                "last_message": now - info["client"].last_message_time
            }
            for conn_id, info in self.connections.items()
        }
    
    def stop(self) -> None:
        """Stop the health monitor"""
        self.logger.info("Stopping WebSocket health monitor")
        self.running = False

# Global health monitor instance
health_monitor = WebSocketHealthMonitor()

class WebSocketClient:
    """Enhanced client for WebSocket market data connections"""
    
    def __init__(self, symbol: str, on_message_callback: Optional[Callable] = None,
                connection_id: Optional[str] = None):
        """
        Initialize WebSocket client
        
        Args:
            symbol: Trading symbol (e.g., "BTC-USDT-SWAP")
            on_message_callback: Optional callback function for received messages
            connection_id: Optional connection identifier for monitoring
        """
        self.symbol = symbol
        self.url = WEBSOCKET_URL.format(symbol=symbol)
        self.on_message_callback = on_message_callback
        self.connection_id = connection_id or f"{symbol}_{int(time.time())}"
        
        self.ws = None
        self.is_connected = False
        self.reconnect_attempts = 0
        self.backoff_time = WEBSOCKET_RECONNECT_DELAY
        self.last_message_time = 0
        self.messages_received = 0
        self.connection_start_time = 0
        self.logger = logging.getLogger(__name__)
        
        # Error tracking
        self.connection_errors = []
        self.message_errors = []
        
        # Register with health monitor
        health_monitor.register_connection(self.connection_id, self)
        
    async def connect(self) -> bool:
        """
        Establish connection to WebSocket server
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        self.logger.info(f"Connecting to {self.url}")
        
        try:
            # Add more debugging information
            self.logger.info("Initiating WebSocket connection...")
            
            # Use more robust connection parameters
            self.ws = await websockets.connect(
                self.url,
                ping_interval=None,  # Disable automatic ping
                close_timeout=10,
                max_size=None,
                compression=None,
                extra_headers={
                    "User-Agent": "CryptoTradeSimulator/1.0"
                }
            )
            
            self.is_connected = True
            self.reconnect_attempts = 0
            self.backoff_time = WEBSOCKET_RECONNECT_DELAY
            self.last_message_time = time.time()
            self.connection_start_time = time.time()
            self.logger.info("WebSocket connection established")
            
            # Try to send a subscription message
            await self.subscribe()
            return True
        except Exception as e:
            self.logger.error(f"WebSocket connection failed: {str(e)}")
            self.is_connected = False
            
            # Track error
            self.connection_errors.append({
                "time": time.time(),
                "error": str(e),
                "attempt": self.reconnect_attempts
            })
            
            # Keep error list manageable
            if len(self.connection_errors) > 10:
                self.connection_errors.pop(0)
                
            return False
    
    async def subscribe(self) -> None:
        """Send subscription message to the WebSocket server"""
        try:
            # This is an example subscription message - adjust based on OKX API docs
            subscription = {
                "op": "subscribe",
                "args": [{
                    "channel": "books",
                    "instId": self.symbol
                }]
            }
            
            self.logger.info(f"Sending subscription: {json.dumps(subscription)}")
            await self.ws.send(json.dumps(subscription))
            self.logger.info("Subscription request sent")
        except Exception as e:
            self.logger.error(f"Failed to send subscription: {str(e)}")
    
    async def disconnect(self) -> None:
        """Close WebSocket connection"""
        if self.ws and self.is_connected:
            self.logger.info("Closing WebSocket connection")
            await self.ws.close()
            self.is_connected = False
    
    async def reconnect(self) -> bool:
        """
        Attempt to reconnect to WebSocket server
        
        Returns:
            bool: True if reconnection successful, False otherwise
        """
        self.reconnect_attempts += 1
        if self.reconnect_attempts > WEBSOCKET_MAX_RECONNECT_ATTEMPTS:
            self.logger.error("Maximum reconnection attempts reached")
            return False
        
        # Exponential backoff with jitter
        jitter = random.uniform(0.8, 1.2)
        backoff = min(60.0, self.backoff_time * (WEBSOCKET_BACKOFF_FACTOR ** (self.reconnect_attempts - 1)))
        wait_time = backoff * jitter
        
        self.logger.info(f"Reconnection attempt {self.reconnect_attempts}, waiting {wait_time:.1f}s...")
        await asyncio.sleep(wait_time)
        
        return await self.connect()
    
    @measure_latency("websocket_message_processing")
    async def _process_message(self, message: str) -> None:
        """
        Process a received WebSocket message
        
        Args:
            message: Raw message string
        """
        try:
            # Parse JSON first to see what kind of message it is
            data = json.loads(message)
            
            # Check if this is a subscription confirmation or other control message
            if "event" in data:
                self.logger.info(f"Received control message: {data}")
                return
            
            # Create OrderBook object from message
            orderbook = OrderBook.from_json(message)
            
            # Call the callback if provided
            if self.on_message_callback:
                self.on_message_callback(orderbook)
            else:
                # Just log for now during initial development
                self.logger.debug(f"Received orderbook: {orderbook}")
                
            # Update message count
            self.messages_received += 1
                
        except json.JSONDecodeError:
            self.logger.warning(f"Invalid JSON: {message[:200]}...")
            self._track_message_error("json_decode", message[:100])
        except KeyError as e:
            self.logger.warning(f"Missing key in message: {e} - {message[:200]}...")
            self._track_message_error("missing_key", str(e))
        except Exception as e:
            self.logger.error(f"Error processing message: {str(e)} - {message[:200]}...")
            self._track_message_error("processing", str(e))
    
    def _track_message_error(self, error_type: str, details: str) -> None:
        """
        Track a message processing error
        
        Args:
            error_type: Type of error
            details: Error details
        """
        self.message_errors.append({
            "time": time.time(),
            "type": error_type,
            "details": details
        })
        
        # Keep error list manageable
        if len(self.message_errors) > 100:
            self.message_errors.pop(0)
    
    async def receive_messages(self) -> None:
        """Receive and process messages from WebSocket"""
        if not self.ws or not self.is_connected:
            self.logger.error("WebSocket not connected")
            return
        
        try:
            self.logger.info("Starting to receive messages...")
            async for message in self.ws:
                self.last_message_time = time.time()
                self.logger.debug(f"Raw message received: {message[:100]}...")
                
                # Process the message
                await self._process_message(message)
        
        except ConnectionClosed as e:
            self.logger.warning(f"WebSocket connection closed: {str(e)}")
            self.is_connected = False
        except Exception as e:
            self.logger.error(f"Error in receive_messages: {str(e)}")
            self.is_connected = False
    
    async def ping_loop(self) -> None:
        """Send periodic pings to keep connection alive"""
        while self.is_connected:
            await asyncio.sleep(WEBSOCKET_PING_INTERVAL)
            
            # Check if connection is stale
            if time.time() - self.last_message_time > WEBSOCKET_PING_INTERVAL * 2:
                self.logger.warning("Connection seems stale, attempting to reconnect")
                self.is_connected = False
                if not await self.reconnect():
                    break
            
            # Send ping if connection is active
            if self.is_connected:
                try:
                    self.logger.debug("Sending ping")
                    # Use a custom ping message instead of WebSocket ping frame
                    ping_message = {"op": "ping"}
                    await self.ws.send(json.dumps(ping_message))
                    self.logger.debug("Ping sent")
                except Exception as e:
                    self.logger.warning(f"Ping failed: {str(e)}")
                    self.is_connected = False
                    if not await self.reconnect():
                        break
    
    async def connect_and_receive(self) -> None:
        """Connect to WebSocket and start receiving messages"""
        if await self.connect():
            # Start ping task
            ping_task = asyncio.create_task(self.ping_loop())
            
            # Start receiving messages
            try:
                await self.receive_messages()
            except Exception as e:
                self.logger.error(f"Unexpected error in connect_and_receive: {str(e)}")
            finally:
                # Cancel ping task when receive_messages exits
                ping_task.cancel()
                try:
                    await self.disconnect()
                except Exception as e:
                    self.logger.error(f"Error during disconnect: {str(e)}")
                    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get connection statistics
        
        Returns:
            Dict[str, Any]: Connection statistics
        """
        now = time.time()
        uptime = now - self.connection_start_time if self.is_connected else 0
        
        return {
            "connection_id": self.connection_id,
            "symbol": self.symbol,
            "connected": self.is_connected,
            "reconnect_attempts": self.reconnect_attempts,
            "messages_received": self.messages_received,
            "messages_per_second": self.messages_received / uptime if uptime > 0 else 0,
            "uptime": uptime,
            "last_message": now - self.last_message_time,
            "connection_errors": len(self.connection_errors),
            "message_errors": len(self.message_errors)
        }