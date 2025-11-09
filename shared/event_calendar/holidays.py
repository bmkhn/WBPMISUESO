from datetime import date
import holidays as pyholidays


def get_philippine_holidays(year=None):
    """
    Returns a dictionary of Philippine holidays for the given year.
    If no year is specified, returns holidays for the current year and next year.
    
    Returns:
        dict: {date: {'name': str, 'type': str}}
              type can be 'regular' or 'special'
    """
    if year is None:
        from datetime import datetime
        year = datetime.now().year

    # Use the holidays library for PH holidays
    ph_holidays = pyholidays.PH(years=year)
    holidays = {}
    for d, name in ph_holidays.items():
        # Try to infer type from name (not perfect, but matches your old logic)
        lower_name = name.lower()
        if 'special' in lower_name or 'chinese' in lower_name or 'black saturday' in lower_name or 'all saints' in lower_name or 'all souls' in lower_name or 'immaculate' in lower_name or 'eve' in lower_name:
            htype = 'special'
        else:
            htype = 'regular'
        holidays[d] = {'name': name, 'type': htype}
    return holidays


def _get_fixed_holidays(year):
    # Deprecated: now handled by holidays library
    return {}


def _get_movable_holidays(year):
    # Deprecated: now handled by holidays library
    return {}


def is_philippine_holiday(check_date):
    """
    Check if a given date is a Philippine holiday.
    
    Args:
        check_date (date): Date to check
    
    Returns:
        dict or None: Holiday info if it's a holiday, None otherwise
    """
    holidays = get_philippine_holidays(check_date.year)
    return holidays.get(check_date)


def get_holiday_name(check_date):
    """
    Get the name of the holiday on the given date.
    
    Args:
        check_date (date): Date to check
    
    Returns:
        str or None: Holiday name if it's a holiday, None otherwise
    """
    holiday_info = is_philippine_holiday(check_date)
    return holiday_info['name'] if holiday_info else None


def get_holidays_in_month(year, month):
    """
    Get all holidays in a specific month.
    
    Args:
        year (int): Year
        month (int): Month (1-12)
    
    Returns:
        dict: {date: {'name': str, 'type': str}}
    """
    all_holidays = get_philippine_holidays(year)
    return {
        d: info for d, info in all_holidays.items()
        if d.year == year and d.month == month
    }


def get_holidays_in_range(start_date, end_date):
    """
    Get all holidays within a date range.
    
    Args:
        start_date (date): Start date
        end_date (date): End date
    
    Returns:
        dict: {date: {'name': str, 'type': str}}
    """
    holidays = {}
    
    # Get holidays for all years in the range
    for year in range(start_date.year, end_date.year + 1):
        year_holidays = get_philippine_holidays(year)
        holidays.update({
            d: info for d, info in year_holidays.items()
            if start_date <= d <= end_date
        })
    
    return holidays
