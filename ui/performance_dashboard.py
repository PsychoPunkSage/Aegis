"""
Performance dashboard for monitoring system metrics
"""
import time
import logging
import tkinter as tk
from tkinter import ttk
from datetime import datetime
from typing import Dict, Any, List

class PerformanceDashboard:
    """Dashboard for monitoring system performance"""
    
    def __init__(self, parent):
        """
        Initialize performance dashboard
        
        Args:
            parent: Parent widget
        """
        self.logger = logging.getLogger(__name__)
        
        # Create main window
        self.window = tk.Toplevel(parent)
        self.window.title("Performance Dashboard")
        self.window.geometry("800x600")

        self.parent = parent
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Configure grid
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(0, weight=0)  # Header
        self.window.rowconfigure(1, weight=1)  # Main content
        self.window.rowconfigure(2, weight=0)  # Footer
        
        # Create header
        header_frame = ttk.Frame(self.window)
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        
        ttk.Label(header_frame, text="Performance Dashboard", font=("Arial", 16, "bold")).pack(side=tk.LEFT, padx=10)
        
        self.update_time_var = tk.StringVar(value="Last update: Never")
        ttk.Label(header_frame, textvariable=self.update_time_var).pack(side=tk.RIGHT, padx=10)
        
        # Create notebook for metrics
        self.notebook = ttk.Notebook(self.window)
        self.notebook.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        
        # Create tabs
        self.overview_tab = ttk.Frame(self.notebook)
        self.latency_tab = ttk.Frame(self.notebook)
        self.connections_tab = ttk.Frame(self.notebook)
        self.errors_tab = ttk.Frame(self.notebook)
        
        self.notebook.add(self.overview_tab, text="Overview")
        self.notebook.add(self.latency_tab, text="Latency")
        self.notebook.add(self.connections_tab, text="Connections")
        self.notebook.add(self.errors_tab, text="Errors")
        
        # Set up each tab
        self._setup_overview_tab()
        self._setup_latency_tab()
        self._setup_connections_tab()
        self._setup_errors_tab()
        
        # Create footer
        footer_frame = ttk.Frame(self.window)
        footer_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        
        ttk.Button(footer_frame, text="Refresh", command=self.refresh).pack(side=tk.LEFT, padx=10)
        ttk.Button(footer_frame, text="Export", command=self._export_metrics).pack(side=tk.LEFT, padx=10)
        ttk.Button(footer_frame, text="Close", command=self.on_close).pack(side=tk.RIGHT, padx=10)
        
        # Initialize data
        self.performance_data = {}
        self.connection_data = {}
        self.error_data = []
        
        # Auto-refresh timer
        self.auto_refresh = True
        self.refresh_interval = 5000  # ms
        self.after_id = None
        self._schedule_refresh()
        
    def _setup_overview_tab(self) -> None:
        """Set up the overview tab"""
        frame = self.overview_tab
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(0, weight=0)
        frame.rowconfigure(1, weight=1)
        
        # System status section
        status_frame = ttk.LabelFrame(frame, text="System Status")
        status_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        
        # Status grid
        for i in range(2):
            status_frame.columnconfigure(i, weight=1)
            
        ttk.Label(status_frame, text="Uptime:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.uptime_label = ttk.Label(status_frame, text="-")
        self.uptime_label.grid(row=0, column=1, sticky="w", padx=5, pady=2)
        
        ttk.Label(status_frame, text="Active Connections:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.connections_label = ttk.Label(status_frame, text="-")
        self.connections_label.grid(row=1, column=1, sticky="w", padx=5, pady=2)
        
        ttk.Label(status_frame, text="Messages Processed:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.messages_label = ttk.Label(status_frame, text="-")
        self.messages_label.grid(row=2, column=1, sticky="w", padx=5, pady=2)
        
        ttk.Label(status_frame, text="Active Symbols:").grid(row=0, column=2, sticky="w", padx=5, pady=2)
        self.symbols_label = ttk.Label(status_frame, text="-")
        self.symbols_label.grid(row=0, column=3, sticky="w", padx=5, pady=2)
        
        ttk.Label(status_frame, text="Error Count:").grid(row=1, column=2, sticky="w", padx=5, pady=2)
        self.errors_label = ttk.Label(status_frame, text="-")
        self.errors_label.grid(row=1, column=3, sticky="w", padx=5, pady=2)
        
        ttk.Label(status_frame, text="Simulator Threads:").grid(row=2, column=2, sticky="w", padx=5, pady=2)
        self.threads_label = ttk.Label(status_frame, text="-")
        self.threads_label.grid(row=2, column=3, sticky="w", padx=5, pady=2)
        
        metrics_frame = ttk.LabelFrame(frame, text="Performance Metrics")
        metrics_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        # Create a treeview for metrics with two columns
        self.metrics_tree = ttk.Treeview(metrics_frame, columns=("metric", "value"), show="headings")
        self.metrics_tree.heading("metric", text="Metric")
        self.metrics_tree.heading("value", text="Value (ms)")
        self.metrics_tree.column("metric", width=150, anchor="w")
        self.metrics_tree.column("value", width=100, anchor="center")
        self.metrics_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Batch metrics section
        batch_frame = ttk.LabelFrame(frame, text="Batch Performance")
        batch_frame.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
        
        # Create a treeview for batch metrics with two columns
        self.batch_tree = ttk.Treeview(batch_frame, columns=("metric", "value"), show="headings")
        self.batch_tree.heading("metric", text="Metric")
        self.batch_tree.heading("value", text="Value")
        self.batch_tree.column("metric", width=150, anchor="w")
        self.batch_tree.column("value", width=100, anchor="center")
        self.batch_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def _setup_latency_tab(self) -> None:
        """Set up the latency tab"""
        frame = self.latency_tab
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        
        # Create a treeview for latency metrics
        self.latency_tree = ttk.Treeview(frame, columns=("process", "avg", "p50", "p95", "p99", "max"), show="headings")
        self.latency_tree.heading("process", text="Process")
        self.latency_tree.heading("avg", text="Avg (ms)")
        self.latency_tree.heading("p50", text="P50 (ms)")
        self.latency_tree.heading("p95", text="P95 (ms)")
        self.latency_tree.heading("p99", text="P99 (ms)")
        self.latency_tree.heading("max", text="Max (ms)")
        
        for col in ("avg", "p50", "p95", "p99", "max"):
            self.latency_tree.column(col, width=80, anchor="center")
            
        self.latency_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
    def _setup_connections_tab(self) -> None:
        """Set up the connections tab"""
        frame = self.connections_tab
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        
        # Create a treeview for connection metrics
        self.connections_tree = ttk.Treeview(
            frame, 
            columns=("symbol", "status", "msgs", "msgs_sec", "uptime", "last_msg", "errors"), 
            show="headings"
        )
        
        self.connections_tree.heading("symbol", text="Symbol")
        self.connections_tree.heading("status", text="Status")
        self.connections_tree.heading("msgs", text="Messages")
        self.connections_tree.heading("msgs_sec", text="Msgs/sec")
        self.connections_tree.heading("uptime", text="Uptime (s)")
        self.connections_tree.heading("last_msg", text="Last Msg (s)")
        self.connections_tree.heading("errors", text="Errors")
        
        self.connections_tree.column("symbol", width=100, anchor="w")
        self.connections_tree.column("status", width=80, anchor="center")
        self.connections_tree.column("msgs", width=80, anchor="e")
        self.connections_tree.column("msgs_sec", width=80, anchor="e")
        self.connections_tree.column("uptime", width=80, anchor="e")
        self.connections_tree.column("last_msg", width=80, anchor="e")
        self.connections_tree.column("errors", width=60, anchor="e")
        
        self.connections_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
    def _setup_errors_tab(self) -> None:
        """Set up the errors tab"""
        frame = self.errors_tab
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        
        # Create a treeview for error log
        self.errors_tree = ttk.Treeview(
            frame, 
            columns=("time", "source", "error"), 
            show="headings"
        )
        
        self.errors_tree.heading("time", text="Time")
        self.errors_tree.heading("source", text="Source")
        self.errors_tree.heading("error", text="Error")
        
        self.errors_tree.column("time", width=150, anchor="w")
        self.errors_tree.column("source", width=100, anchor="w")
        self.errors_tree.column("error", width=400, anchor="w")
        
        self.errors_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
    def update_performance_data(self, data: Dict[str, Any]) -> None:
        """
        Update performance data
        
        Args:
            data: Performance data
        """
        self.performance_data = data
        
    def update_connection_data(self, data: Dict[str, Any]) -> None:
        """
        Update connection data
        
        Args:
            data: Connection data
        """
        self.connection_data = data
        
    def update_error_data(self, data: List[Dict[str, Any]]) -> None:
        """
        Update error data
        
        Args:
            data: Error data
        """
        self.error_data = data
        
    def refresh(self) -> None:
        """Refresh the dashboard with current data"""
        try:
            self._update_overview_tab()
            self._update_latency_tab()
            self._update_connections_tab()
            self._update_errors_tab()

            # Update refresh time
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.update_time_var.set(f"Last update: {now}")

            # Print debug info
            print(f"Dashboard refreshed at {now}, data: {len(self.performance_data)} metrics")
            print(f"                    data: {self.performance_data} metrics")
        except Exception as e:
            print(f"Error refreshing dashboard: {e}")
        
    def _update_overview_tab(self) -> None:
        """Update the overview tab"""
        try:
            if not hasattr(self, 'window') or not self.window.winfo_exists() or not hasattr(self, 'latency_tree'):
                return
            try:
                # Update system status
                uptime = self.performance_data.get("uptime", 0)
                hours = int(uptime // 3600)
                minutes = int((uptime % 3600) // 60)
                seconds = int(uptime % 60)
                self.uptime_label.config(text=f"{hours:02d}:{minutes:02d}:{seconds:02d}")

                # Get connection info
                active_connections = sum(1 for stats in self.connection_data.values() if stats.get("connected", False))
                total_connections = len(self.connection_data)
                self.connections_label.config(text=f"{active_connections}/{total_connections}")

                # Get message count
                messages = sum(stats.get("messages_received", 0) for stats in self.connection_data.values())
                self.messages_label.config(text=f"{messages}")

                # Update Active Symbols
                active_symbols = self.performance_data.get("active_symbols", [])
                self.symbols_label.config(text=f"{len(active_symbols)}")

                # Update Error Count
                error_count = self.performance_data.get("error_count", len(self.error_data))
                self.errors_label.config(text=f"{error_count}")

                # Update Simulator Threads
                threads = self.performance_data.get("simulator_threads", 1)
                self.threads_label.config(text=f"{threads}")

                self.metrics_tree.delete(*self.metrics_tree.get_children())

                # # For symbols, errors, and threads, we may not have data yet
                # if hasattr(self, 'symbols_label'):
                #     active_symbols = self.performance_data.get("active_symbols", [])
                #     symbols_count = len(active_symbols) if isinstance(active_symbols, list) else 0
                #     self.symbols_label.config(text=f"{symbols_count}")

                # if hasattr(self, 'errors_label'):
                #     error_count = len(self.error_data)
                #     self.errors_label.config(text=f"{error_count}")

                # if hasattr(self, 'threads_label'):
                #     simulator_threads = self.performance_data.get("simulator_threads", 0)
                #     self.threads_label.config(text=f"{simulator_threads}")

                # Prepare metrics to display
                metrics = [
                    ("Slippage Prediction", self.performance_data.get("slippage_prediction_latency", 0)),
                    ("Market Impact", self.performance_data.get("market_impact_latency", 0)),
                    ("Fee Calculation", self.performance_data.get("fee_calculation_latency", 0)),
                    ("Maker/Taker", self.performance_data.get("maker_taker_latency", 0)),
                    ("Trade Simulation", self.performance_data.get("trade_simulation_latency", 0)),
                    ("Volatility", self.performance_data.get("volatility_latency", 0)),
                ]

                print(f"METRICS : {metrics}")

                # Add metrics to tree
                for name, value in metrics:
                    self.metrics_tree.insert("", "end", values=(name, f"{value:.2f}"))

                # For batch metrics, add placeholder values if not available
                self.batch_tree.delete(*self.batch_tree.get_children())

                batch_metrics = [
                    ("Batch Success Rate", f"{self.performance_data.get('batch_success_rate', 0):.1f}%"),
                    ("Avg Batch Time", f"{self.performance_data.get('avg_batch_time', 0):.2f}s"),
                    ("Max Batch Size", f"{self.performance_data.get('max_batch_size', 0)}"),
                    ("Completed Batches", f"{self.performance_data.get('completed_batches', 0)}"),
                ]

                print(f"batch metrics: {batch_metrics}")

                for name, value in batch_metrics:
                    self.batch_tree.insert("", "end", values=(name, value))

                print("Overview tab updated successfully")

            except tk.TclError:
                return

        except Exception as e:
            print(f"Error updating overview tab: {e}")
            import traceback
            traceback.print_exc()
            
    def _update_latency_tab(self) -> None:
        """Update the latency tab"""
        try:
            # Check if window and widget still exist
            if not hasattr(self, 'window') or not self.window.winfo_exists() or not hasattr(self, 'latency_tree'):
                return

            try:
                self.latency_tree.delete(*self.latency_tree.get_children())

                # Create a list of components with default values
                components = [
                    ("Orderbook Processing", 0, 0, 0, 0, 0),
                    ("Slippage Model", self.performance_data.get("slippage_prediction_latency", 0), 0, 0, 0, 0),
                    ("Impact Model", self.performance_data.get("market_impact_latency", 0), 0, 0, 0, 0),
                    ("Fee Calculator", self.performance_data.get("fee_calculation_latency", 0), 0, 0, 0, 0),
                    ("Maker/Taker", self.performance_data.get("maker_taker_latency", 0), 0, 0, 0, 0),
                    ("Volatility", self.performance_data.get("volatility_latency", 0), 0, 0, 0, 0),
                    ("Trade Simulation", self.performance_data.get("trade_simulation_latency", 0), 0, 0, 0, 0),
                    ("UI Update", 0, 0, 0, 0, 0)
                ]

                # For percentiles, use defaults or actual values
                for component, avg, p50, p95, p99, max_val in components:
                    # Use different p50/p95/p99 values if available, otherwise use the avg
                    self.latency_tree.insert("", "end", text=component, values=(
                        component,
                        f"{avg:.2f}", 
                        f"{self.performance_data.get(f'{component.lower().replace(' ', '_')}_p50', avg):.2f}", 
                        f"{self.performance_data.get(f'{component.lower().replace(' ', '_')}_p95', avg):.2f}",
                        f"{self.performance_data.get(f'{component.lower().replace(' ', '_')}_p99', avg):.2f}",
                        f"{self.performance_data.get(f'{component.lower().replace(' ', '_')}_max', avg):.2f}"
                    ))

                print("Latency tab updated successfully")

            except tk.TclError:
                return

        except Exception as e:
            print(f"Error updating latency tab: {e}")
            import traceback
            traceback.print_exc()
            
    def _update_connections_tab(self) -> None:
        """Update the connections tab"""
        try: 
            if not hasattr(self, 'window') or not self.window.winfo_exists() or not hasattr(self, 'latency_tree'):
                return
            try:
                self.connections_tree.delete(*self.connections_tree.get_children())

                # Ensure we have connection data
                if not self.connection_data:
                    print("No connection data available")
                    # Add a placeholder row
                    self.connections_tree.insert("", "end", text="No Data", values=(
                        "N/A", "Disconnected", "0", "0", "0", "0", "0"
                    ))
                    return

                # Add data for each connection
                for conn_id, stats in self.connection_data.items():
                    symbol = stats.get("symbol", "-")
                    status = "Connected" if stats.get("connected", False) else "Disconnected"
                    msgs = stats.get("messages_received", 0)
                    msgs_sec = stats.get("messages_per_second", 0)
                    uptime = stats.get("uptime", 0)
                    last_msg = stats.get("last_message", 0)
                    errors = stats.get("connection_errors", 0) + stats.get("message_errors", 0)

                    self.connections_tree.insert("", "end", text=conn_id, values=(
                        symbol, status, msgs, f"{msgs_sec:.1f}", f"{uptime:.1f}", f"{last_msg:.1f}", errors
                    ))

                print("Connections tab updated successfully")

            except tk.TclError:
                return

        except Exception as e:
            print(f"Error updating connections tab: {e}")
            import traceback
            traceback.print_exc()
            
    def _update_errors_tab(self) -> None:
        """Update the errors tab"""
        try: 
            if not hasattr(self, 'window') or not self.window.winfo_exists() or not hasattr(self, 'latency_tree'):
                return
            try:
                self.errors_tree.delete(*self.errors_tree.get_children())

                # Ensure we have error data
                if not self.error_data:
                    print("No error data available")
                    # Add a placeholder row
                    self.errors_tree.insert("", "end", values=(
                        "No errors", "-", "-"
                    ))
                    return

                # Add errors
                for error in self.error_data:
                    time_str = error.get("time", "-")
                    source = error.get("source", "-")
                    error_msg = error.get("error", "-")

                    self.errors_tree.insert("", "end", values=(time_str, source, error_msg))

                print("Errors tab updated successfully")

            except tk.TclError:
                return
            
        except Exception as e:
            print(f"Error updating errors tab: {e}")
            import traceback
            traceback.print_exc()
            
    def _export_metrics(self) -> None:
        """Export metrics to CSV"""
        # Ask for filename
        from tkinter import filedialog
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Export Performance Metrics"
        )
        
        if not filename:
            return
            
        try:
            import csv
            with open(filename, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write header
                writer.writerow(["Category", "Metric", "Value"])
                
                # Write system status
                writer.writerow(["System", "Uptime", self.uptime_label.cget("text")])
                writer.writerow(["System", "Active Connections", self.connections_label.cget("text")])
                writer.writerow(["System", "Messages Processed", self.messages_label.cget("text")])
                writer.writerow(["System", "Active Symbols", self.symbols_label.cget("text")])
                writer.writerow(["System", "Error Count", self.errors_label.cget("text")])
                writer.writerow(["System", "Simulator Threads", self.threads_label.cget("text")])
                
                # Write performance metrics
                for item in self.metrics_tree.get_children():
                    values = self.metrics_tree.item(item, "values")
                    writer.writerow(["Performance", values[0], values[1]])
                    
                # Write batch metrics
                for item in self.batch_tree.get_children():
                    values = self.batch_tree.item(item, "values")
                    writer.writerow(["Batch", values[0], values[1]])
                    
                # Write latency metrics
                for item in self.latency_tree.get_children():
                    component = self.latency_tree.item(item, "text")
                    values = self.latency_tree.item(item, "values")
                    writer.writerow(["Latency", f"{component} - Avg", values[0]])
                    writer.writerow(["Latency", f"{component} - P50", values[1]])
                    writer.writerow(["Latency", f"{component} - P95", values[2]])
                    writer.writerow(["Latency", f"{component} - P99", values[3]])
                    writer.writerow(["Latency", f"{component} - Max", values[4]])
                    
                # Write connection metrics
                for item in self.connections_tree.get_children():
                    values = self.connections_tree.item(item, "values")
                    writer.writerow(["Connection", f"{values[0]} - Status", values[1]])
                    writer.writerow(["Connection", f"{values[0]} - Messages", values[2]])
                    writer.writerow(["Connection", f"{values[0]} - Msgs/sec", values[3]])
                    writer.writerow(["Connection", f"{values[0]} - Uptime", values[4]])
                    writer.writerow(["Connection", f"{values[0]} - Last Msg", values[5]])
                    writer.writerow(["Connection", f"{values[0]} - Errors", values[6]])
                    
            tk.messagebox.showinfo("Export", f"Metrics exported to {filename}")
        except Exception as e:
            tk.messagebox.showerror("Export Error", f"Failed to export metrics: {e}")
    
    def _schedule_refresh(self) -> None:
        """Schedule automatic refresh"""
        if self.auto_refresh and hasattr(self, 'window') and self.window.winfo_exists():
            self.refresh()
            # Store the after ID
            self.after_id = self.window.after(self.refresh_interval, self._schedule_refresh)
        else:
            # Don't schedule any more refreshes
            self.auto_refresh = False
     
    def on_close(self) -> None:
        """Handle closing the dashboard window from any source"""
        # Stop auto refresh
        self.auto_refresh = False

        # Release resources
        if hasattr(self, 'window') and self.window:
            # Destroy the window
            try:
                self.window.destroy()
            except:
                pass
            
        # Notify parent if available
        if hasattr(self.parent, '_on_dashboard_close'):
            try:
                self.parent._on_dashboard_close()
            except Exception as e:
                print(f"Error notifying parent: {e}")

    def close(self) -> None:
        """Internal cleanup - for backward compatibility"""
        self.on_close()