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

def format_indian_numbers(num, decimal_places=2, in_lakhs=False, in_crores=False):
    """
    Format numbers with Indian numbering system (commas after 3 digits, then every 2 digits)
    
    Args:
        num: Number to format
        decimal_places (int): Number of decimal places to display
        in_lakhs (bool): Whether to display in lakhs (divide by 100,000)
        in_crores (bool): Whether to display in crores (divide by 10,000,000)
        
    Returns:
        str: Formatted number with Indian style commas
    """
    if not isinstance(num, (int, float)):
        return "N/A"
    
    # Determine if value should be displayed in lakhs or crores
    if in_crores:
        num = num / 10000000
        suffix = " Cr"
    elif in_lakhs:
        num = num / 100000
        suffix = " L"
    else:
        # Keep as is for thousands (K) display
        suffix = " K"
        
    # Format with the specified decimal places
    formatted_num = f"{num:.{decimal_places}f}"
    
    # Split the number into integer and decimal parts
    # Handle cases where there might not be a decimal part
    parts = formatted_num.split(".")
    integer_part = parts[0]
    decimal_part = parts[1] if len(parts) > 1 else "00"
    
    # Format the integer part with Indian style commas
    # (e.g., 10,00,00,000 instead of 100,000,000)
    result = ""
    if len(integer_part) <= 3:
        result = integer_part
    else:
        # Add the last 3 digits
        result = integer_part[-3:]
        # Add the rest of the digits in groups of 2
        for i in range(len(integer_part) - 3, 0, -2):
            if i-2 >= 0:
                result = integer_part[i-2:i] + "," + result
            else:
                result = integer_part[:i] + "," + result
    
    # Add the decimal part back
    if decimal_places > 0:
        result = result + "." + decimal_part
        
    return result + suffix