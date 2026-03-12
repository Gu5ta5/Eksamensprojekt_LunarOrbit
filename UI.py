"""
LunarOrbit UI-modul.

Indeholder hele brugergrænsefladen for LunarOrbit-applikationen.
`main.py` fungerer kun som entry point og starter applikationen herfra.
"""

import customtkinter as ctk
from PIL import Image, ImageDraw, ImageFont, ImageTk
import random

from logik.moon_api import MoonAPIClient
from logik.boilerplate import DateUtils, MoonEngine, MoonVisuals


def create_outline_text_image(
    text: str,
    font_size: int = 16,
    outline_width: int = 2
) -> ctk.CTkImage:
    """
    Laver et billede af tekst med sort outline.

    Args:
        text (str): Teksten der skal tegnes.
        font_size (int): Skriftstørrelse i pixels.
        outline_width (int): Bredden på outlinen i pixels.

    Returns:
        ctk.CTkImage: Et billedeobjekt der kan bruges i en `CTkLabel`.
    """
    img = Image.new("RGBA", (300, 50), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except Exception:
        font = ImageFont.load_default()

    for adj_x in range(-outline_width, outline_width + 1):
        for adj_y in range(-outline_width, outline_width + 1):
            if adj_x != 0 or adj_y != 0:
                draw.text(
                    (10 + adj_x, 5 + adj_y),
                    text,
                    font=font,
                    fill=(0, 0, 0, 255)
                )

    draw.text((10, 5), text, font=font, fill=(255, 255, 255, 255))

    return ctk.CTkImage(light_image=img, dark_image=img, size=(300, 50))


def generate_cloud_background(
    width: int = 900,
    height: int = 700,
    cloud_cover: float = 50.0
) -> Image.Image:
    """
    Genererer en baggrund med skyer baseret på skydække-procent.

    Args:
        width (int): Billedets bredde i pixels.
        height (int): Billedets højde i pixels.
        cloud_cover (float): Skydække i procent fra 0 til 100.

    Returns:
        Image.Image: Et genereret PIL-billede med gradient og skyer.
    """
    cloud_cover = max(0, min(100, cloud_cover))

    img = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(img, "RGBA")

    start_r = int(10 + (200 * cloud_cover / 100))
    start_g = int(31 + (190 * cloud_cover / 100))
    start_b = int(63 + (160 * cloud_cover / 100))

    end_r = int(50 + (200 * cloud_cover / 100))
    end_g = int(50 + (190 * cloud_cover / 100))
    end_b = int(80 + (160 * cloud_cover / 100))

    for y in range(height):
        r = int(start_r + (end_r - start_r) * y / height)
        g = int(start_g + (end_g - start_g) * y / height)
        b = int(start_b + (end_b - start_b) * y / height)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    num_clouds = int(cloud_cover / 10)
    random.seed(int(cloud_cover * 100))

    for _ in range(num_clouds):
        x = random.randint(-100, width + 100)
        y = random.randint(-50, int(height * 0.6))
        cloud_width = random.randint(80, 200)
        cloud_height = random.randint(40, 100)
        opacity = int(180 + (75 * cloud_cover / 100))
        circle_size = cloud_height

        draw.ellipse(
            [(x, y), (x + circle_size, y + circle_size)],
            fill=(200, 200, 200, opacity)
        )
        draw.ellipse(
            [(x + circle_size // 2, y - circle_size // 4),
             (x + cloud_width, y + circle_size)],
            fill=(220, 220, 220, opacity)
        )
        draw.ellipse(
            [(x + cloud_width - circle_size // 2, y),
             (x + cloud_width + circle_size // 2, y + circle_size)],
            fill=(200, 200, 200, opacity)
        )

    return img


class LunarOrbitApp(ctk.CTk):
    """
    Hovedapplikationsvindue for LunarOrbit.

    Klassen håndterer al UI-rendering og eventbehandling, mens
    forretningslogik delegeres til logikmodulerne.
    """

    def __init__(self):
        """
        Initialiserer applikationsvinduet og alle nødvendige komponenter.

        Returns:
            None
        """
        super().__init__()

        self.api_client = MoonAPIClient()
        self.moon_engine = MoonEngine()
        self.moon_visuals = MoonVisuals()
        self.date_utils = DateUtils()

        self.title("LunarOrbit - Interaktiv Månefase")
        self.geometry("900x700")
        ctk.set_appearance_mode("dark")

        self.current_date = self.date_utils.get_current_date()
        self.moon_data = None
        self.weather_data = None

        self._background_image = None
        self._background_photo = None

        self.slider_range_days = 60
        self.slider_start_date, self.slider_end_date = (
            self.date_utils.create_slider_date_range(
                self.current_date,
                self.slider_range_days
            )
        )

        self._slider_pending_date = None
        self._slider_timer_id = None

        self._setup_ui()
        self._update_clock()
        self._fetch_and_display_moon()

    def _setup_ui(self):
        """
        Opsætter alle brugergrænsefladens komponenter.

        Returns:
            None
        """
        self.background_canvas = ctk.CTkCanvas(
            self,
            bg="#0a1f3f",
            highlightthickness=0
        )
        self.background_canvas.pack(fill="both", expand=True)
        self.background_canvas.place(x=0, y=0, relwidth=1, relheight=1)

        self._update_background(0)

        self.clock_label = ctk.CTkLabel(
            self,
            text="",
            font=("Arial", 14, "bold")
        )
        self.clock_label.place(relx=0.98, rely=0.02, anchor="ne")

        self._info_title_image = create_outline_text_image(
            "Månedata",
            font_size=16,
            outline_width=2
        )
        self._control_title_image = create_outline_text_image(
            "Kontrol",
            font_size=16,
            outline_width=2
        )

        info_title = ctk.CTkLabel(
            self,
            text="",
            image=self._info_title_image
        )
        info_title.place(relx=0.02, rely=0.10, anchor="nw")

        control_title = ctk.CTkLabel(
            self,
            text="",
            image=self._control_title_image
        )
        control_title.place(relx=0.98, rely=0.10, anchor="ne")

        self.date_display_label = ctk.CTkLabel(
            self,
            text=f"{self.current_date}",
            font=("Arial", 18, "bold"),
            text_color="white"
        )
        self.date_display_label.pack(pady=(30, 5), anchor="center")

        self.moon_display = ctk.CTkLabel(
            self,
            text="🌙",
            font=("Arial", 150)
        )
        self.moon_display.pack(pady=10)

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

        interval_info = ctk.CTkLabel(
            self,
            text=f"({self.slider_start_date} til {self.slider_end_date})",
            font=("Arial", 10),
            text_color="gray"
        )
        interval_info.pack(pady=(0, 20))

        self.info_frame = ctk.CTkFrame(self)
        self.info_frame.pack(
            side="left",
            padx=20,
            pady=(70, 20),
            fill="both",
            expand=True
        )

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

        self.control_frame = ctk.CTkFrame(self)
        self.control_frame.pack(
            side="right",
            padx=20,
            pady=(70, 20),
            fill="both",
            expand=True
        )

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
        Opdaterer baggrunden baseret på skydække.

        Args:
            cloud_cover (float): Skydække i procent fra 0 til 100.

        Returns:
            None
        """
        cloud_cover = max(0, min(100, cloud_cover))

        self._background_image = generate_cloud_background(
            width=int(self.winfo_width()) if self.winfo_width() > 1 else 900,
            height=int(self.winfo_height()) if self.winfo_height() > 1 else 700,
            cloud_cover=cloud_cover
        )

        self._background_photo = ImageTk.PhotoImage(self._background_image)

        self.background_canvas.delete("bg")
        self.background_canvas.create_image(
            0,
            0,
            image=self._background_photo,
            anchor="nw",
            tags="bg"
        )
        self.background_canvas.tag_lower("bg")

    def _update_clock(self):
        """
        Opdaterer ur-widgetten hvert sekund uden at blokere UI'et.

        Returns:
            None
        """
        current_time = self.date_utils.get_current_time()
        self.clock_label.configure(text=current_time)
        self.after(1000, self._update_clock)

    def _fetch_and_display_moon(self):
        """
        Henter månedata og viser dem i brugergrænsefladen.

        Returns:
            None
        """
        self.status_label.configure(
            text="Henter data...",
            text_color="yellow"
        )
        self.update()

        complete_data = self.api_client.fetch_complete_data(self.current_date)

        if complete_data.get("moon"):
            self.moon_data = self.moon_engine.format_moon_data(
                complete_data["moon"]
            )
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
        """
        Viser månefasedata og vejrinformation i UI'et.

        Returns:
            None
        """
        if not self.moon_data:
            return

        phase_value = self.moon_data.get("phase", 0)
        emoji = self.moon_visuals.get_large_moon_display(phase_value, size=1)
        self.moon_display.configure(text=emoji)

        phase_name = self.moon_data.get("phase_name", "Ukendt")
        self.phase_label.configure(text=f"Fase: {phase_name}")

        illumination_percent = self.moon_data.get("illumination_percent", "0%")
        self.illumination_label.configure(
            text=f"Belysning: {illumination_percent}"
        )

        days_to_full = int(
            round(self.moon_engine.calculate_days_to_full_moon(phase_value))
        )
        self.days_to_full_label.configure(
            text=f"Dage til fuldmåne: {days_to_full}"
        )

        self.date_display_label.configure(text=self.current_date)

        if self.weather_data:
            temp_max = self.weather_data.get("temperature_max", "-")
            temp_min = self.weather_data.get("temperature_min", "-")

            if temp_min != "-" and temp_max != "-":
                self.temp_label.configure(
                    text=f"Temperatur: {int(temp_min)}°C til {int(temp_max)}°C"
                )
            else:
                self.temp_label.configure(
                    text="Temperatur: (ikke tilgængeligt)"
                )

            cloud_cover = self.weather_data.get("cloud_cover", "-")
            if cloud_cover != "-":
                self.cloud_label.configure(
                    text=f"Skydække: {int(cloud_cover)}%"
                )
                self._update_background(float(cloud_cover))
            else:
                self.cloud_label.configure(
                    text="Skydække: (ikke tilgængeligt)"
                )
                self._update_background(0)
        else:
            self.temp_label.configure(text="Temperatur: (ikke tilgængeligt)")
            self.cloud_label.configure(text="Skydække: (ikke tilgængeligt)")
            self._update_background(0)

    def _display_error(self):
        """
        Viser fejltilstand i UI'et.

        Returns:
            None
        """
        self.phase_label.configure(text="Fase: Fejl ved hentning")
        self.illumination_label.configure(text="Belysning: -")
        self.moon_display.configure(text="❌")
        self._update_background(0)

    def _on_slider_change(self, slider_value: float):
        """
        Håndterer ændringer fra datoskyderen med debouncing.

        Args:
            slider_value (float): Skyderens værdi mellem 0 og 100.

        Returns:
            None
        """
        selected_date = self.date_utils.slider_value_to_date(
            slider_value,
            self.slider_start_date,
            self.slider_end_date
        )

        self.current_date = selected_date
        self.date_display_label.configure(text=self.current_date)
        self._slider_pending_date = selected_date

        if self._slider_timer_id:
            self.after_cancel(self._slider_timer_id)

        self._slider_timer_id = self.after(500, self._process_slider_update)

    def _process_slider_update(self):
        """
        Behandler den udsatte slider-opdatering efter debounce-perioden.

        Returns:
            None
        """
        if self._slider_pending_date:
            self._fetch_and_display_moon()

        self._slider_timer_id = None

    def _reset_to_today(self):
        """
        Nulstiller dato og slider tilbage til dags dato.

        Returns:
            None
        """
        today = self.date_utils.get_current_date()
        slider_value = self.date_utils.date_to_slider_value(
            today,
            self.slider_start_date,
            self.slider_end_date
        )

        self.date_slider.set(slider_value)
        self._on_slider_change(slider_value)
