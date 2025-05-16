"""
Input panel for the Crypto Trade Simulator
"""
import tkinter as tk
from tkinter import ttk
import logging
from typing import Dict, Any, Optional, Callable
from models.fee_calculator import FeeTier

class InputPanel:
    """
    Input panel for simulation parameters
    """
    
    def __init__(self, parent, on_simulate: Optional[Callable] = None):
        """
        Initialize input panel
        
        Args:
            parent: Parent widget
            on_simulate: Callback for simulation button
        """
        self.logger = logging.getLogger(__name__)
        self.on_simulate = on_simulate
        
        # Create frame
        self.frame = ttk.LabelFrame(parent, text="Input Parameters")
        
        # Configure grid for the frame
        for i in range(4):
            self.frame.columnconfigure(i, weight=1)
        
        # Title
        title_label = ttk.Label(self.frame, text="Trade Parameters", font=("Arial", 14, "bold"))
        title_label.grid(row=0, column=0, columnspan=4, pady=10)
        
        # Create input fields
        self._create_input_fields()
        
        # Create simulate button
        simulate_button = ttk.Button(self.frame, text="Simulate Trade", command=self._on_simulate_clicked)
        simulate_button.grid(row=16, column=0, columnspan=4, pady=20)
        
    def _create_input_fields(self) -> None:
        """Create all input fields for the panel"""
        row = 1
        
        # Exchange selection
        ttk.Label(self.frame, text="Exchange:").grid(row=row, column=0, sticky="w", padx=10, pady=5)
        self.exchange_var = tk.StringVar(value="OKX")
        exchange_combo = ttk.Combobox(self.frame, textvariable=self.exchange_var, state="readonly")
        exchange_combo["values"] = ["OKX"]
        exchange_combo.grid(row=row, column=1, columnspan=3, sticky="ew", padx=10, pady=5)
        
        row += 1
        
        # Symbol selection
        ttk.Label(self.frame, text="Symbol:").grid(row=row, column=0, sticky="w", padx=10, pady=5)
        self.symbol_var = tk.StringVar(value="BTC-USDT-SWAP")
        symbol_combo = ttk.Combobox(self.frame, textvariable=self.symbol_var)
        symbol_combo["values"] = ["BTC-USDT-SWAP", "ETH-USDT-SWAP", "BTC-USDT", "ETH-USDT"]
        symbol_combo.grid(row=row, column=1, columnspan=3, sticky="ew", padx=10, pady=5)
        
        row += 1
        
        # Order type selection
        ttk.Label(self.frame, text="Order Type:").grid(row=row, column=0, sticky="w", padx=10, pady=5)
        self.order_type_var = tk.StringVar(value="market")
        ttk.Radiobutton(self.frame, text="Market", variable=self.order_type_var, value="market").grid(
            row=row, column=1, sticky="w", padx=10, pady=5
        )
        ttk.Radiobutton(self.frame, text="Limit", variable=self.order_type_var, value="limit").grid(
            row=row, column=2, sticky="w", padx=10, pady=5
        )
        
        row += 1
        
        # Trade side selection
        ttk.Label(self.frame, text="Side:").grid(row=row, column=0, sticky="w", padx=10, pady=5)
        self.side_var = tk.StringVar(value="buy")
        ttk.Radiobutton(self.frame, text="Buy", variable=self.side_var, value="buy").grid(
            row=row, column=1, sticky="w", padx=10, pady=5
        )
        ttk.Radiobutton(self.frame, text="Sell", variable=self.side_var, value="sell").grid(
            row=row, column=2, sticky="w", padx=10, pady=5
        )
        
        row += 1
        
        # Quantity input
        ttk.Label(self.frame, text="Quantity (BTC):").grid(row=row, column=0, sticky="w", padx=10, pady=5)
        self.quantity_var = tk.StringVar(value="0.1")
        quantity_entry = ttk.Entry(self.frame, textvariable=self.quantity_var)
        quantity_entry.grid(row=row, column=1, columnspan=3, sticky="ew", padx=10, pady=5)
        
        row += 1
        
        # Quote currency quantity input
        ttk.Label(self.frame, text="OR Quantity (USDT):").grid(row=row, column=0, sticky="w", padx=10, pady=5)
        self.quantity_quote_var = tk.StringVar(value="1000")
        quantity_quote_entry = ttk.Entry(self.frame, textvariable=self.quantity_quote_var)
        quantity_quote_entry.grid(row=row, column=1, columnspan=3, sticky="ew", padx=10, pady=5)
        
        row += 1
        
        # Separator
        separator = ttk.Separator(self.frame, orient="horizontal")
        separator.grid(row=row, column=0, columnspan=4, sticky="ew", padx=10, pady=15)
        
        row += 1
        
        # Market parameters subtitle
        ttk.Label(self.frame, text="Market Parameters", font=("Arial", 12, "bold")).grid(
            row=row, column=0, columnspan=4, pady=5
        )
        
        row += 1
        
        # Volatility input
        ttk.Label(self.frame, text="Volatility (%):").grid(row=row, column=0, sticky="w", padx=10, pady=5)
        self.volatility_var = tk.StringVar(value="2.5")
        volatility_entry = ttk.Entry(self.frame, textvariable=self.volatility_var)
        volatility_entry.grid(row=row, column=1, columnspan=3, sticky="ew", padx=10, pady=5)
        
        row += 1
        
        # Fee tier selection
        ttk.Label(self.frame, text="Fee Tier:").grid(row=row, column=0, sticky="w", padx=10, pady=5)
        self.fee_tier_var = tk.StringVar(value=FeeTier.TIER1.name)
        fee_tier_combo = ttk.Combobox(self.frame, textvariable=self.fee_tier_var, state="readonly")
        fee_tier_combo["values"] = [tier.name for tier in FeeTier]
        fee_tier_combo.grid(row=row, column=1, columnspan=3, sticky="ew", padx=10, pady=5)
        
        row += 1
        
        # Add some advanced parameters
        
        # Separator
        separator = ttk.Separator(self.frame, orient="horizontal")
        separator.grid(row=row, column=0, columnspan=4, sticky="ew", padx=10, pady=15)
        
        row += 1
        
        # Advanced parameters subtitle (collapsed by default)
        self.show_advanced_var = tk.BooleanVar(value=False)
        advanced_check = ttk.Checkbutton(
            self.frame, 
            text="Show Advanced Parameters", 
            variable=self.show_advanced_var,
            command=self._toggle_advanced_params
        )
        advanced_check.grid(row=row, column=0, columnspan=4, sticky="w", padx=10, pady=5)
        
        row += 1
        
        # Advanced parameters frame (hidden by default)
        self.advanced_frame = ttk.Frame(self.frame)
        self.advanced_frame.grid(row=row, column=0, columnspan=4, sticky="nsew", padx=10, pady=5)
        self.advanced_frame.grid_remove()  # Hide the frame initially
        
        # Add advanced parameters to the advanced frame
        ttk.Label(self.advanced_frame, text="Simulation Complexity:").grid(
            row=0, column=0, sticky="w", padx=10, pady=5
        )
        self.complexity_var = tk.StringVar(value="standard")
        ttk.Radiobutton(
            self.advanced_frame, text="Standard", variable=self.complexity_var, value="standard"
        ).grid(row=0, column=1, sticky="w", padx=10, pady=5)
        ttk.Radiobutton(
            self.advanced_frame, text="Advanced", variable=self.complexity_var, value="advanced"
        ).grid(row=0, column=2, sticky="w", padx=10, pady=5)
        
        ttk.Label(self.advanced_frame, text="Market Impact Model:").grid(
            row=1, column=0, sticky="w", padx=10, pady=5
        )
        self.impact_model_var = tk.StringVar(value="almgren-chriss")
        impact_model_combo = ttk.Combobox(self.advanced_frame, textvariable=self.impact_model_var, state="readonly")
        impact_model_combo["values"] = ["almgren-chriss", "linear", "square-root"]
        impact_model_combo.grid(row=1, column=1, columnspan=2, sticky="ew", padx=10, pady=5)
        
    def _toggle_advanced_params(self) -> None:
        """Toggle visibility of advanced parameters"""
        if self.show_advanced_var.get():
            self.advanced_frame.grid()
        else:
            self.advanced_frame.grid_remove()
            
    def _on_simulate_clicked(self) -> None:
        """Handle simulate button click"""
        # Collect parameters
        params = self._get_parameters()
        
        # Validate parameters
        if self._validate_parameters(params):
            # Call the callback if provided
            if self.on_simulate:
                self.on_simulate(params)
        
    def _get_parameters(self) -> Dict[str, Any]:
        """
        Get parameters from input fields
        
        Returns:
            Dict[str, Any]: Parameter values
        """
        # Parse numeric inputs
        try:
            quantity = float(self.quantity_var.get()) if self.quantity_var.get() else 0.0
        except ValueError:
            quantity = 0.0
            
        try:
            quantity_quote = float(self.quantity_quote_var.get()) if self.quantity_quote_var.get() else 0.0
        except ValueError:
            quantity_quote = 0.0
            
        try:
            volatility = float(self.volatility_var.get()) if self.volatility_var.get() else 2.5
        except ValueError:
            volatility = 2.5
        
        # Create parameters dictionary
        params = {
            "exchange": self.exchange_var.get(),
            "symbol": self.symbol_var.get(),
            "order_type": self.order_type_var.get(),
            "side": self.side_var.get(),
            "quantity": quantity,
            "quantity_quote": quantity_quote,
            "volatility": volatility,
            "fee_tier": FeeTier[self.fee_tier_var.get()],
            
            # Advanced parameters
            "complexity": self.complexity_var.get(),
            "impact_model": self.impact_model_var.get()
        }
        
        return params
    
    def _validate_parameters(self, params: Dict[str, Any]) -> bool:
        """
        Validate parameter values
        
        Args:
            params: Parameters to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        # Check that at least one quantity field is filled
        if params["quantity"] <= 0 and params["quantity_quote"] <= 0:
            tk.messagebox.showerror("Invalid Input", "Please enter a quantity in either BTC or USDT.")
            return False
            
        # Check volatility
        if params["volatility"] <= 0:
            tk.messagebox.showerror("Invalid Input", "Volatility must be positive.")
            return False
            
        return True