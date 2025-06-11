from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Union, Dict, List
import re

def format_currency(amount: Union[Decimal, float, str]) -> str:
    """Format a number as currency (e.g., 1234.56 -> TSHS 1,234.56)."""
    if isinstance(amount, str):
        amount = Decimal(amount)
    return f"TSHS {amount:,.2f}"

def format_date(dt: Union[datetime, date]) -> str:
    """Format a date/datetime object to a readable string."""
    if isinstance(dt, datetime):
        return dt.strftime("%d %b %Y, %I:%M %p")
    return dt.strftime("%d %b %Y")

def validate_email(email: str) -> bool:
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_phone(phone: str) -> bool:
    """Validate phone number format (Kenyan)."""
    pattern = r'^(?:\+254|0)[17]\d{8}$'
    return bool(re.match(pattern, phone))

def calculate_total(items: List[Dict]) -> Decimal:
    """Calculate total amount from a list of items with quantity and price."""
    return sum(Decimal(str(item['quantity'])) * Decimal(str(item['price'])) for item in items)

def generate_report_filename(report_type: str, start_date: date, end_date: date) -> str:
    """Generate a filename for reports."""
    return f"{report_type}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.pdf"

def get_date_range_filter(range_type: str) -> tuple[datetime, datetime]:
    """
    Get start and end dates for common date ranges.
    
    Args:
        range_type (str): One of 'today', 'week', 'month', 'year'
        
    Returns:
        tuple[datetime, datetime]: Start and end datetime objects
    """
    today = datetime.now()
    start_date = None
    end_date = datetime.now()

    if range_type == 'today':
        start_date = today.replace(hour=0, minute=0, second=0, microsecond=0)
    elif range_type == 'week':
        start_date = today.replace(hour=0, minute=0, second=0, microsecond=0)
        start_date = start_date - timedelta(days=start_date.weekday())
    elif range_type == 'month':
        start_date = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif range_type == 'year':
        start_date = today.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        raise ValueError("Invalid range_type. Must be one of: today, week, month, year")

    return start_date, end_date

def format_stock_status(current: int, minimum: int) -> tuple[str, str]:
    """
    Get stock status and appropriate color.
    
    Returns:
        tuple[str, str]: (status_text, color_class)
    """
    if current <= 0:
        return "Out of Stock", "text-red-600"
    elif current <= minimum:
        return "Low Stock", "text-yellow-600"
    return "In Stock", "text-green-600" 