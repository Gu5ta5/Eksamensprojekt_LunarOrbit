"""
LunarOrbit UI-modul.
Galakse-tema med lilla/pink gradient baggrund og stjerner.

Alle kendte fejl er rettet:
- Ingen sorte bokse bag labels (bg_color matcher CTk's mørke tema).
- Baggrunden skalerer med vinduet via <Configure>-eventet.
- Månen vises som én enkelt emoji.
- Slideren navigerer ±60 dage fra i dag.
- Vejrdata hentes i baggrunden (threading) så UI ikke fryser.
"""

import customtkinter as ctk
import tkinter as tk
from PIL import Image, ImageDraw, ImageTk
import random
import threading

from logik.moon_api import MoonAPIClient
from logik.boilerplate import DateUtils, MoonEngine, MoonVisuals


# CTk dark mode bruger denne baggrundsfarve på vinduet.
# Vi sætter bg_color på alle labels til denne værdi så der
# ikke opstår sorte bokse bag teksten.
CTK_DARK_BG = "#212121"


# ──────────────────────────────────────────────
# BAGGRUND
# ──────────────────────────────────────────────

def generate_space_background(width, height):
    """
    Genererer et galakse-baggrundsbillede med lilla/pink gradient og hvide stjerner.

    Gradient fra øverst til nederst:
      - Øverst:  mørk navy-lilla  (15, 5, 40)
      - Midt:    dyb lilla        (60, 10, 90)
      - Nederst: varm pink        (120, 20, 80)

    Ovenpå tegnes 200 hvide prikker som simulerer stjerner.

    Args:
        width (int):  Billedets bredde i pixels.
        height (int): Billedets højde i pixels.

    Returns:
        PIL.Image: Færdigt baggrundsbillede.
    """
    img = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(img)

    top    = (15,  5,  40)
    mid    = (60, 10,  90)
    bottom = (120, 20, 80)

    for y in range(height):
        ratio = y / height
        if ratio < 0.5:
            t = ratio / 0.5
            r = int(top[0] * (1 - t) + mid[0] * t)
            g = int(top[1] * (1 - t) + mid[1] * t)
            b = int(top[2] * (1 - t) + mid[2] * t)
        else:
            t = (ratio - 0.5) / 0.5
            r = int(mid[0] * (1 - t) + bottom[0] * t)
            g = int(mid[1] * (1 - t) + bottom[1] * t)
            b = int(mid[2] * (1 - t) + bottom[2] * t)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # Stjerner – fast seed så de er ens hver gang
    random.seed(42)
    for _ in range(200):
        x = random.randint(0, width)
        y = random.randint(0, height)
        size = random.choice([1, 1, 1, 2])
        brightness = random.randint(160, 255)
        draw.ellipse([x, y, x + size, y + size],
                     fill=(brightness, brightness, brightness))

    return img


# ──────────────────────────────────────────────
# HOVED-APP
# ──────────────────────────────────────────────

