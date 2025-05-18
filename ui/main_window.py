"""
Main application window for the Crypto Trade Simulator
"""
import tkinter as tk
from tkinter import ttk
import logging
from typing import Dict, Any, List, Optional, Callable

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

        # Store performance data
        self.performance_data = {}
        self.connection_data = {}
        self.error_log = []

        # Add a menu bar
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)
        
        # File menu
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Export Results", command=self._export_results)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.stop)
        
        # Tools menu
        tools_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Performance Dashboard", command=self.show_performance_dashboard)
        tools_menu.add_command(label="Batch Simulation", command=self._show_batch_dialog)

    def _export_results(self) -> None:
        """Export current results"""
        # Delegate to output panel
        if hasattr(self.output_panel, '_export_to_csv'):
            self.output_panel._export_to_csv()
        else:
            tk.messagebox.showinfo("Export", "No export function available")
    
    def _show_batch_dialog(self) -> None:
        """Show batch simulation dialog"""
        batch_dialog = tk.Toplevel(self.root)
        batch_dialog.title("Batch Simulation")
        batch_dialog.geometry("400x500")
        batch_dialog.transient(self.root)
        batch_dialog.grab_set()
        
        # Create frame
        frame = ttk.Frame(batch_dialog, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Base parameters section
        ttk.Label(frame, text="Base Parameters", font=("Arial", 10, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 5))
        
        # Symbol
        ttk.Label(frame, text="Symbol:").grid(row=1, column=0, sticky="w", pady=2)
        symbol_var = tk.StringVar(value=self.input_panel.symbol_var.get())
        ttk.Combobox(frame, textvariable=symbol_var, values=self.input_panel.symbol_combo["values"]).grid(row=1, column=1, sticky="ew", pady=2)
        
        # Side
        ttk.Label(frame, text="Side:").grid(row=2, column=0, sticky="w", pady=2)
        side_var = tk.StringVar(value=self.input_panel.side_var.get())
        side_frame = ttk.Frame(frame)
        side_frame.grid(row=2, column=1, sticky="w", pady=2)
        ttk.Radiobutton(side_frame, text="Buy", variable=side_var, value="buy").pack(side=tk.LEFT)
        ttk.Radiobutton(side_frame, text="Sell", variable=side_var, value="sell").pack(side=tk.LEFT)
        
        # Fee tier
        ttk.Label(frame, text="Fee Tier:").grid(row=3, column=0, sticky="w", pady=2)
        fee_tier_var = tk.StringVar(value=self.input_panel.fee_tier_var.get())
        ttk.Combobox(frame, textvariable=fee_tier_var, values=self.input_panel.fee_tier_combo["values"]).grid(row=3, column=1, sticky="ew", pady=2)
        
        # Variations section
        ttk.Label(frame, text="Parameter Variations", font=("Arial", 10, "bold")).grid(row=4, column=0, columnspan=2, sticky="w", pady=(10, 5))
        
        # Quantity variations
        quantity_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(frame, text="Quantity Variations", variable=quantity_var).grid(row=5, column=0, columnspan=2, sticky="w", pady=2)
        
        # Base quantity
        ttk.Label(frame, text="Base Quantity:").grid(row=6, column=0, sticky="w", pady=2)
        base_qty_var = tk.StringVar(value=self.input_panel.quantity_var.get())
        ttk.Entry(frame, textvariable=base_qty_var).grid(row=6, column=1, sticky="ew", pady=2)
        
        # Volatility variations
        volatility_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(frame, text="Volatility Variations", variable=volatility_var).grid(row=7, column=0, columnspan=2, sticky="w", pady=2)
        
        # Base volatility
        ttk.Label(frame, text="Base Volatility:").grid(row=8, column=0, sticky="w", pady=2)
        base_vol_var = tk.StringVar(value=self.input_panel.volatility_var.get())
        ttk.Entry(frame, textvariable=base_vol_var).grid(row=8, column=1, sticky="ew", pady=2)
        
        # Model variations
        model_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(frame, text="Impact Model Variations", variable=model_var).grid(row=9, column=0, columnspan=2, sticky="w", pady=2)
        
        # Order type variations
        order_type_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(frame, text="Order Type Variations", variable=order_type_var).grid(row=10, column=0, columnspan=2, sticky="w", pady=2)
        
        # Run batch button
        def run_batch():
            # Collect parameters
            params = {
                "batch_mode": True,
                "exchange": "OKX",
                "symbol": symbol_var.get(),
                "side": side_var.get(),
                "fee_tier": fee_tier_var.get(),
                "quantity": float(base_qty_var.get()) if base_qty_var.get() else 0.1,
                "volatility": float(base_vol_var.get()) if base_vol_var.get() else 2.5,
                "quantity_variations": quantity_var.get(),
                "volatility_variations": volatility_var.get(),
                "model_variations": model_var.get(),
                "order_type_variations": order_type_var.get()
            }
            
            # Close dialog
            batch_dialog.destroy()
            
            # Run simulation
            if self.on_simulation_request:
                self.on_simulation_request(params)
        
        ttk.Button(frame, text="Run Batch Simulation", command=run_batch).grid(row=11, column=0, columnspan=2, pady=10)
        
        # Cancel button
        ttk.Button(frame, text="Cancel", command=batch_dialog.destroy).grid(row=12, column=0, columnspan=2)
        
        # Make dialog resizable
        for i in range(2):
            frame.columnconfigure(i, weight=1)
            
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
    
    def show_performance_dashboard(self) -> None:
        """Show the performance dashboard"""
        # Import the dashboard
        from ui.performance_dashboard import PerformanceDashboard

        # Create dashboard if it doesn't exist
        if not hasattr(self, 'dashboard') or not self.dashboard:
            self.dashboard = PerformanceDashboard(self.root)
        else:
            # If it exists, bring it to front
            self.dashboard.window.lift()

        # Update with current data
        self.dashboard.update_performance_data(self.performance_data)
        self.dashboard.update_connection_data(self.connection_data)
        self.dashboard.update_error_data(self.error_log)
        self.dashboard.refresh()

    def update_performance_metrics(self, metrics: Dict[str, Any]) -> None:
        """
        Update performance metrics
        
        Args:
            metrics: Performance metrics
        """
        self.performance_data = metrics
        
        # Update dashboard if it exists
        if hasattr(self, 'dashboard') and self.dashboard:
            self.dashboard.update_performance_data(metrics)
            self.dashboard.refresh()
            
    def update_connection_stats(self, stats: Dict[str, Any]) -> None:
        """
        Update connection statistics
        
        Args:
            stats: Connection statistics
        """
        self.connection_data = stats
        
        # Update dashboard if it exists
        if hasattr(self, 'dashboard') and self.dashboard:
            self.dashboard.update_connection_data(stats)
            self.dashboard.refresh()
            
    def update_error_log(self, errors: List[Dict[str, Any]]) -> None:
        """
        Update error log
        
        Args:
            errors: Error log entries
        """
        self.error_log = errors
        
        # Update dashboard if it exists
        if hasattr(self, 'dashboard') and self.dashboard:
            self.dashboard.update_error_data(errors)
            self.dashboard.refresh()
            
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