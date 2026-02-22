"""
Moon API Client Module for LunarOrbit

Handles moon phase calculations based on astronomical algorithms.
Also fetches supplementary weather/observation data from Open Meteo API.

This module encapsulates the API logic following the Single Responsibility Principle.
"""

import requests
from datetime import datetime
from typing import Dict, Optional


class MoonAPIClient:
    """
    Moon phase calculator using astronomical algorithms.
    
    Calculates moon phase and illumination based on the date.
    Uses well-established algorithms for accuracy without external API dependency.
    
    Also integrates with Open Meteo API to fetch weather data and other
    supplementary information for a complete astronomical picture.
    
    This approach is reliable both offline (moon calculations) and online (API data).
    """
    
    # Reference date: January 6, 2000 was a New Moon (phase = 0)
    KNOWN_NEW_MOON = datetime(2000, 1, 6)
    SYNODIC_MONTH = 29.530588  # Days in a lunar cycle (precise value)
    
    # Open Meteo API endpoints
    WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast"
    GEOCODING_API_URL = "https://geocoding-api.open-meteo.com/v1/search"
    
    def __init__(self, latitude: float = 55.6761, longitude: float = 12.5683, location_name: str = "København"):
        """
        Initialize the Moon Calculator and API Client.
        
        Args:
            latitude (float): Observation latitude. Defaults to Copenhagen (55.6761)
            longitude (float): Observation longitude. Defaults to Copenhagen (12.5683)
            location_name (str): Location name for display. Defaults to "København"
        """
        self.latitude = latitude
        self.longitude = longitude
        self.location_name = location_name
    
    def fetch_moon_data(self, date_string: str) -> Optional[Dict[str, any]]:
        """
        Calculate moon phase and illumination for a specific date.
        
        Args:
            date_string (str): Date in format YYYY-MM-DD
        
        Returns:
            dict: Dictionary with keys:
                - 'illumination' (float): Moon illumination 0-100%
                - 'phase' (float): Moon phase value 0-1
            None: If date parsing fails
        """
        try:
            # Parse the date string
            date_obj = datetime.strptime(date_string, "%Y-%m-%d")
            
            # Calculate days since known new moon
            days_since_new_moon = (date_obj - self.KNOWN_NEW_MOON).days
            
            # Calculate position in current lunar cycle (0-1)
            days_in_cycle = days_since_new_moon % self.SYNODIC_MONTH
            phase = days_in_cycle / self.SYNODIC_MONTH
            
            # Calculate illumination (0-100%)
            # Full illumination at phase 0.5, minimum at 0 and 1
            if phase < 0.5:
                illumination = 100 * (2 * phase)
            else:
                illumination = 100 * (2 * (1 - phase))
            
            return {
                "illumination": float(illumination),
                "phase": float(phase)
            }
        
        except ValueError as e:
            print(f"Fejl: Ugyldigt datoformat. Forventet YYYY-MM-DD: {e}")
            return None
        
        except Exception as e:
            print(f"Uventet fejl ved beregning af månedata: {e}")
            return None
    
    def fetch_weather_data(self, date_string: str) -> Optional[Dict[str, any]]:
        """
        Fetch weather data for a specific date from Open Meteo API.
        
        Supplements moon data with real weather observations.
        
        Args:
            date_string (str): Date in format YYYY-MM-DD
        
        Returns:
            dict: Dictionary with weather information
            None: If API call fails
        """
        try:
            params = {
                "latitude": self.latitude,
                "longitude": self.longitude,
                "start_date": date_string,
                "end_date": date_string,
                "daily": "temperature_2m_max,temperature_2m_min,cloud_cover_max,weather_code",
                "timezone": "auto"
            }
            
            response = requests.get(
                self.WEATHER_API_URL,
                params=params,
                timeout=5
            )
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("daily") and len(data["daily"].get("time", [])) > 0:
                return {
                    "temperature_max": data["daily"]["temperature_2m_max"][0],
                    "temperature_min": data["daily"]["temperature_2m_min"][0],
                    "cloud_cover": data["daily"]["cloud_cover_max"][0],
                    "weather_code": data["daily"]["weather_code"][0],
                    "location": self.location_name
                }
            return None
        
        except requests.exceptions.RequestException as e:
            print(f"Advarsel: Kunne ikke hente vejrdata: {e}")
            return None
        
        except Exception as e:
            print(f"Uventet fejl ved hentning af vejrdata: {e}")
            return None
    
    def fetch_complete_data(self, date_string: str) -> Dict[str, any]:
        """
        Fetch complete moon and weather data for a date.
        
        Combines moon calculations with optional weather API data.
        
        Args:
            date_string (str): Date in format YYYY-MM-DD
        
        Returns:
            dict: Complete data dictionary with moon and optional weather info
        """
        # Get moon data (always works - local calculation)
        moon_data = self.fetch_moon_data(date_string)
        
        # Get weather data (optional - requires API connection)
        weather_data = self.fetch_weather_data(date_string)
        
        result = {
            "moon": moon_data,
            "weather": weather_data,
            "date": date_string
        }
        
        return result



