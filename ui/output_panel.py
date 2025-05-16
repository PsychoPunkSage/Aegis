"""
Output panel for the Crypto Trade Simulator
"""
import tkinter as tk
from tkinter import ttk
import logging
from typing import Dict, Any

class OutputPanel:
    """
    Output panel for simulation results
    """
    
    def __init__(self, parent):
        """
        Initialize output panel
        
        Args:
            parent: Parent widget
        """
        self.logger = logging.getLogger(__name__)
        
        # Create frame
        self.frame = ttk.LabelFrame(parent, text="Simulation Results")
        
        # Configure grid for the frame
        self.frame.columnconfigure(0, weight=1)
        self.frame.columnconfigure(1, weight=1)
        self.frame.rowconfigure(1, weight=1)
        self.frame.rowconfigure(3, weight=1)
        
        # Create sections
        self._create_market_data_section()
        self._create_simulation_results_section()
        
    def _create_market_data_section(self) -> None:
        """Create market data display section"""
        # Market data frame
        market_frame = ttk.LabelFrame(self.frame, text="Current Market Data")
        market_frame.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
        
        # Configure grid
        for i in range(4):
            market_frame.columnconfigure(i, weight=1)
            
        # Create labels for market data
        ttk.Label(market_frame, text="Symbol:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.symbol_label = ttk.Label(market_frame, text="-")
        self.symbol_label.grid(row=0, column=1, sticky="w", padx=5, pady=2)
        
        ttk.Label(market_frame, text="Price:").grid(row=0, column=2, sticky="w", padx=5, pady=2)
        self.price_label = ttk.Label(market_frame, text="-")
        self.price_label.grid(row=0, column=3, sticky="w", padx=5, pady=2)
        
        ttk.Label(market_frame, text="Spread:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.spread_label = ttk.Label(market_frame, text="-")
        self.spread_label.grid(row=1, column=1, sticky="w", padx=5, pady=2)
        
        ttk.Label(market_frame, text="Volatility:").grid(row=1, column=2, sticky="w", padx=5, pady=2)
        self.volatility_label = ttk.Label(market_frame, text="-")
        self.volatility_label.grid(row=1, column=3, sticky="w", padx=5, pady=2)
        
        ttk.Label(market_frame, text="Ask Depth:").grid(row=2, column=0, sticky="w", padx=5, pady=2)
        self.ask_depth_label = ttk.Label(market_frame, text="-")
        self.ask_depth_label.grid(row=2, column=1, sticky="w", padx=5, pady=2)
        
        ttk.Label(market_frame, text="Bid Depth:").grid(row=2, column=2, sticky="w", padx=5, pady=2)
        self.bid_depth_label = ttk.Label(market_frame, text="-")
        self.bid_depth_label.grid(row=2, column=3, sticky="w", padx=5, pady=2)
        
        # Add a small orderbook display (top few levels)
        ttk.Label(market_frame, text="Top Orderbook Levels:").grid(
            row=3, column=0, columnspan=4, sticky="w", padx=5, pady=5
        )
        
        # Orderbook headers
        ttk.Label(market_frame, text="Bid Qty", anchor="e").grid(
            row=4, column=0, sticky="e", padx=5, pady=2
        )
        ttk.Label(market_frame, text="Bid Price", anchor="e").grid(
            row=4, column=1, sticky="e", padx=5, pady=2
        )
        ttk.Label(market_frame, text="Ask Price", anchor="w").grid(
            row=4, column=2, sticky="w", padx=5, pady=2
        )
        ttk.Label(market_frame, text="Ask Qty", anchor="w").grid(
            row=4, column=3, sticky="w", padx=5, pady=2
        )
        
        # Create labels for top 5 orderbook levels
        self.bid_qty_labels = []
        self.bid_price_labels = []
        self.ask_price_labels = []
        self.ask_qty_labels = []
        
        for i in range(5):
            bid_qty = ttk.Label(market_frame, text="-", anchor="e")
            bid_qty.grid(row=5+i, column=0, sticky="e", padx=5, pady=1)
            self.bid_qty_labels.append(bid_qty)
            
            bid_price = ttk.Label(market_frame, text="-", anchor="e")
            bid_price.grid(row=5+i, column=1, sticky="e", padx=5, pady=1)
            self.bid_price_labels.append(bid_price)
            
            ask_price = ttk.Label(market_frame, text="-", anchor="w")
            ask_price.grid(row=5+i, column=2, sticky="w", padx=5, pady=1)
            self.ask_price_labels.append(ask_price)
            
            ask_qty = ttk.Label(market_frame, text="-", anchor="w")
            ask_qty.grid(row=5+i, column=3, sticky="w", padx=5, pady=1)
            self.ask_qty_labels.append(ask_qty)
            
    def _create_simulation_results_section(self) -> None:
        """Create simulation results display section"""
        # Create notebook for results
        self.results_notebook = ttk.Notebook(self.frame)
        self.results_notebook.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
        
        # Summary tab
        summary_frame = ttk.Frame(self.results_notebook)
        self.results_notebook.add(summary_frame, text="Summary")
        
        # Configure grid
        for i in range(4):
            summary_frame.columnconfigure(i, weight=1)
            
        # Create labels for summary results
        row = 0
        
        ttk.Label(summary_frame, text="Order Details:", font=("Arial", 10, "bold")).grid(
            row=row, column=0, columnspan=4, sticky="w", padx=5, pady=5
        )
        
        row += 1
        
        ttk.Label(summary_frame, text="Symbol:").grid(row=row, column=0, sticky="w", padx=5, pady=2)
        self.result_symbol_label = ttk.Label(summary_frame, text="-")
        self.result_symbol_label.grid(row=row, column=1, sticky="w", padx=5, pady=2)
        
        ttk.Label(summary_frame, text="Side:").grid(row=row, column=2, sticky="w", padx=5, pady=2)
        self.result_side_label = ttk.Label(summary_frame, text="-")
        self.result_side_label.grid(row=row, column=3, sticky="w", padx=5, pady=2)
        
        row += 1
        
        ttk.Label(summary_frame, text="Quantity:").grid(row=row, column=0, sticky="w", padx=5, pady=2)
        self.result_quantity_label = ttk.Label(summary_frame, text="-")
        self.result_quantity_label.grid(row=row, column=1, sticky="w", padx=5, pady=2)
        
        ttk.Label(summary_frame, text="Order Value:").grid(row=row, column=2, sticky="w", padx=5, pady=2)
        self.result_value_label = ttk.Label(summary_frame, text="-")
        self.result_value_label.grid(row=row, column=3, sticky="w", padx=5, pady=2)
        
        row += 1
        
        # Separator
        separator = ttk.Separator(summary_frame, orient="horizontal")
        separator.grid(row=row, column=0, columnspan=4, sticky="ew", padx=5, pady=10)
        
        row += 1
        
        ttk.Label(summary_frame, text="Cost Breakdown:", font=("Arial", 10, "bold")).grid(
            row=row, column=0, columnspan=4, sticky="w", padx=5, pady=5
        )
        
        row += 1
        
        ttk.Label(summary_frame, text="Slippage:").grid(row=row, column=0, sticky="w", padx=5, pady=2)
        self.result_slippage_label = ttk.Label(summary_frame, text="-")
        self.result_slippage_label.grid(row=row, column=1, sticky="w", padx=5, pady=2)
        
        ttk.Label(summary_frame, text="Slippage Cost:").grid(row=row, column=2, sticky="w", padx=5, pady=2)
        self.result_slippage_cost_label = ttk.Label(summary_frame, text="-")
        self.result_slippage_cost_label.grid(row=row, column=3, sticky="w", padx=5, pady=2)
        
        row += 1
        
        ttk.Label(summary_frame, text="Market Impact:").grid(row=row, column=0, sticky="w", padx=5, pady=2)
        self.result_impact_label = ttk.Label(summary_frame, text="-")
        self.result_impact_label.grid(row=row, column=1, sticky="w", padx=5, pady=2)
        
        ttk.Label(summary_frame, text="Impact Cost:").grid(row=row, column=2, sticky="w", padx=5, pady=2)
        self.result_impact_cost_label = ttk.Label(summary_frame, text="-")
        self.result_impact_cost_label.grid(row=row, column=3, sticky="w", padx=5, pady=2)
        
        row += 1
        
        ttk.Label(summary_frame, text="Fee Rate:").grid(row=row, column=0, sticky="w", padx=5, pady=2)
        self.result_fee_rate_label = ttk.Label(summary_frame, text="-")
        self.result_fee_rate_label.grid(row=row, column=1, sticky="w", padx=5, pady=2)
        
        ttk.Label(summary_frame, text="Fee Cost:").grid(row=row, column=2, sticky="w", padx=5, pady=2)
        self.result_fee_cost_label = ttk.Label(summary_frame, text="-")
        self.result_fee_cost_label.grid(row=row, column=3, sticky="w", padx=5, pady=2)
        
        row += 1
        
        # Separator
        separator = ttk.Separator(summary_frame, orient="horizontal")
        separator.grid(row=row, column=0, columnspan=4, sticky="ew", padx=5, pady=10)
        
        row += 1
        
        ttk.Label(summary_frame, text="Total Costs:", font=("Arial", 10, "bold")).grid(
            row=row, column=0, columnspan=4, sticky="w", padx=5, pady=5
        )
        
        row += 1
        
        ttk.Label(summary_frame, text="Net Cost:").grid(row=row, column=0, sticky="w", padx=5, pady=2)
        self.result_net_cost_label = ttk.Label(summary_frame, text="-", font=("Arial", 10, "bold"))
        self.result_net_cost_label.grid(row=row, column=1, sticky="w", padx=5, pady=2)
        
        ttk.Label(summary_frame, text="Cost Percentage:").grid(row=row, column=2, sticky="w", padx=5, pady=2)
        self.result_net_pct_label = ttk.Label(summary_frame, text="-", font=("Arial", 10, "bold"))
        self.result_net_pct_label.grid(row=row, column=3, sticky="w", padx=5, pady=2)
        
        row += 1
        
        # Separator
        separator = ttk.Separator(summary_frame, orient="horizontal")
        separator.grid(row=row, column=0, columnspan=4, sticky="ew", padx=5, pady=10)
        
        row += 1
        
        ttk.Label(summary_frame, text="Other Metrics:", font=("Arial", 10, "bold")).grid(
            row=row, column=0, columnspan=4, sticky="w", padx=5, pady=5
        )
        
        row += 1
        
        ttk.Label(summary_frame, text="Maker/Taker:").grid(row=row, column=0, sticky="w", padx=5, pady=2)
        self.result_maker_taker_label = ttk.Label(summary_frame, text="-")
        self.result_maker_taker_label.grid(row=row, column=1, sticky="w", padx=5, pady=2)
        
        ttk.Label(summary_frame, text="Internal Latency:").grid(row=row, column=2, sticky="w", padx=5, pady=2)
        self.result_latency_label = ttk.Label(summary_frame, text="-")
        self.result_latency_label.grid(row=row, column=3, sticky="w", padx=5, pady=2)
        
        # Details tab
        details_frame = ttk.Frame(self.results_notebook)
        self.results_notebook.add(details_frame, text="Details")
        
        # Configure grid
        details_frame.columnconfigure(0, weight=1)
        details_frame.rowconfigure(0, weight=1)
        
        # Create a text widget for detailed results
        self.details_text = tk.Text(details_frame, wrap=tk.WORD, width=50, height=20)
        self.details_text.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(details_frame, orient="vertical", command=self.details_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.details_text.configure(yscrollcommand=scrollbar.set)
        
        # Visualization tab
        viz_frame = ttk.Frame(self.results_notebook)
        self.results_notebook.add(viz_frame, text="Visualization")
        
        # Configure grid
        viz_frame.columnconfigure(0, weight=1)
        viz_frame.rowconfigure(0, weight=1)
        
        # Create a canvas for visualization
        self.viz_canvas = tk.Canvas(viz_frame, bg="white", width=500, height=400)
        self.viz_canvas.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
    def update_market_data(self, data: Dict[str, Any]) -> None:
        """
        Update market data display
        
        Args:
            data: Market data to display
        """
        if not data:
            return
            
        # Update market data labels
        self.symbol_label.configure(text=data.get("symbol", "-"))
        self.price_label.configure(text=f"{data.get('mid_price', 0.0):.2f}")
        
        spread = data.get("spread", 0.0)
        spread_bps = (spread / data.get("mid_price", 1.0)) * 10000 if data.get("mid_price", 0.0) > 0 else 0.0
        self.spread_label.configure(text=f"{spread:.2f} ({spread_bps:.1f} bps)")
        
        self.volatility_label.configure(text=f"{data.get('volatility', 0.0):.2f}%")
        
        bid_depth = data.get("bid_depth", 0.0)
        ask_depth = data.get("ask_depth", 0.0)
        self.bid_depth_label.configure(text=f"{bid_depth:.4f}")
        self.ask_depth_label.configure(text=f"{ask_depth:.4f}")
        
        # Update orderbook display
        bids = data.get("bids", [])
        asks = data.get("asks", [])
        
        for i in range(5):
            if i < len(bids):
                bid = bids[i]
                self.bid_qty_labels[i].configure(text=f"{bid['quantity']:.4f}")
                self.bid_price_labels[i].configure(text=f"{bid['price']:.2f}")
            else:
                self.bid_qty_labels[i].configure(text="-")
                self.bid_price_labels[i].configure(text="-")
                
            if i < len(asks):
                ask = asks[i]
                self.ask_qty_labels[i].configure(text=f"{ask['quantity']:.4f}")
                self.ask_price_labels[i].configure(text=f"{ask['price']:.2f}")
            else:
                self.ask_qty_labels[i].configure(text="-")
                self.ask_price_labels[i].configure(text="-")
                
    def update_simulation_results(self, results: Dict[str, Any]) -> None:
        """
        Update simulation results display
        
        Args:
            results: Simulation results to display
        """
        if not results:
            return
            
        # Check for error
        if "error" in results:
            self.details_text.delete("1.0", tk.END)
            self.details_text.insert(tk.END, f"Error: {results['error']}")
            return
            
        # Update order details
        self.result_symbol_label.configure(text=results.get("symbol", "-"))
        self.result_side_label.configure(text=results.get("side", "-").upper())
        self.result_quantity_label.configure(text=f"{results.get('quantity', 0.0):.6f}")
        self.result_value_label.configure(text=f"${results.get('order_value', 0.0):.2f}")
        
        # Update cost breakdown
        slippage_pct = results.get("expected_slippage_pct", 0.0)
        slippage_cost = results.get("expected_slippage_cost", 0.0)
        self.result_slippage_label.configure(text=f"{slippage_pct:.4f}%")
        self.result_slippage_cost_label.configure(text=f"${slippage_cost:.2f}")
        
        impact = results.get("market_impact", {}).get("total_impact_pct", 0.0)
        impact_cost = results.get("market_impact", {}).get("impact_cost", 0.0)
        self.result_impact_label.configure(text=f"{impact:.4f}%")
        self.result_impact_cost_label.configure(text=f"${impact_cost:.2f}")
        
        effective_fee_rate = results.get("fees", {}).get("effective_fee_rate", 0.0) * 100
        fee_cost = results.get("fees", {}).get("total_fee", 0.0)
        self.result_fee_rate_label.configure(text=f"{effective_fee_rate:.4f}%")
        self.result_fee_cost_label.configure(text=f"${fee_cost:.2f}")
        
        # Update total costs
        net_cost = results.get("net_cost", 0.0)
        net_cost_pct = results.get("net_cost_pct", 0.0)
        self.result_net_cost_label.configure(text=f"${net_cost:.2f}")
        self.result_net_pct_label.configure(text=f"{net_cost_pct:.4f}%")
        
        # Update other metrics
        maker_proportion = results.get("fees", {}).get("maker_proportion", 0.0) * 100
        taker_proportion = results.get("fees", {}).get("taker_proportion", 0.0) * 100
        self.result_maker_taker_label.configure(text=f"{maker_proportion:.1f}% / {taker_proportion:.1f}%")
        
        latency = results.get("internal_latency_ms", 0.0)
        self.result_latency_label.configure(text=f"{latency:.2f} ms")
        
        # Update details text
        self.details_text.delete("1.0", tk.END)
        
        # Format the results dictionary as a readable string
        self._add_details_section("Order Parameters", {
            "Exchange": results.get("exchange", "-"),
            "Symbol": results.get("symbol", "-"),
            "Order Type": results.get("order_type", "-").capitalize(),
            "Side": results.get("side", "-").capitalize(),
            "Quantity": f"{results.get('quantity', 0.0):.6f}",
            "Order Value": f"${results.get('order_value', 0.0):.2f}",
            "Fee Tier": results.get("fee_tier", "-")
        })
        
        self._add_details_section("Market Conditions", {
            "Mid Price": f"${results.get('mid_price', 0.0):.2f}",
            "Spread": f"{results.get('spread', 0.0):.2f} (${results.get('spread_bps', 0.0):.1f} bps)",
            "Volatility": f"{results.get('volatility', 0.0):.2f}%"
        })
        
        self._add_details_section("Slippage", {
            "Expected Slippage": f"{slippage_pct:.4f}%",
            "Slippage Cost": f"${slippage_cost:.2f}"
        })
        
        market_impact = results.get("market_impact", {})
        self._add_details_section("Market Impact", {
            "Temporary Impact": f"{market_impact.get('temporary_impact_pct', 0.0):.4f}%",
            "Permanent Impact": f"{market_impact.get('permanent_impact_pct', 0.0):.4f}%",
            "Total Impact": f"{market_impact.get('total_impact_pct', 0.0):.4f}%",
            "Impact Cost": f"${market_impact.get('impact_cost', 0.0):.2f}",
            "Relative Size": f"{market_impact.get('relative_size', 0.0):.6f}",
            "% of ADV": f"{market_impact.get('pct_of_adv', 0.0):.4f}%"
        })
        
        fees = results.get("fees", {})
        self._add_details_section("Fees", {
            "Maker Proportion": f"{fees.get('maker_proportion', 0.0) * 100:.1f}%",
            "Taker Proportion": f"{fees.get('taker_proportion', 0.0) * 100:.1f}%",
            "Maker Fee Rate": f"{fees.get('maker_fee_rate', 0.0) * 100:.4f}%",
            "Taker Fee Rate": f"{fees.get('taker_fee_rate', 0.0) * 100:.4f}%",
            "Maker Fee": f"${fees.get('maker_fee', 0.0):.2f}",
            "Taker Fee": f"${fees.get('taker_fee', 0.0):.2f}",
            "Total Fee": f"${fees.get('total_fee', 0.0):.2f}",
            "Effective Fee Rate": f"{fees.get('effective_fee_rate', 0.0) * 100:.4f}%"
        })
        
        self._add_details_section("Total Costs", {
            "Net Cost": f"${net_cost:.2f}",
            "Net Cost Percentage": f"{net_cost_pct:.4f}%"
        })
        
        self._add_details_section("Performance", {
            "Internal Latency": f"{latency:.2f} ms",
            "Average Latency": f"{results.get('avg_latency_ms', 0.0):.2f} ms"
        })
        
        # Create simple visualization
        self._create_cost_breakdown_chart(results)
        
    def _add_details_section(self, title: str, data: Dict[str, str]) -> None:
        """
        Add a section to the details text
        
        Args:
            title: Section title
            data: Key-value pairs to display
        """
        self.details_text.insert(tk.END, f"{title}\n", "section_title")
        self.details_text.insert(tk.END, "-" * 50 + "\n")
        
        for key, value in data.items():
            self.details_text.insert(tk.END, f"{key}: ", "item_key")
            self.details_text.insert(tk.END, f"{value}\n", "item_value")
            
        self.details_text.insert(tk.END, "\n")
        
        # Configure tags
        self.details_text.tag_configure("section_title", font=("Arial", 10, "bold"))
        self.details_text.tag_configure("item_key", font=("Arial", 9))
        self.details_text.tag_configure("item_value", font=("Arial", 9, "bold"))
        
    def _create_cost_breakdown_chart(self, results: Dict[str, Any]) -> None:
        """
        Create a simple cost breakdown chart
        
        Args:
            results: Simulation results
        """
        # Clear canvas
        self.viz_canvas.delete("all")
        
        # Define chart dimensions
        chart_width = 400
        chart_height = 200
        margin_left = 50
        margin_top = 50
        margin_bottom = 50
        margin_right = 50
        
        # Calculate costs for the chart
        slippage_cost = results.get("expected_slippage_cost", 0.0)
        impact_cost = results.get("market_impact", {}).get("impact_cost", 0.0)
        fee_cost = results.get("fees", {}).get("total_fee", 0.0)
        
        total_cost = slippage_cost + impact_cost + fee_cost
        
        if total_cost <= 0:
            # Draw a message if there's no cost to display
            self.viz_canvas.create_text(
                margin_left + chart_width / 2,
                margin_top + chart_height / 2,
                text="No cost data to display",
                font=("Arial", 12),
                fill="gray"
            )
            return
            
        # Calculate proportions
        slippage_prop = slippage_cost / total_cost if total_cost > 0 else 0
        impact_prop = impact_cost / total_cost if total_cost > 0 else 0
        fee_prop = fee_cost / total_cost if total_cost > 0 else 0
        
        # Draw title
        self.viz_canvas.create_text(
            margin_left + chart_width / 2,
            margin_top / 2,
            text="Cost Breakdown",
            font=("Arial", 12, "bold"),
            fill="black"
        )
        
        # Draw chart background
        self.viz_canvas.create_rectangle(
            margin_left,
            margin_top,
            margin_left + chart_width,
            margin_top + chart_height,
            fill="white",
            outline="black"
        )
        
        # Draw bars
        bar_width = chart_width / 3
        
        # Slippage bar
        slippage_height = chart_height * slippage_prop
        self.viz_canvas.create_rectangle(
            margin_left,
            margin_top + chart_height - slippage_height,
            margin_left + bar_width,
            margin_top + chart_height,
            fill="blue",
            outline="black"
        )
        
        # Impact bar
        impact_height = chart_height * impact_prop
        self.viz_canvas.create_rectangle(
            margin_left + bar_width,
            margin_top + chart_height - impact_height,
            margin_left + 2 * bar_width,
            margin_top + chart_height,
            fill="red",
            outline="black"
        )
        
        # Fee bar
        fee_height = chart_height * fee_prop
        self.viz_canvas.create_rectangle(
            margin_left + 2 * bar_width,
            margin_top + chart_height - fee_height,
            margin_left + 3 * bar_width,
            margin_top + chart_height,
            fill="green",
            outline="black"
        )
        
        # Draw labels
        self.viz_canvas.create_text(
            margin_left + bar_width / 2,
            margin_top + chart_height + 15,
            text="Slippage",
            font=("Arial", 10),
            fill="black"
        )
        
        self.viz_canvas.create_text(
            margin_left + 1.5 * bar_width,
            margin_top + chart_height + 15,
            text="Market Impact",
            font=("Arial", 10),
            fill="black"
        )
        
        self.viz_canvas.create_text(
            margin_left + 2.5 * bar_width,
            margin_top + chart_height + 15,
            text="Fees",
            font=("Arial", 10),
            fill="black"
        )
        
        # Draw values
        self.viz_canvas.create_text(
            margin_left + bar_width / 2,
            margin_top + chart_height - slippage_height / 2,
            text=f"${slippage_cost:.2f}",
            font=("Arial", 9),
            fill="white" if slippage_height > 20 else "black"
        )
        
        self.viz_canvas.create_text(
            margin_left + 1.5 * bar_width,
            margin_top + chart_height - impact_height / 2,
            text=f"${impact_cost:.2f}",
            font=("Arial", 9),
            fill="white" if impact_height > 20 else "black"
        )
        
        self.viz_canvas.create_text(
            margin_left + 2.5 * bar_width,
            margin_top + chart_height - fee_height / 2,
            text=f"${fee_cost:.2f}",
            font=("Arial", 9),
            fill="white" if fee_height > 20 else "black"
        )
        
        # Draw total
        self.viz_canvas.create_text(
            margin_left + chart_width / 2,
            margin_top + chart_height + 35,
            text=f"Total Cost: ${total_cost:.2f}",
            font=("Arial", 10, "bold"),
            fill="black"
        )