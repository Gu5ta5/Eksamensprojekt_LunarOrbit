"""
Boilerplate Module for LunarOrbit

Contains utility functions, constants, and helper classes.
This module provides reusable functionality for the application.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Tuple


class DateUtils:
    """Utility functions for date and time handling."""
    
    @staticmethod
    def get_current_date() -> str:
        """
        Get today's date in YYYY-MM-DD format.
        
        Returns:
            str: Current date formatted as YYYY-MM-DD
        """
        return datetime.now().strftime("%Y-%m-%d")
    
    @staticmethod
    def get_current_time() -> str:
        """
        Get current time in HH:MM:SS format.
        
        Returns:
            str: Current time formatted as HH:MM:SS
        """
        return datetime.now().strftime("%H:%M:%S")
    
    @staticmethod
    def format_date(date_obj: datetime) -> str:
        """
        Format a datetime object to YYYY-MM-DD.
        
        Args:
            date_obj (datetime): Date object to format
        
        Returns:
            str: Formatted date string
        """
        return date_obj.strftime("%Y-%m-%d")
    
    @staticmethod
    def get_date_range(start_date: datetime, days: int = 30) -> List[str]:
        """
        Generate a list of dates starting from start_date for N days.
        
        Args:
            start_date (datetime): Starting date
            days (int): Number of days to generate
        
        Returns:
            list: List of date strings in YYYY-MM-DD format
        """
        date_list = []
        for i in range(days):
            date = start_date + timedelta(days=i)
            date_list.append(date.strftime("%Y-%m-%d"))
        return date_list


class MoonConstants:
    """Constants related to moon observations."""
    
    # Copenhagen coordinates (default observation point)
    LATITUDE = 55.6761
    LONGITUDE = 12.5683
    
    # Moon cycle constants
    SYNODIC_MONTH = 29.53  # Days in a lunar cycle
    
    # Phase names in Danish
    PHASE_NAMES = {
        0: "Nymåne",
        1: "Voksende halvmåne",
        2: "Første kvarter",
        3: "Voksende gibbous",
        4: "Fuldmåne",
        5: "Aftagende gibbous",
        6: "Sidste kvarter",
        7: "Aftagende halvmåne"
    }


class Validators:
    """Input validation utilities."""
    
    @staticmethod
    def is_valid_date(date_string: str) -> bool:
        """
        Validate if string is a valid date in YYYY-MM-DD format.
        
        Args:
            date_string (str): Date string to validate
        
        Returns:
            bool: True if valid date format, False otherwise
        """
        try:
            datetime.strptime(date_string, "%Y-%m-%d")
            return True
        except ValueError:
            return False
    
    @staticmethod
    def is_valid_phase(phase_value: float) -> bool:
        """
        Validate if phase value is in valid range (0-1).
        
        Args:
            phase_value (float): Phase value to validate
        
        Returns:
            bool: True if 0 <= phase_value <= 1
        """
        return 0 <= phase_value <= 1
    
    @staticmethod
    def is_valid_illumination(illumination: float) -> bool:
        """
        Validate if illumination value is in valid range (0-100).
        
        Args:
            illumination (float): Illumination percentage to validate
        
        Returns:
            bool: True if 0 <= illumination <= 100
        """
        return 0 <= illumination <= 100


class Formatters:
    """Output formatting utilities."""
    
    @staticmethod
    def format_illumination(illumination: float) -> str:
        """
        Format illumination value as percentage string.
        
        Args:
            illumination (float): Illumination percentage (0-100)
        
        Returns:
            str: Formatted string (e.g., "75%")
        """
        return f"{int(illumination)}%"
    
    @staticmethod
    def format_coordinates(latitude: float, longitude: float) -> str:
        """
        Format coordinates for display.
        
        Args:
            latitude (float): Latitude value
            longitude (float): Longitude value
        
        Returns:
            str: Formatted coordinates string
        """
        return f"{latitude:.4f}°N, {longitude:.4f}°E"

class MoonEngine:
    """
    Moon phase calculation and transformation engine.
    
    Converts raw moon phase values from API into human-readable names
    and provides phase-related calculations.
    """
    
    # Synodic month (lunar cycle) in days
    SYNODIC_MONTH = 29.53
    
    @staticmethod
    def get_phase_name(phase_value: float) -> str:
        """
        Convert API phase value (0-1) to human-readable phase name.
        
        The moon cycle is divided into 8 phases:
        - 0.0-0.125: Nymåne (New Moon)
        - 0.125-0.25: Voksende halvmåne (Waxing Crescent)
        - 0.25-0.375: Første kvarter (First Quarter)
        - 0.375-0.5: Voksende gibbous (Waxing Gibbous)
        - 0.5-0.625: Fuldmåne (Full Moon)
        - 0.625-0.75: Aftagende gibbous (Waning Gibbous)
        - 0.75-0.875: Sidste kvarter (Last Quarter)
        - 0.875-1.0: Aftagende halvmåne (Waning Crescent)
        
        Args:
            phase_value (float): Phase value from API (0-1)
        
        Returns:
            str: Human-readable phase name in Danish
        """
        if phase_value < 0.125:
            return "Nymåne"
        elif phase_value < 0.25:
            return "Voksende halvmåne"
        elif phase_value < 0.375:
            return "Første kvarter"
        elif phase_value < 0.5:
            return "Voksende gibbous"
        elif phase_value < 0.625:
            return "Fuldmåne"
        elif phase_value < 0.75:
            return "Aftagende gibbous"
        elif phase_value < 0.875:
            return "Sidste kvarter"
        else:
            return "Aftagende halvmåne"
    
    @staticmethod
    def format_moon_data(api_data: Dict[str, float]) -> Dict[str, any]:
        """
        Transform raw API data into formatted display data.
        
        Args:
            api_data (dict): Raw data from MoonAPIClient with keys:
                - 'illumination': float (0-100)
                - 'phase': float (0-1)
        
        Returns:
            dict: Formatted data with keys:
                - 'illumination': float (0-100)
                - 'illumination_percent': str (e.g., "75%")
                - 'phase': float (0-1)
                - 'phase_name': str (e.g., "Fuldmåne")
        """
        if not api_data:
            return {
                "illumination": 0,
                "illumination_percent": "0%",
                "phase": 0,
                "phase_name": "Ukendt"
            }
        
        illumination = api_data.get("illumination", 0)
        phase = api_data.get("phase", 0)
        
        return {
            "illumination": illumination,
            "illumination_percent": f"{int(illumination)}%",
            "phase": phase,
            "phase_name": MoonEngine.get_phase_name(phase)
        }
    
    @staticmethod
    def calculate_days_to_full_moon(phase_value: float) -> float:
        """
        Calculate estimated days until next full moon.
        
        Based on synodic month of 29.53 days.
        
        Args:
            phase_value (float): Current phase value (0-1)
        
        Returns:
            float: Approximate days until full moon
        """
        days_into_cycle = phase_value * MoonEngine.SYNODIC_MONTH
        days_to_full = (0.5 * MoonEngine.SYNODIC_MONTH) - days_into_cycle
        
        if days_to_full < 0:
            days_to_full += MoonEngine.SYNODIC_MONTH
        
        return round(days_to_full, 1)


class MoonVisuals:
    """
    Moon phase visualization handler.
    
    Maps moon phase values (0-1) to visual representations (emojis).
    Provides consistent visual feedback for different moon phases.
    """
    
    # Moon phase emojis for 8 distinct phases
    MOON_EMOJIS = {
        0: "🌑",  # Nymåne (New Moon)
        1: "🌒",  # Voksende halvmåne (Waxing Crescent)
        2: "🌓",  # Første kvarter (First Quarter)
        3: "🌔",  # Voksende gibbous (Waxing Gibbous)
        4: "🌕",  # Fuldmåne (Full Moon)
        5: "🌖",  # Aftagende gibbous (Waning Gibbous)
        6: "🌗",  # Sidste kvarter (Last Quarter)
        7: "🌘",  # Aftagende halvmåne (Waning Crescent),
    }
    
    PHASE_RANGES = [
        (0.0, 0.125, 0, "Nymåne"),
        (0.125, 0.25, 1, "Voksende halvmåne"),
        (0.25, 0.375, 2, "Første kvarter"),
        (0.375, 0.5, 3, "Voksende gibbous"),
        (0.5, 0.625, 4, "Fuldmåne"),
        (0.625, 0.75, 5, "Aftagende gibbous"),
        (0.75, 0.875, 6, "Sidste kvarter"),
        (0.875, 1.0, 7, "Aftagende halvmåne"),
    ]
    
    @staticmethod
    def get_moon_emoji(phase: float) -> str:
        """
        Get emoji representation for a moon phase value.
        
        Args:
            phase (float): Phase value (0-1)
        
        Returns:
            str: Moon emoji character
        """
        # Ensure phase is in valid range
        phase = phase % 1.0
        
        for min_phase, max_phase, emoji_key, _ in MoonVisuals.PHASE_RANGES:
            if min_phase <= phase < max_phase:
                return MoonVisuals.MOON_EMOJIS[emoji_key]
        
        # Fallback to waning crescent if outside normal ranges
        return MoonVisuals.MOON_EMOJIS[7]
    
    @staticmethod
    def get_phase_info(phase: float) -> Dict[str, any]:
        """
        Get complete phase information including emoji and name.
        
        Args:
            phase (float): Phase value (0-1)
        
        Returns:
            dict: Dictionary with keys:
                - 'emoji': str (emoji character)
                - 'name': str (phase name in Danish)
                - 'index': int (phase index 0-7)
        """
        phase = phase % 1.0
        
        for min_phase, max_phase, emoji_key, phase_name in MoonVisuals.PHASE_RANGES:
            if min_phase <= phase < max_phase:
                return {
                    "emoji": MoonVisuals.MOON_EMOJIS[emoji_key],
                    "name": phase_name,
                    "index": emoji_key
                }
        
        # Fallback
        return {
            "emoji": MoonVisuals.MOON_EMOJIS[7],
            "name": "Aftagende halvmåne",
            "index": 7
        }
    
    @staticmethod
    def get_large_moon_display(phase: float, size: int = 3) -> str:
        """
        Get enlarged moon emoji for prominent display.
        
        Repeats emoji character to make it visually larger.
        
        Args:
            phase (float): Phase value (0-1)
            size (int): Number of times to repeat emoji (1-5)
        
        Returns:
            str: Enlarged moon emoji display
        """
        emoji = MoonVisuals.get_moon_emoji(phase)
        size = max(1, min(5, size))  # Clamp size between 1-5
        return emoji * size