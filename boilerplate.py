"""
Boilerplate-modul for LunarOrbit

Indeholder hjælpefunktioner, konstanter og hjælperklasser.
Dette modul giver genbrugelig funktionalitet til applikationen.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Tuple


class DateUtils:
    """Hjælpefunktioner til dato- og tidshåndtering."""
    
    @staticmethod
    def get_current_date() -> str:
        """
        Får dagens dato i YYYY-MM-DD-format.
        
        Returns:
            str: Nuværende dato formateret som YYYY-MM-DD
        """
        return datetime.now().strftime("%Y-%m-%d")
    
    @staticmethod
    def get_current_time() -> str:
        """
        Får aktuel tid i HH:MM:SS-format.
        
        Returns:
            str: Aktuel tid formateret som HH:MM:SS
        """
        return datetime.now().strftime("%H:%M:%S")
    
    @staticmethod
    def format_date(date_obj: datetime) -> str:
        """
        Formatterer et datetime-objekt til YYYY-MM-DD.
        
        Args:
            date_obj (datetime): Datoobjekt der skal formateres
        
        Returns:
            str: Formateret datostreng
        """
        return date_obj.strftime("%Y-%m-%d")
    
    @staticmethod
    def get_date_range(start_date: datetime, days: int = 30) -> List[str]:
        """
        Genererer en liste af datoer startende fra start_date i N dage.
        
        Args:
            start_date (datetime): Startdato
            days (int): Antal dage at generere
        
        Returns:
            list: Liste af datostrenge i YYYY-MM-DD-format
        """
        date_list = []
        for i in range(days):
            date = start_date + timedelta(days=i)
            date_list.append(date.strftime("%Y-%m-%d"))
        return date_list


class MoonConstants:
    """Konstanter relateret til månobservationer."""
    
    # Københavns koordinater (standard observationspunkt)
    LATITUDE = 55.6761
    LONGITUDE = 12.5683
    
    # Månecykluskonstanter
    SYNODIC_MONTH = 29.53  # Dage i en månecyklus
    
    # Fasenavne på dansk
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
    """Hjælpeprogrammer til inputvalidering."""
    
    @staticmethod
    def is_valid_date(date_string: str) -> bool:
        """
        Validerer om streng er en gyldig dato i YYYY-MM-DD-format.
        
        Args:
            date_string (str): Datostreng der skal valideres
        
        Returns:
            bool: Sandt hvis gyldig datoformat, falsk ellers
        """
        try:
            datetime.strptime(date_string, "%Y-%m-%d")
            return True
        except ValueError:
            return False
    
    @staticmethod
    def is_valid_phase(phase_value: float) -> bool:
        """
        Validerer om faseværdi er i gyldig interval (0-1).
        
        Args:
            phase_value (float): Faseværdi der skal valideres
        
        Returns:
            bool: Sandt hvis 0 <= phase_value <= 1
        """
        return 0 <= phase_value <= 1
    
    @staticmethod
    def is_valid_illumination(illumination: float) -> bool:
        """
        Validerer om belysningsværdi er i gyldig interval (0-100).
        
        Args:
            illumination (float): Belysningsprocent der skal valideres
        
        Returns:
            bool: Sandt hvis 0 <= illumination <= 100
        """
        return 0 <= illumination <= 100


class Formatters:
    """Hjælpeprogrammer til outputformatering."""
    
    @staticmethod
    def format_illumination(illumination: float) -> str:
        """
        Formatterer belysningsværdi som procentstreng.
        
        Args:
            illumination (float): Belysningsprocent (0-100)
        
        Returns:
            str: Formateret streng (f.eks. "75%")
        """
        return f"{int(illumination)}%"
    
    @staticmethod
    def format_coordinates(latitude: float, longitude: float) -> str:
        """
        Formatterer koordinater til visning.
        
        Args:
            latitude (float): Breddegrad værdi
            longitude (float): Længdegrad værdi
        
        Returns:
            str: Formateret koordinatstreng
        """
        return f"{latitude:.4f}°N, {longitude:.4f}°E"

class MoonEngine:
    """
    Månefaseberegning og transformationsmotor.
    
    Konverterer råmånefaseværdier fra API til menneskelæsbare navne
    og giver faserelatererede beregninger.
    """
    
    # Synodisk måned (månecyklus) i dage
    SYNODIC_MONTH = 29.53
    
    @staticmethod
    def get_phase_name(phase_value: float) -> str:
        """
        Konverterer API-faseværdi (0-1) til menneskelæsbar fasenavn.
        
        Månecyklusen er opdelt i 8 faser:
        - 0.0-0.125: Nymåne
        - 0.125-0.25: Voksende halvmåne
        - 0.25-0.375: Første kvarter
        - 0.375-0.5: Voksende gibbous
        - 0.5-0.625: Fuldmåne
        - 0.625-0.75: Aftagende gibbous
        - 0.75-0.875: Sidste kvarter
        - 0.875-1.0: Aftagende halvmåne
        
        Args:
            phase_value (float): Faseværdi fra API (0-1)
        
        Returns:
            str: Menneskelæsbar fasenavn på dansk
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
        Transformerer råt API-data til formateret visningsdata.
        
        Args:
            api_data (dict): Råt data fra MoonAPIClient med nøgler:
                - 'illumination': float (0-100)
                - 'phase': float (0-1)
        
        Returns:
            dict: Formateret data med nøgler:
                - 'illumination': float (0-100)
                - 'illumination_percent': str (f.eks., "75%")
                - 'phase': float (0-1)
                - 'phase_name': str (f.eks., "Fuldmåne")
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
        Beregner estimeret dage til næste fuldmåne.
        
        Baseret på synodisk måned på 29,53 dage.
        
        Args:
            phase_value (float): Aktuel faseværdi (0-1)
        
        Returns:
            float: Omtrentlige dage til fuldmåne
        """
        days_into_cycle = phase_value * MoonEngine.SYNODIC_MONTH
        days_to_full = (0.5 * MoonEngine.SYNODIC_MONTH) - days_into_cycle
        
        if days_to_full < 0:
            days_to_full += MoonEngine.SYNODIC_MONTH
        
        return round(days_to_full, 1)


class MoonVisuals:
    """
    Månefasevisualiseringshandler.
    
    Mapper månefaseværdier (0-1) til visuelle repræsentationer (emoji'er).
    Giver konsistent visuelt feedback for forskellige månefaser.
    """
    
    # Månefase-emoji'er for 8 adskilte faser
    MOON_EMOJIS = {
        0: "🌑",  # Nymåne
        1: "🌒",  # Voksende halvmåne
        2: "🌓",  # Første kvarter
        3: "🌔",  # Voksende gibbous
        4: "🌕",  # Fuldmåne
        5: "🌖",  # Aftagende gibbous
        6: "🌗",  # Sidste kvarter
        7: "🌘",  # Aftagende halvmåne,
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
        Henter emoji-repræsentation for en månefaseværdi.
        
        Args:
            phase (float): Faseværdi (0-1)
        
        Returns:
            str: Månens emoji-tegn
        """
        # Sikrer fase er i gyldigt område
        phase = phase % 1.0
        
        for min_phase, max_phase, emoji_key, _ in MoonVisuals.PHASE_RANGES:
            if min_phase <= phase < max_phase:
                return MoonVisuals.MOON_EMOJIS[emoji_key]
        
        # Fallback til aftagende halvmåne hvis uden for normale områder
        return MoonVisuals.MOON_EMOJIS[7]
    
    @staticmethod
    def get_phase_info(phase: float) -> Dict[str, any]:
        """
        Henter fuldstændig faseinformation inkl. emoji og navn.
        
        Args:
            phase (float): Faseværdi (0-1)
        
        Returns:
            dict: Ordbog med nøgler:
                - 'emoji': str (emoji-tegn)
                - 'name': str (fasenavn på dansk)
                - 'index': int (faseindeks 0-7)
        """
        phase = phase % 1.0
        
        for min_phase, max_phase, emoji_key, phase_name in MoonVisuals.PHASE_RANGES:
            if min_phase <= phase < max_phase:
                return {
                    "emoji": MoonVisuals.MOON_EMOJIS[emoji_key],
                    "name": phase_name,
                    "index": emoji_key
                }
        
        # Fallback-værdi
        return {
            "emoji": MoonVisuals.MOON_EMOJIS[7],
            "name": "Aftagende halvmåne",
            "index": 7
        }
    
    @staticmethod
    def get_large_moon_display(phase: float, size: int = 3) -> str:
        """
        Henter forstørret månens emoji til prominent visning.
        
        Gentager emoji-tegnet for at gøre det visuelt større.
        
        Args:
            phase (float): Faseværdi (0-1)
            size (int): Antal gange emoji gentages (1-5)
        
        Returns:
            str: Forstørret månens emoji-visning
        """
        emoji = MoonVisuals.get_moon_emoji(phase)
        size = max(1, min(5, size))  # Begrænser størrelse mellem 1-5
        return emoji * size