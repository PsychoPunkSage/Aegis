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

        # Check if dashboard exists and is still valid
        dashboard_exists = hasattr(self, 'dashboard') and self.dashboard
        if dashboard_exists:
            try:
                # Try to access a property to see if it's still valid
                self.dashboard.window.winfo_exists()
            except (tk.TclError, AttributeError):
                # If we get an error, the dashboard is no longer valid
                dashboard_exists = False
                delattr(self, 'dashboard')

        # Create dashboard if it doesn't exist or is no longer valid
        if not dashboard_exists:
            self.dashboard = PerformanceDashboard(self.root)

            # Add a callback when the window is closed to update our reference
            self.dashboard.window.protocol("WM_DELETE_WINDOW", 
                                          lambda: self._on_dashboard_close())
        else:
            # If it exists, bring it to front
            self.dashboard.window.lift()

        # Update with current data
        self.dashboard.update_performance_data(self.performance_data)
        self.dashboard.update_connection_data(self.connection_data)
        self.dashboard.update_error_data(self.error_log)
        self.dashboard.refresh()

    def _on_dashboard_close(self) -> None:
        """Handle dashboard window closing"""
        if hasattr(self, 'dashboard'):
            try:
                # Let the dashboard know it's being closed
                self.dashboard.close()
            except:
                pass
            # Remove our reference
            self.dashboard = None

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

    def update_batch_status(self, status: Dict[str, Any]) -> None:
        """
        Update batch simulation status

        Args:
            status: Batch status
        """
        # Show status in UI
        self.status_var.set(f"Batch simulation {status['batch_id']} running with {status['variations']} variations...")  
    
    def update_batch_results(self, results: Dict[str, Any]) -> None:
        """
        Update batch simulation results

        Args:
            results: Batch results
        """
        batch_id = results.get("batch_id", "unknown")
        count = results.get("count", 0)
        processing_time = results.get("processing_time", 0)

        # Update status
        self.status_var.set(f"Batch simulation {batch_id} completed: {count} simulations in {processing_time:.1f}s")

        # Display results
        # Create batch results window
        batch_window = tk.Toplevel(self.root)
        batch_window.title(f"Batch Results: {batch_id}")
        batch_window.geometry("800x600")

        # Configure grid
        batch_window.columnconfigure(0, weight=1)
        batch_window.rowconfigure(0, weight=0)  # Header
        batch_window.rowconfigure(1, weight=1)  # Results
        batch_window.rowconfigure(2, weight=0)  # Footer

        # Create header
        header_frame = ttk.Frame(batch_window)
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)

        ttk.Label(header_frame, text=f"Batch Simulation Results: {batch_id}", 
                 font=("Arial", 14, "bold")).pack(side=tk.LEFT, padx=10)

        ttk.Label(header_frame, 
                 text=f"{count} simulations in {processing_time:.1f}s").pack(side=tk.RIGHT, padx=10)

        # Create results table
        results_frame = ttk.Frame(batch_window)
        results_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)

        # Create treeview
        tree = ttk.Treeview(results_frame)
        tree.pack(fill=tk.BOTH, expand=True)

        # Add columns
        tree["columns"] = ("variation", "slippage", "impact", "fees", "net_cost")
        tree.column("#0", width=50, minwidth=50, stretch=tk.NO)
        tree.column("variation", width=200, minwidth=200)
        tree.column("slippage", width=100, minwidth=100)
        tree.column("impact", width=100, minwidth=100)
        tree.column("fees", width=100, minwidth=100)
        tree.column("net_cost", width=100, minwidth=100)

        tree.heading("#0", text="ID")
        tree.heading("variation", text="Variation")
        tree.heading("slippage", text="Slippage (%)")
        tree.heading("impact", text="Impact (%)")
        tree.heading("fees", text="Fees (%)")
        tree.heading("net_cost", text="Net Cost (%)")

        # Add scrollbar
        scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.configure(yscrollcommand=scrollbar.set)

        # Add data
        for i, item in enumerate(results.get("results", [])):
            variation = item.get("variation", {})
            result = item.get("result", {})

            # Format variation string
            variation_str = ", ".join(f"{k}={v}" for k, v in variation.items())

            # Get metrics
            slippage = result.get("expected_slippage_pct", 0)
            impact = result.get("market_impact", {}).get("total_impact_pct", 0)
            fees = result.get("fees", {}).get("effective_fee_rate", 0) * 100
            net_cost = result.get("net_cost_pct", 0)

            tree.insert("", "end", text=str(i+1), values=(
                variation_str,
                f"{slippage:.4f}",
                f"{impact:.4f}",
                f"{fees:.4f}",
                f"{net_cost:.4f}"
            ))

        # Create footer with export button
        footer_frame = ttk.Frame(batch_window)
        footer_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        
        # Add export button
        def export_batch():
            from utils.export import export_batch_results_to_csv
            from tkinter import filedialog

            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                title="Export Batch Results"
            )

            if filename:
                export_batch_results_to_csv(results, filename)
                tk.messagebox.showinfo("Export", f"Results exported to {filename}")

        tk.Button(footer_frame, text="Export to CSV", command=export_batch).pack(side=tk.LEFT, padx=10)

        # Add close button
        tk.Button(footer_frame, text="Close", command=batch_window.destroy).pack(side=tk.RIGHT, padx=10)
    
            
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