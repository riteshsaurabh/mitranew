"""
Formatting utility functions for consistent display of values in the MoneyMitra dashboard
"""

def format_currency(value, is_indian=False, decimal_places=2):
    """
    Format a currency value with the appropriate symbol and decimal places
    
    Args:
        value: The numeric value to format
        is_indian (bool): Whether to use Indian currency (₹)
        decimal_places (int): Number of decimal places to display
        
    Returns:
        str: Formatted currency string
    """
    if not isinstance(value, (int, float)):
        return "N/A"
        
    format_str = f"{{:.{decimal_places}f}}"
    if is_indian:
        return f"₹{format_str.format(value)}"
    else:
        return f"${format_str.format(value)}"

def format_percent(value, decimal_places=2):
    """
    Format a value as a percentage with specified decimal places
    
    Args:
        value: The numeric value to format (0.01 = 1%)
        decimal_places (int): Number of decimal places to display
        
    Returns:
        str: Formatted percentage string
    """
    if not isinstance(value, (int, float)):
        return "N/A"
        
    # Convert to percentage
    percent_value = value * 100 if value < 10 else value
    format_str = f"{{:.{decimal_places}f}}%"
    return format_str.format(percent_value)

def format_large_number(num, is_indian=False, decimal_places=2):
    """
    Format large numbers to K, M, B, T or Indian format (Lakhs, Crores)
    
    Args:
        num: Number to format
        is_indian (bool): Whether to use Indian currency notation
        decimal_places (int): Number of decimal places to display
        
    Returns:
        str: Formatted number
    """
    if not isinstance(num, (int, float)):
        return "N/A"
    
    format_str = f"{{:.{decimal_places}f}}"
    
    # Use Indian format if requested
    if is_indian:
        abs_num = abs(num)
        if abs_num >= 10000000:  # Crore (10 million)
            return f"₹{format_str.format(abs_num / 10000000)} Cr"
        elif abs_num >= 100000:  # Lakh (100 thousand)
            return f"₹{format_str.format(abs_num / 100000)} L"
        elif abs_num >= 1000:    # Thousand
            return f"₹{format_str.format(abs_num / 1000)} K"
        else:
            return f"₹{format_str.format(abs_num)}"
    
    # Western format
    abs_num = abs(num)
    if abs_num >= 1_000_000_000_000:
        return f"${format_str.format(abs_num / 1_000_000_000_000)}T"
    elif abs_num >= 1_000_000_000:
        return f"${format_str.format(abs_num / 1_000_000_000)}B"
    elif abs_num >= 1_000_000:
        return f"${format_str.format(abs_num / 1_000_000)}M"
    elif abs_num >= 1_000:
        return f"${format_str.format(abs_num / 1_000)}K"
    else:
        return f"${format_str.format(abs_num)}"

def format_number(num, decimal_places=2):
    """
    Format a number with specified decimal places
    
    Args:
        num: Number to format
        decimal_places (int): Number of decimal places to display
        
    Returns:
        str: Formatted number
    """
    if not isinstance(num, (int, float)):
        return "N/A"
        
    format_str = f"{{:.{decimal_places}f}}"
    return format_str.format(num)