class LunarOrbitApp(ctk.CTk):
    """
    Hovedklassen for LunarOrbit-applikationen.

    Baggrunds-strategi:
        Et tk.Canvas fylder hele vinduet og tegner PIL-billedet.
        Baggrunden gentegnes automatisk når vinduet ændrer størrelse
        via <Configure>-eventet. Alle widgets placeres i et
        tk.Frame oven på canvas med gennemsigtig baggrund.
    """

    def __init__(self):
        """
        Initialiserer applikationen og sætter alle komponenter op.
        """
        super().__init__()

        self.title("LunarOrbit")
        self.geometry("900x700")
        ctk.set_appearance_mode("dark")

        # ── Logik-objekter ──
        self.api_client   = MoonAPIClient()
        self.moon_engine  = MoonEngine()
        self.moon_visuals = MoonVisuals()
        self.date_utils   = DateUtils()

        # ── Dato og slider-interval (±60 dage) ──
        self.today        = self.date_utils.get_current_date()
        self.current_date = self.today
        self.slider_start, self.slider_end = self.date_utils.create_slider_date_range(
            self.today, range_days=60
        )

        # ── Cache til vejrdata ──
        self._weather_cache = {}

        # ── Canvas som baggrund ──
        # tk.Canvas (ikke ctk) understøtter PIL-billeder via create_image().
        self.canvas = tk.Canvas(self, highlightthickness=0, bd=0, bg=CTK_DARK_BG)
        self.canvas.place(x=0, y=0, relwidth=1, relheight=1)

        # Generer baggrundsbilledet én gang i høj opløsning og gem det.
        # Ved resize skalerer vi dette billede i stedet for at generere nyt.
        self._bg_original = generate_space_background(1920, 1080)

        # Tegn baggrunden første gang i standardstørrelsen
        self._tegn_baggrund_i_storrelse(900, 700)

        # Lyt på resize-events – men KUN fra selve vinduet (se _on_resize)
        self.bind("<Configure>", self._on_resize)

        # ── UI ──
        self._setup_ui()
        self._update_clock()
        self._fetch_and_display_moon()

    # ──────────────────────────────────────────────
    # BAGGRUND
    # ──────────────────────────────────────────────

    def _tegn_baggrund_i_storrelse(self, w, h):
        """
        Skalerer det originale baggrundsbillede til (w, h) og tegner det på canvas.

        Args:
            w (int): Ønsket bredde i pixels.
            h (int): Ønsket højde i pixels.
        """
        skaleret = self._bg_original.resize((w, h), Image.LANCZOS)
        self.bg_photo = ImageTk.PhotoImage(skaleret)
        self.canvas.delete("baggrund")
        self.canvas.create_image(0, 0, image=self.bg_photo, anchor="nw", tags="baggrund")
        self.canvas.tag_lower("baggrund")

    def _on_resize(self, event):
        """
        Kaldes automatisk når vinduet ændrer størrelse.

        VIGTIGT: <Configure> fyres af på ALLE widgets, ikke kun vinduet.
        Vi tjekker derfor om event.widget er selve vinduet (self) inden
        vi gør noget – ellers ville slideren og andre widgets også
        trigge denne funktion og rode med baggrunden.

        Baggrunden genereres én gang i fuld opløsning og gemmes i
        self._bg_original. Ved resize skalerer vi bare det gemte billede
        i stedet for at generere et nyt – det er meget hurtigere.

        Args:
            event: Tkinter Configure-event med ny width og height.
        """
        # Ignorer events fra child-widgets (slider, labels, frames osv.)
        if event.widget is not self:
            return

        w, h = event.width, event.height
        if w < 10 or h < 10:
            return

        # Skaler det originale baggrundsbillede til den nye størrelse
        skaleret = self._bg_original.resize((w, h), Image.LANCZOS)
        self.bg_photo = ImageTk.PhotoImage(skaleret)

        self.canvas.delete("baggrund")
        self.canvas.create_image(0, 0, image=self.bg_photo, anchor="nw", tags="baggrund")
        self.canvas.tag_lower("baggrund")

    # ──────────────────────────────────────────────
    # UI OPBYGNING
    # ──────────────────────────────────────────────

    def _setup_ui(self):
        """
        Bygger alle UI-elementer.

        Layout:
          - Ur øverst til højre
          - Status + reset-knap øverst til venstre (lille)
          - Dato centreret øverst
          - Stor måne-emoji i midten
          - Slider med − og + ikoner
          - To paneler i bunden: Månefase+Vejr (venstre) og Astronomi (højre)
            Begge fylder hele bunden fra venstre til højre kant.

        tk.Label bruges til ur, dato og måne fordi de kan have
        gennemsigtig baggrund der matcher gradienten. CTkLabel kan ikke.
        """

        # ── Ur øverst til højre ──
        self.clock_label = tk.Label(
            self, text="", font=("Arial", 14),
            fg="white", bg="#11052a"
        )
        self.clock_label.place(relx=0.98, rely=0.02, anchor="ne")

        # ── Status øverst til venstre ──
        self.status_label = ctk.CTkLabel(
            self, text="Klar", font=("Arial", 11),
            text_color="lightgreen",
            fg_color="transparent", bg_color="#11052a"
        )
        self.status_label.place(x=10, y=8)

        # ── Reset-knap lige under status ──
        self.reset_button = ctk.CTkButton(
            self, text="⟲ Tilbage til i dag",
            font=("Arial", 11), height=28,
            fg_color="#6010a0", hover_color="#8020c0",
            bg_color="#11052a",
            command=self._reset_to_today
        )
        self.reset_button.place(x=10, y=30)

        # ── Dato centreret ──
        self.date_label = tk.Label(
            self, text=self.current_date,
            font=("Arial", 20, "bold"),
            fg="white", bg="#11052a"
        )
        self.date_label.place(relx=0.5, rely=0.07, anchor="center")

        # ── Stor måne-emoji ──
        self.moon_display = tk.Label(
            self, text="🌙",
            font=("Arial", 280),
            fg="white", bg="#2a0849"
        )
        self.moon_display.place(relx=0.5, rely=0.35, anchor="center")

        # ── Slider med − og + ikoner ──
        self.minus_label = tk.Label(
            self, text="−", font=("Arial", 22, "bold"),
            fg="#c060e0", bg="#3c0a5a"
        )
        self.minus_label.place(relx=0.05, rely=0.62, anchor="center")

        self.date_slider = ctk.CTkSlider(
            self, from_=0, to=100, height=20,
            button_color="#c060e0", button_hover_color="#d080f0",
            progress_color="#8020b0", bg_color="#3c0a5a",
            command=self._on_slider_change
        )
        self.date_slider.set(50)
        self.date_slider.place(relx=0.5, rely=0.62, anchor="center", relwidth=0.76)

        self.plus_label = tk.Label(
            self, text="+", font=("Arial", 22, "bold"),
            fg="#c060e0", bg="#3c0a5a"
        )
        self.plus_label.place(relx=0.95, rely=0.62, anchor="center")

        # ── Månefase + Vejr panel (venstre halvdel af bunden) ──
        # Fylder fra venstre kant til midten med en lille margen
        self.info_frame = ctk.CTkFrame(
            self,
            fg_color="#2a0a3a", bg_color="#5e0f54",
            corner_radius=15, border_width=1, border_color="#c060e0",
            width=400, height=200
        )
        self.info_frame.place(relx=0.01, rely=0.67, relwidth=0.47, relheight=0.30)
        self.info_frame.pack_propagate(False)

        # Titel
        ctk.CTkLabel(
            self.info_frame, text="🌙 Månefase & Vejr",
            font=("Arial", 14, "bold"),
            fg_color="transparent", text_color="#c060e0"
        ).pack(anchor="w", padx=14, pady=(10, 4))

        self.phase_label = ctk.CTkLabel(
            self.info_frame, text="Fase: -",
            font=("Arial", 14), fg_color="transparent", text_color="white"
        )
        self.phase_label.pack(anchor="w", padx=14, pady=3)

        self.illumination_label = ctk.CTkLabel(
            self.info_frame, text="Belysning: -",
            font=("Arial", 14), fg_color="transparent", text_color="white"
        )
        self.illumination_label.pack(anchor="w", padx=14, pady=3)

        self.days_label = ctk.CTkLabel(
            self.info_frame, text="Dage til fuldmåne: -",
            font=("Arial", 14), fg_color="transparent", text_color="white"
        )
        self.days_label.pack(anchor="w", padx=14, pady=3)

        self.weather_label = ctk.CTkLabel(
            self.info_frame, text="Vejr: henter...",
            font=("Arial", 14), fg_color="transparent", text_color="white",
            wraplength=300
        )
        self.weather_label.pack(anchor="w", padx=14, pady=3)

        # ── Astronomi panel (højre halvdel af bunden) ──
        # Fylder fra midten til højre kant med en lille margen
        self.astro_frame = ctk.CTkFrame(
            self,
            fg_color="#2a0a3a", bg_color="#5e0f54",
            corner_radius=15, border_width=1, border_color="#c060e0",
            width=400, height=200
        )
        self.astro_frame.place(relx=0.52, rely=0.67, relwidth=0.47, relheight=0.30)
        self.astro_frame.pack_propagate(False)

        # Titel
        ctk.CTkLabel(
            self.astro_frame, text="🌍 Astronomi",
            font=("Arial", 14, "bold"),
            fg_color="transparent", text_color="#c060e0"
        ).pack(anchor="w", padx=14, pady=(10, 4))

        self.sunrise_label = ctk.CTkLabel(
            self.astro_frame, text="🌅 Solopgang:    -",
            font=("Arial", 14), fg_color="transparent", text_color="white"
        )
        self.sunrise_label.pack(anchor="w", padx=14, pady=3)

        self.sunset_label = ctk.CTkLabel(
            self.astro_frame, text="🌇 Solnedgang:   -",
            font=("Arial", 14), fg_color="transparent", text_color="white"
        )
        self.sunset_label.pack(anchor="w", padx=14, pady=3)

        self.moonrise_label = ctk.CTkLabel(
            self.astro_frame, text="🌕 Måneopgang:   -",
            font=("Arial", 14), fg_color="transparent", text_color="white"
        )
        self.moonrise_label.pack(anchor="w", padx=14, pady=3)

        self.moonset_label = ctk.CTkLabel(
            self.astro_frame, text="🌑 Månenedgang:  -",
            font=("Arial", 14), fg_color="transparent", text_color="white"
        )
        self.moonset_label.pack(anchor="w", padx=14, pady=3)

        self.uv_label = ctk.CTkLabel(
            self.astro_frame, text="☀️ UV-indeks:    -",
            font=("Arial", 14), fg_color="transparent", text_color="white"
        )
        self.uv_label.pack(anchor="w", padx=14, pady=3)

        self.precip_label = ctk.CTkLabel(
            self.astro_frame, text="🌧 Nedbør:       -%",
            font=("Arial", 14), fg_color="transparent", text_color="white"
        )
        self.precip_label.pack(anchor="w", padx=14, pady=3)

    # ──────────────────────────────────────────────
    # LOGIK
    # ──────────────────────────────────────────────

    def _update_clock(self):
        """
        Opdaterer ur-labelen med aktuel tid hvert sekund.

        Bruger after() til at kalde sig selv igen efter 1000ms.
        """
        self.clock_label.config(text=self.date_utils.get_current_time())
        self.after(1000, self._update_clock)

    def _fetch_and_display_moon(self):
        """
        Henter og viser månefasedata for den valgte dato.

        Månefasen beregnes lokalt (ingen API, øjeblikkeligt).
        Vejrdata hentes i en baggrundstråd så UI ikke fryser.
        """
        date = self.current_date

        # Månefase: lokal beregning, vises med det samme
        moon_raw = self.api_client.fetch_moon_data(date)
        if moon_raw:
            moon  = self.moon_engine.format_moon_data(moon_raw)
            phase = moon.get("phase", 0)

            self.moon_display.config(
                text=self.moon_visuals.get_large_moon_display(phase, size=1)
            )
            self.phase_label.configure(text=f"Fase: {moon.get('phase_name')}")
            self.illumination_label.configure(
                text=f"Belysning: {moon.get('illumination_percent')}"
            )
            days = int(round(self.moon_engine.calculate_days_to_full_moon(phase)))
            self.days_label.configure(text=f"Dage til fuldmåne: {days}")

        # Vejrdata: hentes i baggrundstråd
        self.status_label.configure(text="Henter vejr...", text_color="orange")

        if date in self._weather_cache:
            self._update_weather_ui(self._weather_cache[date])
        else:
            thread = threading.Thread(
                target=self._fetch_weather_in_background,
                args=(date,),
                daemon=True
            )
            thread.start()

    def _fetch_weather_in_background(self, date):
        """
        Henter vejrdata fra API i en baggrundstråd.

        Bruger after(0, ...) til at opdatere UI i hoved-tråden
        (krav i Tkinter – UI må kun opdateres fra hoved-tråden).

        Args:
            date (str): Dato i YYYY-MM-DD format.
        """
        weather = self.api_client.fetch_weather_data(date)
        self._weather_cache[date] = weather
        self.after(0, lambda: self._update_weather_ui(weather))

    def _update_weather_ui(self, weather):
        """
        Opdaterer vejr-labelen og det astronomiske panel med hentet data.

        Args:
            weather (dict eller None): Vejrdata fra API, eller None ved fejl.
        """
        if weather:
            tekst = (
                f"🌡 {weather.get('temperature_min')}° – "
                f"{weather.get('temperature_max')}°C\n"
                f"☁ Skydækket: {weather.get('cloud_cover')}%"
            )
            self.weather_label.configure(text=f"Vejr: {tekst}")
            self.status_label.configure(text="Klar", text_color="lightgreen")

            # Opdater astronomi-panelet
            self.sunrise_label.configure(
                text=f"🌅 Solopgang:   {weather.get('sunrise', '-')}")
            self.sunset_label.configure(
                text=f"🌇 Solnedgang:  {weather.get('sunset', '-')}")
            self.moonrise_label.configure(
                text=f"🌕 Måneopgang:  {weather.get('moonrise', '-')}")
            self.moonset_label.configure(
                text=f"🌑 Månenedgang: {weather.get('moonset', '-')}")

            uv = weather.get('uv_index', '-')
            self.uv_label.configure(text=f"☀️ UV-indeks:   {uv}")

            precip = weather.get('precip_prob', '-')
            self.precip_label.configure(
                text=f"🌧 Nedbør:      {precip}%")
        else:
            self.weather_label.configure(text="Vejr: ikke tilgængeligt")
            self.status_label.configure(text="Klar", text_color="lightgreen")
            self.sunrise_label.configure(text="🌅 Solopgang:   -")
            self.sunset_label.configure(text="🌇 Solnedgang:  -")
            self.moonrise_label.configure(text="🌕 Måneopgang:  -")
            self.moonset_label.configure(text="🌑 Månenedgang: -")
            self.uv_label.configure(text="☀️ UV-indeks:   -")
            self.precip_label.configure(text="🌧 Nedbør:      -%")

    def _on_slider_change(self, value):
        """
        Kaldes når brugeren trækker i slideren.

        Konverterer slider-position (0–100) til en dato og opdaterer visningen.

        Args:
            value (float): Sliderens position (0.0 til 100.0).
        """
        self.current_date = self.date_utils.slider_value_to_date(
            value,
            self.slider_start,
            self.slider_end
        )
        self.date_label.config(text=self.current_date)
        self._fetch_and_display_moon()

    def _reset_to_today(self):
        """
        Nulstiller datoen til i dag og sætter slideren til midten (50 = i dag).
        """
        self.current_date = self.today
        self.date_label.config(text=self.current_date)
        self.date_slider.set(50)
        self._fetch_and_display_moon()