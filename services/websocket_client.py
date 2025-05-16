"""
WebSocket client for connecting to market data streams
"""
import asyncio
import json
import logging
import time
from typing import Optional, Callable, Dict, Any
import websockets
from websockets.exceptions import ConnectionClosed

from config import (
    WEBSOCKET_URL, 
    WEBSOCKET_PING_INTERVAL, 
    WEBSOCKET_RECONNECT_DELAY,
    WEBSOCKET_MAX_RECONNECT_ATTEMPTS
)
from data.market_data import OrderBook

class WebSocketClient:
    """Client for WebSocket market data connections"""
    
    def __init__(self, symbol: str, on_message_callback: Optional[Callable] = None):
        """
        Initialize WebSocket client
        
        Args:
            symbol: Trading symbol (e.g., "BTC-USDT-SWAP")
            on_message_callback: Optional callback function for received messages
        """
        self.symbol = symbol
        self.url = WEBSOCKET_URL.format(symbol=symbol)
        self.on_message_callback = on_message_callback
        self.ws = None
        self.is_connected = False
        self.reconnect_attempts = 0
        self.last_message_time = 0
        self.logger = logging.getLogger(__name__)
        
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
            self.ws = await websockets.connect(
                self.url,
                ping_interval=None,  # Disable automatic ping
                close_timeout=10,
                max_size=None,
                compression=None
            )
            self.is_connected = True
            self.reconnect_attempts = 0
            self.last_message_time = time.time()
            self.logger.info("WebSocket connection established")
            
            # Try to send a subscription message
            await self.subscribe()
            return True
        except Exception as e:
            self.logger.error(f"WebSocket connection failed: {str(e)}")
            self.is_connected = False
            return False
        
    async def subscribe(self) -> None:
        """Send subscription message to the WebSocket server"""
        try:
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
        
        self.logger.info(f"Reconnection attempt {self.reconnect_attempts}...")
        await asyncio.sleep(WEBSOCKET_RECONNECT_DELAY)
        return await self.connect()
    
    async def receive_messages(self) -> None:
        """Receive and process messages from WebSocket"""
        if not self.ws or not self.is_connected:
            self.logger.error("WebSocket not connected")
            return
        
        try:
            self.logger.info("Starting to receive messages...")
            async for message in self.ws:
                self.last_message_time = time.time()
                self.logger.debug(f"Raw message received: {message[:200]}...")
                
                # Process the received message
                try:
                    # Parse JSON first to see what kind of message it is
                    data = json.loads(message)
                    
                    # Check if this is a subscription confirmation or other control message
                    if "event" in data:
                        self.logger.info(f"Received control message: {data}")
                        continue
                    
                    # Create OrderBook object from message
                    orderbook = OrderBook.from_json(message)
                    
                    # Call the callback if provided
                    if self.on_message_callback:
                        self.on_message_callback(orderbook)
                    else:
                        # Just log for now during initial development
                        self.logger.info(f"Received orderbook: {orderbook}")
                        
                except json.JSONDecodeError:
                    self.logger.warning(f"Invalid JSON: {message[:200]}...")
                except KeyError as e:
                    self.logger.warning(f"Missing key in message: {e} - {message[:200]}...")
                except Exception as e:
                    self.logger.error(f"Error processing message: {str(e)} - {message[:200]}...")
        
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