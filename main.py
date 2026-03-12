"""
LunarOrbit - Interaktiv Månefase Visualisering

Et professionelt uddannelsesværktøj til at visualisere og udforske månefaser.
Bruger Open Meteo API for astronomiske data og CustomTkinter for moderne brugergrænseflade.

Arkitektur:
- main.py: UI-controller (denne fil) - håndterer al GUI-logik
- moon_api.py: API-klient - kommunikerer med Open Meteo og beregner månefasedata
- boilerplate.py: Hjælpeprogrammer - hjælpefunktioner, konstanter, månemotor og visuals
"""

import customtkinter as ctk
from logik.moon_api import MoonAPIClient
from logik.boilerplate import DateUtils, MoonEngine, MoonVisuals
from PIL import Image, ImageDraw, ImageFont, ImageTk
import io
import math
import random


def create_outline_text_image(text: str, font_size: int = 16, outline_width: int = 2) -> ctk.CTkImage:
    """
    Laver et billede af tekst med sort outline.
    
    Tegner tekst med hvid farve og sort outline omkring.
    
    Args:
        text (str): Teksten der skal tegnes
        font_size (int): Font-størrelse i pixels
        outline_width (int): Outline-bredde i pixels (default 2)
    
    Returns:
        ctk.CTkImage: PhotoImage der kan bruges i CTkLabel
    """
    # Skaber billede med transparent baggrund
    img = Image.new('RGBA', (300, 50), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Prøver at lade system-font, fallback til default hvis ikke tilgængelig
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        # Fallback font hvis arial ikke findes
        font = ImageFont.load_default()
    
    # Tegner sort outline omkring teksten
    # Tegner teksten på 8 positioner omkring originalkoordinatet (360-graders outline)
    for adj_x in range(-outline_width, outline_width + 1):
        for adj_y in range(-outline_width, outline_width + 1):
            if adj_x != 0 or adj_y != 0:
                draw.text((10 + adj_x, 5 + adj_y), text, font=font, fill=(0, 0, 0, 255))
    
    # Tegner hvid tekst på toppen
    draw.text((10, 5), text, font=font, fill=(255, 255, 255, 255))
    
    # Konvertér til PhotoImage
    return ctk.CTkImage(light_image=img, dark_image=img, size=(300, 50))


def generate_cloud_background(width: int = 900, height: int = 700, cloud_cover: float = 50.0) -> Image.Image:
    """
    Genererer en baggrund med skyer baseret på skydække-procent.
    
    0% cloud_cover = klart blåt (næsten mørkt)
    100% cloud_cover = helt hvidt med tætte skyer
    
    Args:
        width (int): Bredde på billede i pixels
        height (int): Højde på billede i pixels
        cloud_cover (float): Skydække procent (0-100)
    
    Returns:
        Image.Image: PIL billede med gradient og skyer
    """
    # Sikrer at cloud_cover er i gyldig range
    cloud_cover = max(0, min(100, cloud_cover))
    
    # Opret billede
    img = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(img, 'RGBA')
    
    # ===== GRADIENT BAGGRUND =====
    # Blå (klart) til mørkegrå (overskyet) baseret på cloud_cover
    # 0% = Deep Navy Blue (#0a1f3f)
    # 100% = Light Gray (#d0d0d0)
    
    # Beregn farver baseret på cloud_cover
    start_r = int(10 + (200 * cloud_cover / 100))
    start_g = int(31 + (190 * cloud_cover / 100))
    start_b = int(63 + (160 * cloud_cover / 100))
    
    end_r = int(50 + (200 * cloud_cover / 100))
    end_g = int(50 + (190 * cloud_cover / 100))
    end_b = int(80 + (160 * cloud_cover / 100))
    
    # Tegn gradient
    for y in range(height):
        # Interporlér mellem start og end baseret på y-position
        r = int(start_r + (end_r - start_r) * y / height)
        g = int(start_g + (end_g - start_g) * y / height)
        b = int(start_b + (end_b - start_b) * y / height)
        
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    
    # ===== TEGN SKYER =====
    # Antal skyer baseret på cloud_cover
    # 0% = 0-1 skyer
    # 50% = 3-5 skyer
    # 100% = 8-12 skyer
    num_clouds = int(cloud_cover / 10)  # 0-10 skyer
    
    # Seed random for reproducibility baseret på cloud_cover
    random.seed(int(cloud_cover * 100))
    
    # Tegn skyer som overlappende hvite ellipser
    for i in range(num_clouds):
        # Tilfældig position
        x = random.randint(-100, width + 100)
        y = random.randint(-50, int(height * 0.6))  # Skyer i øvre del
        
        # Cloud-størrelse varierer
        cloud_width = random.randint(80, 200)
        cloud_height = random.randint(40, 100)
        
        # Cloud-opacitet baseret påcloud_cover
        opacity = int(180 + (75 * cloud_cover / 100))  # 180-255
        
        # Tegn cloud som 3 overlappende cirkler (puffy effect)
        circle_size = cloud_height
        
        # Venstre cirkel
        draw.ellipse(
            [(x, y), (x + circle_size, y + circle_size)],
            fill=(200, 200, 200, opacity)
        )
        
        # Midter cirkel (større)
        draw.ellipse(
            [(x + circle_size // 2, y - circle_size // 4), 
             (x + cloud_width, y + circle_size)],
            fill=(220, 220, 220, opacity)
        )
        
        # Højre cirkel
        draw.ellipse(
            [(x + cloud_width - circle_size // 2, y), 
             (x + cloud_width + circle_size // 2, y + circle_size)],
            fill=(200, 200, 200, opacity)
        )
    
    return img


class LunarOrbitApp(ctk.CTk):
    """
    Hovedapplikationsvindue for LunarOrbit.
    
    Ansvarlig kun for UI-rendering og eventbehandling.
    Al forretningslogik delegeres til specialiserede moduler.
    """
    
    def __init__(self):
        """Initialiserer applikationsvinduet og komponenter."""
        super().__init__()
        
        # Initialiserer forretningslogikmoduler
        self.api_client = MoonAPIClient()
        self.moon_engine = MoonEngine()
        self.moon_visuals = MoonVisuals()
        self.date_utils = DateUtils()
        
        # Konfiguration
        self.title("LunarOrbit - Interaktiv Månefase")
        self.geometry("900x700")
        ctk.set_appearance_mode("dark")
        
        # Aktuelt valgt dato (starter med i dag)
        self.current_date = self.date_utils.get_current_date()
        self.moon_data = None
        self.weather_data = None
        
        # Baggrund billede-referencer (holder den i hukommelsen for at undgå garbage collection)
        self._background_image = None  # PIL Image
        self._background_photo = None  # tkinter.PhotoImage
        
        # Slider-datointervaller (±60 dage fra i dag)
        self.slider_range_days = 60
        self.slider_start_date, self.slider_end_date = self.date_utils.create_slider_date_range(
            self.current_date, 
            self.slider_range_days
        )
        
        # Debouncing for slider - udsætter API-kald til 500ms efter sidste bevægelse
        self._slider_pending_date = None
        self._slider_timer_id = None  # ID for pending timer
        
        # Opsætter UI
        self._setup_ui()
        
        # Starter ur-opdateringsløkke
        self._update_clock()
        
        # Henter initiale månefasedata (som også opdaterer baggrund)
        self._fetch_and_display_moon()
    
    def _setup_ui(self):
        """Opsætter alle UI-komponenter med nyt layout."""
        # ===== BAGGRUND CANVAS (tegner skyer baseret på skydække %) =====
        self.background_canvas = ctk.CTkCanvas(
            self,
            bg='#0a1f3f',  # Initial navy blue
            highlightthickness=0
        )
        self.background_canvas.pack(fill="both", expand=True)
        self.background_canvas.place(x=0, y=0, relwidth=1, relheight=1)
        
        # Tegner initial baggrund (hvis vejrdata ikke tilgængeligt endnu)
        self._update_background(0)
        
        # ===== TOP SECTION: Clock & Status =====
        self.clock_label = ctk.CTkLabel(
            self,
            text="",
            font=("Arial", 14, "bold")
        )
        self.clock_label.place(relx=0.98, rely=0.02, anchor="ne")
        
        # ===== FRAME TITLES (uden for frames - hvid tekst med sort outline) =====
        # Laver outline-billeder for titler
        self._info_title_image = create_outline_text_image("Månedata", font_size=16, outline_width=2)
        self._control_title_image = create_outline_text_image("Kontrol", font_size=16, outline_width=2)
        
        # Info frame title - øverst til venstre, lige over kasserne
        info_title = ctk.CTkLabel(
            self,
            text="",
            image=self._info_title_image
        )
        info_title.place(relx=0.02, rely=0.10, anchor="nw")
        
        # Control frame title - øverst til højre, lige over kasserne
        control_title = ctk.CTkLabel(
            self,
            text="",
            image=self._control_title_image
        )
        control_title.place(relx=0.98, rely=0.10, anchor="ne")
        
        # ===== CENTER SECTION: Moon Display with Date & Slider =====
        # Dato vises OVER månen i bold skrift med sort outline-effekt
        self.date_display_label = ctk.CTkLabel(
            self,
            text=f"{self.current_date}",
            font=("Arial", 18, "bold"),
            text_color="white"
        )
        self.date_display_label.pack(pady=(30, 5), anchor="center")
        
        # Måne emoji - CENTER, stor
        self.moon_display = ctk.CTkLabel(
            self,
            text="🌙",
            font=("Arial", 150)
        )
        self.moon_display.pack(pady=10)
        
        # Datoskyder - direkte UNDER månen
        slider_label = ctk.CTkLabel(
            self,
            text="Vælg dato:",
            font=("Arial", 12, "bold"),
            text_color="white"
        )
        slider_label.pack(pady=(10, 3))
        
        initial_slider_value = self.date_utils.date_to_slider_value(
            self.current_date,
            self.slider_start_date,
            self.slider_end_date
        )
        
        self.date_slider = ctk.CTkSlider(
            self,
            from_=0,
            to=100,
            number_of_steps=121,
            command=self._on_slider_change,
            orientation="horizontal"
        )
        self.date_slider.set(initial_slider_value)
        self.date_slider.pack(padx=20, pady=10, fill="x")
        
        # Datointerval info under slider
        interval_info = ctk.CTkLabel(
            self,
            text=f"({self.slider_start_date} til {self.slider_end_date})",
            font=("Arial", 10),
            text_color="gray"
        )
        interval_info.pack(pady=(0, 20))
        
        # ===== LEFT SIDE: Info Frame (uden titel - titel er øverst) =====
        self.info_frame = ctk.CTkFrame(self)
        self.info_frame.pack(side="left", padx=20, pady=(70, 20), fill="both", expand=True)
        
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
        
        # Vejr-sektion
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
        
        # ===== RIGHT SIDE: Control Frame (uden titel - titel er øverst) =====
        self.control_frame = ctk.CTkFrame(self)
        self.control_frame.pack(side="right", padx=20, pady=(70, 20), fill="both", expand=True)
        
        # Reset knap
        reset_button = ctk.CTkButton(
            self.control_frame,
            text="⟲ Tilbage til i dag",
            command=self._reset_to_today,
            font=("Arial", 11)
        )
        reset_button.pack(anchor="w", padx=5, pady=5, fill="x")
        
        self.status_label = ctk.CTkLabel(
            self.control_frame,
            text="System klar",
            font=("Arial", 11),
            text_color="green"
        )
        self.status_label.pack(anchor="w", pady=5)
    
    def _update_background(self, cloud_cover: float = 0):
        """
        Opdaterer baggrund canvas baseret på skydække procentdel.
        
        Tegner gradient-baggrund med skyer baseret på vejrdata.
        
        Args:
            cloud_cover (float): Skydække procent (0-100)
        """
        # Sikrer valid range
        cloud_cover = max(0, min(100, cloud_cover))
        
        # Genererer baggrund-billede (PIL Image objekt)
        self._background_image = generate_cloud_background(
            width=int(self.winfo_width()) if self.winfo_width() > 1 else 900,
            height=int(self.winfo_height()) if self.winfo_height() > 1 else 700,
            cloud_cover=cloud_cover
        )
        
        # Konverterer PIL.Image til tkinter.PhotoImage (Canvas kræver dette format)
        self._background_photo = ImageTk.PhotoImage(self._background_image)
        
        # Tegn baggrund på canvas
        self.background_canvas.delete("bg")
        self.background_canvas.create_image(
            0, 0,
            image=self._background_photo,
            anchor='nw',
            tags="bg"
        )
        
        # Sikrer canvas er på bagsiden
        self.background_canvas.tag_lower("bg")
    
    def _update_clock(self):
        """
        Opdaterer ur-widget hvert sekund.
        
        Bruger self.after() for at undgå at blokere UI-eventloopet.
        """
        current_time = self.date_utils.get_current_time()
        self.clock_label.configure(text=current_time)
        
        # Planlægger næste opdatering om 1000ms
        self.after(1000, self._update_clock)
    
    def _fetch_and_display_moon(self):
        """
        Henter månefasedata for aktuel dato og opdaterer displayet.
        
        Orkestrerer API-kald og datatransformation.
        """
        self.status_label.configure(
            text="Henter data...",
            text_color="yellow"
        )
        self.update()
        
        # Henter komplet data (måne + valgfrit vejr)
        complete_data = self.api_client.fetch_complete_data(self.current_date)
        
        if complete_data.get("moon"):
            # Transformerer månefasedata ved hjælp af motor
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
        """Viser månefasedata og eventuelt vejrinformation i UI'en."""
        if not self.moon_data:
            return
        
        # Henter faseværdi for emoji
        phase_value = self.moon_data.get("phase", 0)
        
        # Viser månens emoji (stor og klar)
        emoji = self.moon_visuals.get_large_moon_display(phase_value, size=1)
        self.moon_display.configure(text=emoji)
        
        # Opdaterer faseetiket
        phase_name = self.moon_data.get("phase_name", "Ukendt")
        self.phase_label.configure(
            text=f"Fase: {phase_name}"
        )
        
        # Opdaterer belysningsetiket med fed tal
        illumination_percent = self.moon_data.get("illumination_percent", "0%")
        self.illumination_label.configure(
            text=f"Belysning: {illumination_percent}"
        )
        
        # Beregner og viser dage til fuldmåne (hele tal kun)
        days_to_full = int(round(self.moon_engine.calculate_days_to_full_moon(phase_value)))
        self.days_to_full_label.configure(
            text=f"Dage til fuldmåne: {days_to_full}"
        )
        
        # Opdaterer datoen over månen (uden "Dato:" tekst)
        self.date_display_label.configure(
            text=self.current_date
        )
        
        # Opdaterer vejretiketterne hvis tilgængelig
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
                # Opdaterer baggrund baseret på skydække
                self._update_background(float(cloud_cover))
            else:
                self.cloud_label.configure(text="Skydække: (ikke tilgængeligt)")
                self._update_background(0)
        else:
            self.temp_label.configure(text="Temperatur: (ikke tilgængeligt)")
            self.cloud_label.configure(text="Skydække: (ikke tilgængeligt)")
            self._update_background(0)
    
    def _display_error(self):
        """Viser fejltilstand i UI'en."""
        self.phase_label.configure(text="Fase: Fejl ved hentning")
        self.illumination_label.configure(text="Belysning: -")
        self.moon_display.configure(text="❌")
        self._update_background(0)  # Sætter mørk baggrund ved fejl
    
    def _on_slider_change(self, slider_value: float):
        """
        Callback-funktion der køres når datoskyder ændres.
        
        Bruger debouncing for at undgå mange API-kald under slider-træk.
        Udsætter datahentning til 500ms efter sidste slider-bevægelse.
        
        Args:
            slider_value (float): Slider-værdi fra 0-100
        """
        # Konverterer slider-værdi til dato
        selected_date = self.date_utils.slider_value_to_date(
            slider_value,
            self.slider_start_date,
            self.slider_end_date
        )
        
        # Opdaterer aktuelt valgt dato
        self.current_date = selected_date
        
        # Opdaterer datoen over månen øjeblikkeligt (visuelt feedback)
        self.date_display_label.configure(text=self.current_date)
        
        # Gemmer dato for senere hentning
        self._slider_pending_date = selected_date
        
        # Canceller ældre pending timer hvis den findes
        if self._slider_timer_id:
            self.after_cancel(self._slider_timer_id)
        
        # Planlegger data-fetch efter 500ms af inaktivitet
        self._slider_timer_id = self.after(500, self._process_slider_update)
    
    def _process_slider_update(self):
        """
        Processer udsat slider-opdatering når debounce-vinduet er lukket.
        
        Køres kun når slideren ikke er bevæget i 500ms.
        """
        if self._slider_pending_date:
            # Henter nye månefasedata for den valgte dato
            self._fetch_and_display_moon()
        
        # Nulstiller timer-ID
        self._slider_timer_id = None
    
    def _reset_to_today(self):
        """
        Reset-knap callback - sætter slideren og datoen tilbage til i dag.
        
        Bruges når brugeren vil vende tilbage til nuværende dato.
        Eksplicit kalder _on_slider_change() for at trigger data-opdatering.
        """
        # Beregner slider-værdi for i dag
        today = self.date_utils.get_current_date()
        slider_value = self.date_utils.date_to_slider_value(
            today,
            self.slider_start_date,
            self.slider_end_date
        )
        
        # Sætter slider og trigger callback-funktionen
        self.date_slider.set(slider_value)
        
        # Eksplicit kalder callback for at opdatere månedata
        self._on_slider_change(slider_value)


if __name__ == "__main__":
    """Kører applikationen."""
    app = LunarOrbitApp()
    app.mainloop()

