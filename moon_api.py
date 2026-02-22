"""
Måne-API-klientmodul for LunarOrbit

Håndterer månefaseberegninger baseret på astronomiske algoritmer.
Henter også supplerende vejr/observationsdata fra Open Meteo API.

Dette modul indkapsler API-logikken efter Single Responsibility-princippet.
"""

import requests
from datetime import datetime
from typing import Dict, Optional


class MoonAPIClient:
    """
    Månefaseberegner ved hjælp af astronomiske algoritmer.
    
    Beregner månefase og belysning baseret på datoen.
    Bruger veletablerede algoritmer for nøjagtighed uden ekstern API-afhængighed.
    
    Integrerer også med Open Meteo API for at hente vejrdata og anden
    supplerende information for et komplet astronomisk billede.
    
    Denne tilgang er pålidelig både offline (månefaseberegninger) og online (API-data).
    """
    
    # Referencedato: 6. januar 2000 var nymåne (fase = 0)
    KNOWN_NEW_MOON = datetime(2000, 1, 6)
    SYNODIC_MONTH = 29.530588  # Dage i en månecyklus (præcis værdi)
    
    # Open Meteo API-endepunkter
    WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast"
    GEOCODING_API_URL = "https://geocoding-api.open-meteo.com/v1/search"
    
    def __init__(self, latitude: float = 55.6761, longitude: float = 12.5683, location_name: str = "København"):
        """
        Initialiserer Måneberegneren og API-klienten.
        
        Args:
            latitude (float): Observationsbreddegrad. Standard til København (55.6761)
            longitude (float): Observationslængdegrad. Standard til København (12.5683)
            location_name (str): Stednavnet til visning. Standard "København"
        """
        self.latitude = latitude
        self.longitude = longitude
        self.location_name = location_name
    
    def fetch_moon_data(self, date_string: str) -> Optional[Dict[str, any]]:
        """
        Beregner månefase og belysning for en bestemt dato.
        
        Args:
            date_string (str): Dato i format YYYY-MM-DD
        
        Returns:
            dict: Ordbog med nøgler:
                - 'illumination' (float): Månens belysning 0-100%
                - 'phase' (float): Månefaseværdi 0-1
            None: Hvis datoparsing mislykkes
        """
        try:
            # Parser datostrengen
            date_obj = datetime.strptime(date_string, "%Y-%m-%d")
            
            # Beregner dage siden kendt nymåne
            days_since_new_moon = (date_obj - self.KNOWN_NEW_MOON).days
            
            # Beregner position i nuværende månecyklus (0-1)
            days_in_cycle = days_since_new_moon % self.SYNODIC_MONTH
            phase = days_in_cycle / self.SYNODIC_MONTH
            
            # Beregner belysning (0-100%)
            # Fuld belysning ved fase 0,5, minimum ved 0 og 1
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
        Henter vejrdata for en bestemt dato fra Open Meteo API.
        
        Supplerer månefasedata med reelle vejrobservationer.
        
        Args:
            date_string (str): Dato i format YYYY-MM-DD
        
        Returns:
            dict: Ordbog med vejrinformation
            None: Hvis API-kald mislykkes
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
        Henter komplet måne- og vejrdata for en dato.
        
        Kombinerer månefaseberegninger med eventuel vejr-API-data.
        
        Args:
            date_string (str): Dato i format YYYY-MM-DD
        
        Returns:
            dict: Komplet databordbog med måne- og eventuel vejrinfo
        """
        # Henter månefasedata (virker altid - lokal beregning)
        moon_data = self.fetch_moon_data(date_string)
        
        # Henter vejrdata (valgfrit - kræver API-forbindelse)
        weather_data = self.fetch_weather_data(date_string)
        
        result = {
            "moon": moon_data,
            "weather": weather_data,
            "date": date_string
        }
        
        return result



