"""
Export utilities for simulation results
"""
import csv
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

def export_results_to_csv(results: Dict[str, Any], filename: Optional[str] = None) -> str:
    """
    Export simulation results to CSV
    
    Args:
        results: Simulation results
        filename: Optional filename, defaults to auto-generated
        
    Returns:
        str: Path to the exported file
    """
    logger = logging.getLogger(__name__)
    
    # Generate filename if not provided
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        symbol = results.get("symbol", "unknown")
        side = results.get("side", "unknown")
        filename = f"simulation_{symbol}_{side}_{timestamp}.csv"
        
    try:
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header
            writer.writerow(["Parameter", "Value"])
            
            # Write input parameters
            writer.writerow(["Input Parameters", ""])
            writer.writerow(["Exchange", results.get("exchange", "")])
            writer.writerow(["Symbol", results.get("symbol", "")])
            writer.writerow(["Order Type", results.get("order_type", "")])
            writer.writerow(["Side", results.get("side", "")])
            writer.writerow(["Quantity", results.get("quantity", "")])
            writer.writerow(["Order Value", results.get("order_value", "")])
            writer.writerow(["Fee Tier", results.get("fee_tier", "")])
            
            # Write market conditions
            writer.writerow(["Market Conditions", ""])
            writer.writerow(["Mid Price", results.get("mid_price", "")])
            writer.writerow(["Spread", results.get("spread", "")])
            writer.writerow(["Spread (bps)", results.get("spread_bps", "")])
            writer.writerow(["Volatility", results.get("volatility", "")])
            
            # Write simulation results
            writer.writerow(["Simulation Results", ""])
            writer.writerow(["Slippage (%)", results.get("expected_slippage_pct", "")])
            writer.writerow(["Slippage Cost", results.get("expected_slippage_cost", "")])
            
            # Write market impact
            market_impact = results.get("market_impact", {})
            writer.writerow(["Market Impact", ""])
            writer.writerow(["Temporary Impact (%)", market_impact.get("temporary_impact_pct", "")])
            writer.writerow(["Permanent Impact (%)", market_impact.get("permanent_impact_pct", "")])
            writer.writerow(["Total Impact (%)", market_impact.get("total_impact_pct", "")])
            writer.writerow(["Impact Cost", market_impact.get("impact_cost", "")])
            
            # Write fees
            fees = results.get("fees", {})
            writer.writerow(["Fees", ""])
            writer.writerow(["Maker Proportion", fees.get("maker_proportion", "")])
            writer.writerow(["Taker Proportion", fees.get("taker_proportion", "")])
            writer.writerow(["Maker Fee Rate", fees.get("maker_fee_rate", "")])
            writer.writerow(["Taker Fee Rate", fees.get("taker_fee_rate", "")])
            writer.writerow(["Maker Fee", fees.get("maker_fee", "")])
            writer.writerow(["Taker Fee", fees.get("taker_fee", "")])
            writer.writerow(["Total Fee", fees.get("total_fee", "")])
            
            # Write total costs
            writer.writerow(["Total Costs", ""])
            writer.writerow(["Net Cost", results.get("net_cost", "")])
            writer.writerow(["Net Cost (%)", results.get("net_cost_pct", "")])
            
            # Write performance metrics
            writer.writerow(["Performance", ""])
            writer.writerow(["Internal Latency (ms)", results.get("internal_latency_ms", "")])
            
        logger.info(f"Exported simulation results to {filename}")
        return filename
        
    except Exception as e:
        logger.error(f"Error exporting results to CSV: {e}")
        return ""

def export_batch_results_to_csv(batch_results: Dict[str, Any], filename: Optional[str] = None) -> str:
    """
    Export batch simulation results to CSV
    
    Args:
        batch_results: Batch simulation results
        filename: Optional filename, defaults to auto-generated
        
    Returns:
        str: Path to the exported file
    """
    logger = logging.getLogger(__name__)
    
    # Generate filename if not provided
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        batch_id = batch_results.get("batch_id", "unknown")
        filename = f"batch_{batch_id}_{timestamp}.csv"
        
    try:
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            
            # Extract individual results
            results = batch_results.get("results", [])
            
            if not results:
                logger.warning("No results to export")
                return filename
                
            # Get headers from first result
            first_result = results[0].get("result", {})
            
            # Create parameter headers
            param_headers = list(results[0].get("variation", {}).keys())
            
            # Create result headers
            result_headers = [
                "Exchange", "Symbol", "Side", "Order Type",
                "Slippage (%)", "Impact (%)", "Fees (%)", "Net Cost (%)"
            ]
            
            # Write header row
            writer.writerow(param_headers + result_headers)
            
            # Write data rows
            for item in results:
                variation = item.get("variation", {})
                result = item.get("result", {})
                
                # Extract parameter values
                param_values = [variation.get(header, "") for header in param_headers]
                
                # Extract result values
                market_impact = result.get("market_impact", {})
                fees = result.get("fees", {})
                
                result_values = [
                    result.get("exchange", ""),
                    result.get("symbol", ""),
                    result.get("side", ""),
                    result.get("order_type", ""),
                    result.get("expected_slippage_pct", ""),
                    market_impact.get("total_impact_pct", ""),
                    fees.get("effective_fee_rate", "") * 100 if fees.get("effective_fee_rate") is not None else "",
                    result.get("net_cost_pct", "")
                ]
                
                # Write the row
                writer.writerow(param_values + result_values)
                
        logger.info(f"Exported batch results to {filename}")
        return filename
        
    except Exception as e:
        logger.error(f"Error exporting batch results to CSV: {e}")
        return ""

def export_results_to_json(results: Dict[str, Any], filename: Optional[str] = None) -> str:
    """
    Export simulation results to JSON
    
    Args:
        results: Simulation results
        filename: Optional filename, defaults to auto-generated
        
    Returns:
        str: Path to the exported file
    """
    logger = logging.getLogger(__name__)
    
    # Generate filename if not provided
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        symbol = results.get("symbol", "unknown")
        side = results.get("side", "unknown")
        filename = f"simulation_{symbol}_{side}_{timestamp}.json"
        
    try:
        with open(filename, 'w') as jsonfile:
            json.dump(results, jsonfile, indent=2)
            
        logger.info(f"Exported simulation results to {filename}")
        return filename
        
    except Exception as e:
        logger.error(f"Error exporting results to JSON: {e}")
        return ""