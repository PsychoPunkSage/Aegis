"""
Exchange fee calculations
"""
import logging
from enum import Enum
from typing import Dict, Any, Optional
from utils.performance import measure_latency

class FeeTier(Enum):
    """OKX fee tiers"""
    TIER1 = "VIP1"  # Highest fees
    TIER2 = "VIP2"
    TIER3 = "VIP3"
    TIER4 = "VIP4"
    TIER5 = "VIP5"  # Lowest fees

class FeeCalculator:
    """
    Calculate exchange fees based on exchange rules and fee tiers
    """
    
    def __init__(self):
        """Initialize fee calculator with OKX fee structure"""
        self.logger = logging.getLogger(__name__)
        
        # OKX spot fee structure (maker/taker) as of 2024
        # These values are approximate and should be updated from their documentation
        self.fee_structure = {
            FeeTier.TIER1: {"maker": 0.00080, "taker": 0.00100},
            FeeTier.TIER2: {"maker": 0.00065, "taker": 0.00085},
            FeeTier.TIER3: {"maker": 0.00050, "taker": 0.00075},
            FeeTier.TIER4: {"maker": 0.00035, "taker": 0.00060},
            FeeTier.TIER5: {"maker": 0.00025, "taker": 0.00045},
        }
        
    @measure_latency("fee_calculation")
    def calculate_fees(self, order_value: float, fee_tier: FeeTier, maker_proportion: float = 0.0) -> Dict[str, float]:
        """
        Calculate fees for a given order
        
        Args:
            order_value: Total order value in quote currency
            fee_tier: Fee tier to apply
            maker_proportion: Proportion of order executed as maker (0.0 - 1.0)
            
        Returns:
            Dict[str, float]: Fee calculations
        """
        if order_value <= 0:
            return {
                "maker_fee_rate": 0.0,
                "taker_fee_rate": 0.0,
                "maker_fee": 0.0,
                "taker_fee": 0.0,
                "total_fee": 0.0,
                "effective_fee_rate": 0.0
            }
            
        # Ensure maker_proportion is between 0 and 1
        maker_proportion = max(0.0, min(1.0, maker_proportion))
        taker_proportion = 1.0 - maker_proportion
        
        # Get fee rates for the tier
        maker_fee_rate = self.fee_structure[fee_tier]["maker"]
        taker_fee_rate = self.fee_structure[fee_tier]["taker"]
        
        # Calculate maker and taker components
        maker_order_value = order_value * maker_proportion
        taker_order_value = order_value * taker_proportion
        
        maker_fee = maker_order_value * maker_fee_rate
        taker_fee = taker_order_value * taker_fee_rate
        
        # Calculate total fee
        total_fee = maker_fee + taker_fee
        
        # Calculate effective fee rate
        effective_fee_rate = total_fee / order_value if order_value > 0 else 0.0
        
        self.logger.debug(
            f"Fee calculation: "
            f"order_value={order_value:.2f}, "
            f"tier={fee_tier.name}, "
            f"maker_pct={maker_proportion:.2%}, "
            f"total_fee={total_fee:.4f}, "
            f"rate={effective_fee_rate:.6f}"
        )
        
        return {
            "maker_fee_rate": maker_fee_rate,
            "taker_fee_rate": taker_fee_rate,
            "maker_fee": maker_fee,
            "taker_fee": taker_fee,
            "total_fee": total_fee,
            "effective_fee_rate": effective_fee_rate
        }
        
    def get_tier_details(self, fee_tier: FeeTier) -> Dict[str, float]:
        """
        Get details for a specific fee tier
        
        Args:
            fee_tier: Fee tier to get details for
            
        Returns:
            Dict[str, float]: Fee tier details
        """
        return self.fee_structure[fee_tier]
        
    def get_all_tiers(self) -> Dict[str, Dict[str, float]]:
        """
        Get all fee tiers
        
        Returns:
            Dict[str, Dict[str, float]]: All fee tiers
        """
        return {tier.name: self.fee_structure[tier] for tier in self.fee_structure}