"""
Main application window for the Crypto Trade Simulator
"""
import tkinter as tk
from tkinter import ttk
import logging
from typing import Dict, Any, Optional, Callable

from ui.input_panel import InputPanel
from ui.output_panel import OutputPanel

class MainWindow:
    """
    Main application window
    """
    
    def __init__(self, on_simulation_request: Optional[Callable] = None):
        """
        Initialize main window
        
        Args:
            on_simulation_request: Callback for simulation requests
        """
        self.logger = logging.getLogger(__name__)
        self.on_simulation_request = on_simulation_request
        
        # Create main window
        self.root = tk.Tk()
        self.root.title("Crypto Trade Simulator")
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)
        
        # Configure grid
        self.root.columnconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=2)
        self.root.rowconfigure(0, weight=1)
        
        # Create status bar
        self.status_var = tk.StringVar(value="Ready")
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.grid(row=1, column=0, columnspan=2, sticky="ew")
        
        # Create panels
        self.input_panel = InputPanel(self.root, on_simulate=self._handle_simulation_request)
        self.input_panel.frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        self.output_panel = OutputPanel(self.root)
        self.output_panel.frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        
    def _handle_simulation_request(self, params: Dict[str, Any]) -> None:
        """
        Handle simulation request from input panel
        
        Args:
            params: Simulation parameters
        """
        self.logger.info(f"Simulation requested with params: {params}")
        self.status_var.set("Simulating trade...")
        
        # Call the callback if provided
        if self.on_simulation_request:
            self.on_simulation_request(params)
            
    def update_status(self, status: str) -> None:
        """
        Update status bar
        
        Args:
            status: Status message
        """
        self.status_var.set(status)
        
    def update_market_data(self, orderbook_summary: Dict[str, Any]) -> None:
        """
        Update market data display
        
        Args:
            orderbook_summary: Summary of orderbook data
        """
        self.output_panel.update_market_data(orderbook_summary)
        
    def update_simulation_results(self, results: Dict[str, Any]) -> None:
        """
        Update simulation results display
        
        Args:
            results: Simulation results
        """
        self.output_panel.update_simulation_results(results)
        self.status_var.set("Simulation complete")
        
    def run(self) -> None:
        """
        Run the main event loop
        """
        self.logger.info("Starting UI main loop")
        self.root.mainloop()
        
    def stop(self) -> None:
        """
        Stop the main event loop
        """
        self.logger.info("Stopping UI")
        self.root.destroy()