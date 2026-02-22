"""
LunarOrbit - Interactive Moon Phase Visualization

A professional educational tool for visualizing and exploring moon phases.
Uses Open Meteo API for real astronomical data and CustomTkinter for modern UI.

Architecture:
- main.py: UI Controller (this file) - handles all GUI logic
- moon_api.py: API Client - communicates with Open Meteo and calculates moon data
- boilerplate.py: Utilities - helper functions, constants, moon engine, and visuals
"""

import customtkinter as ctk
from moon_api import MoonAPIClient
from boilerplate import DateUtils, MoonEngine, MoonVisuals


class LunarOrbitApp(ctk.CTk):
    """
    Main application window for LunarOrbit.
    
    Responsible only for UI rendering and event handling.
    All business logic is delegated to specialized modules.
    """
    
    def __init__(self):
        """Initialize the application window and components."""
        super().__init__()
        
        # Initialize business logic modules
        self.api_client = MoonAPIClient()
        self.moon_engine = MoonEngine()
        self.moon_visuals = MoonVisuals()
        self.date_utils = DateUtils()
        
        # Configuration
        self.title("LunarOrbit - Interaktiv Månefase")
        self.geometry("900x700")
        ctk.set_appearance_mode("dark")
        
        # Current selected date (starts with today)
        self.current_date = self.date_utils.get_current_date()
        self.moon_data = None
        self.weather_data = None
        
        # Setup UI
        self._setup_ui()
        
        # Start clock update loop
        self._update_clock()
        
        # Fetch initial moon data
        self._fetch_and_display_moon()
    
    def _setup_ui(self):
        """Set up all UI components."""
        # Clock widget - top right corner
        self.clock_label = ctk.CTkLabel(
            self,
            text="",
            font=("Arial", 14, "bold")
        )
        self.clock_label.place(relx=0.98, rely=0.02, anchor="ne")
        
        # Main moon visualization area - CENTER with LARGE emoji
        self.moon_display = ctk.CTkLabel(
            self,
            text="🌙",
            font=("Arial", 150)
        )
        self.moon_display.pack(pady=20)
        
        # Moon info display - LEFT SIDE
        self.info_frame = ctk.CTkFrame(self)
        self.info_frame.pack(side="left", padx=20, pady=20, fill="both", expand=True)
        
        # Title
        title_label = ctk.CTkLabel(
            self.info_frame,
            text="Månedata",
            font=("Arial", 16, "bold")
        )
        title_label.pack(anchor="w", pady=10)
        
        self.phase_label = ctk.CTkLabel(
            self.info_frame,
            text="Fase: -",
            font=("Arial", 13)
        )
        self.phase_label.pack(anchor="w", pady=5)
        
        self.illumination_label = ctk.CTkLabel(
            self.info_frame,
            text="Belysning: -",
            font=("Arial", 13)
        )
        self.illumination_label.pack(anchor="w", pady=5)
        
        self.days_to_full_label = ctk.CTkLabel(
            self.info_frame,
            text="Dage til fuldmåne: -",
            font=("Arial", 13)
        )
        self.days_to_full_label.pack(anchor="w", pady=5)
        
        # Weather info section
        weather_title = ctk.CTkLabel(
            self.info_frame,
            text="Vejr (hvis tilgængeligt)",
            font=("Arial", 13, "bold")
        )
        weather_title.pack(anchor="w", pady=(15, 5))
        
        self.temp_label = ctk.CTkLabel(
            self.info_frame,
            text="Temperatur: -",
            font=("Arial", 12)
        )
        self.temp_label.pack(anchor="w", pady=3)
        
        self.cloud_label = ctk.CTkLabel(
            self.info_frame,
            text="Skydække: -",
            font=("Arial", 12)
        )
        self.cloud_label.pack(anchor="w", pady=3)
        
        # Date picker and status - RIGHT SIDE
        self.control_frame = ctk.CTkFrame(self)
        self.control_frame.pack(side="right", padx=20, pady=20, fill="both", expand=True)
        
        control_title = ctk.CTkLabel(
            self.control_frame,
            text="Kontrol",
            font=("Arial", 16, "bold")
        )
        control_title.pack(anchor="w", pady=10)
        
        self.date_label = ctk.CTkLabel(
            self.control_frame,
            text=f"Dato: {self.current_date}",
            font=("Arial", 12)
        )
        self.date_label.pack(anchor="w", pady=5)
        
        self.status_label = ctk.CTkLabel(
            self.control_frame,
            text="System klar",
            font=("Arial", 11),
            text_color="green"
        )
        self.status_label.pack(anchor="w", pady=5)
    
    def _update_clock(self):
        """
        Update the clock widget every second.
        
        Uses self.after() to avoid blocking the UI event loop.
        """
        current_time = self.date_utils.get_current_time()
        self.clock_label.configure(text=current_time)
        
        # Schedule next update in 1000ms
        self.after(1000, self._update_clock)
    
    def _fetch_and_display_moon(self):
        """
        Fetch moon data for current date and update display.
        
        Orchestrates the API calls and data transformation.
        """
        self.status_label.configure(
            text="Henter data...",
            text_color="yellow"
        )
        self.update()
        
        # Get complete data (moon + optional weather)
        complete_data = self.api_client.fetch_complete_data(self.current_date)
        
        if complete_data.get("moon"):
            # Transform moon data using engine
            self.moon_data = self.moon_engine.format_moon_data(complete_data["moon"])
            self.weather_data = complete_data.get("weather")
            self._display_moon_data()
            self.status_label.configure(
                text="Data indlæst",
                text_color="green"
            )
        else:
            self.status_label.configure(
                text="Fejl ved datahentning",
                text_color="red"
            )
            self._display_error()
    
    def _display_moon_data(self):
        """Display the moon data and optional weather in the UI."""
        if not self.moon_data:
            return
        
        # Get phase value for emoji
        phase_value = self.moon_data.get("phase", 0)
        
        # Display moon emoji (large and clear)
        emoji = self.moon_visuals.get_large_moon_display(phase_value, size=1)
        self.moon_display.configure(text=emoji)
        
        # Update phase label
        phase_name = self.moon_data.get("phase_name", "Ukendt")
        self.phase_label.configure(
            text=f"Fase: {phase_name}"
        )
        
        # Update illumination label with bold number
        illumination_percent = self.moon_data.get("illumination_percent", "0%")
        self.illumination_label.configure(
            text=f"Belysning: {illumination_percent}"
        )
        
        # Calculate and display days to full moon (whole number only)
        days_to_full = int(round(self.moon_engine.calculate_days_to_full_moon(phase_value)))
        self.days_to_full_label.configure(
            text=f"Dage til fuldmåne: {days_to_full}"
        )
        
        # Update date label
        self.date_label.configure(
            text=f"Dato: {self.current_date}"
        )
        
        # Update weather labels if available
        if self.weather_data:
            temp_max = self.weather_data.get("temperature_max", "-")
            temp_min = self.weather_data.get("temperature_min", "-")
            if temp_min != "-" and temp_max != "-":
                self.temp_label.configure(
                    text=f"Temperatur: {int(temp_min)}°C til {int(temp_max)}°C"
                )
            else:
                self.temp_label.configure(text="Temperatur: (ikke tilgængeligt)")
            
            cloud_cover = self.weather_data.get("cloud_cover", "-")
            if cloud_cover != "-":
                self.cloud_label.configure(
                    text=f"Skydække: {int(cloud_cover)}%"
                )
            else:
                self.cloud_label.configure(text="Skydække: (ikke tilgængeligt)")
        else:
            self.temp_label.configure(text="Temperatur: (ikke tilgængeligt)")
            self.cloud_label.configure(text="Skydække: (ikke tilgængeligt)")
    
    def _display_error(self):
        """Display error state in UI."""
        self.phase_label.configure(text="Fase: Fejl ved hentning")
        self.illumination_label.configure(text="Belysning: -")
        self.moon_display.configure(text="❌")


if __name__ == "__main__":
    """Run the application."""
    app = LunarOrbitApp()
    app.mainloop()

