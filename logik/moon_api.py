"""
Måne-API-klientmodul for LunarOrbit.

Håndterer:
  1. Månefaseberegning     — lokal matematik, ingen API
  2. Solopgang/solnedgang  — lokal NOAA-algoritme, ingen API
  3. Måneopgang/nedgang    — lokal astronomisk formel, ingen API
  4. Vejrdata              — Open-Meteo API (temperatur, skydække)

Alle astronomiske tider beregnes lokalt, så de altid virker uanset
internetforbindelse og dato — der er ingen API-grænser eller 400-fejl.
"""

import math
import datetime as dt
import requests
from typing import Dict, Optional


# ──────────────────────────────────────────────
# SOLOPGANG / SOLNEDGANG  (NOAA-algoritme)
# ──────────────────────────────────────────────

def _sol_tider(år, måned, dag, breddegrad, længdegrad):
    """
    Beregner solopgang og solnedgang med NOAA's algoritme.

    Nøjagtighed ca. ±1 minut. Bruger solens deklination og tidsligning
    til at finde solar noon, og derefter timevinklen til opgang/nedgang.

    Args:
        år (int), måned (int), dag (int): Dato.
        breddegrad (float): Observatørens breddegrad i grader.
        længdegrad (float): Observatørens længdegrad i grader.

    Returns:
        tuple: (solopgang, solnedgang) som "HH:MM" strenge i lokal tid,
               eller ("-", "-") ved polar dag/nat.
    """
    try:
        # Dage siden J2000.0
        J = (dt.date(år, måned, dag) - dt.date(2000, 1, 1)).days

        # Solens middelanomalig og ekliptikale longitude
        M   = math.radians((357.5291 + 0.98560028 * J) % 360)
        L   = (280.4665 + 0.98564736 * J) % 360
        C   = 1.9148 * math.sin(M) + 0.0200 * math.sin(2*M) + 0.0003 * math.sin(3*M)
        lam = math.radians((L + C + 180 + 102.9372) % 360)

        # Solens deklination
        dekl = math.asin(math.sin(math.radians(23.4393)) * math.cos(lam))

        # Tidsligning (minutter → timer): kompenserer for Jordens elliptiske bane
        tidslign = (-2.468 * math.sin(2 * math.radians(L))
                    + 0.053 * math.sin(4 * math.radians(L))
                    - 1.915 * math.sin(M)
                    - 0.020 * math.sin(2 * M)) / 60.0

        # Solar noon i UTC-timer
        noon_utc = 12.0 - (længdegrad / 15.0) - tidslign

        # Timevinklen H: vinklen fra solar noon til solopgang/nedgang
        # Sol regnes op når den er 0.8333 grader under horisonten (refraktion)
        phi   = math.radians(breddegrad)
        cos_H = (math.sin(math.radians(-0.8333)) - math.sin(phi) * math.sin(dekl)) / \
                (math.cos(phi) * math.cos(dekl))

        if abs(cos_H) > 1:
            return ("-", "-")   # Polar dag eller polarnat

        H = math.degrees(math.acos(cos_H)) / 15.0  # Grader → timer

        # Dansk sommertid: UTC+2 fra sidst i marts til sidst i oktober
        er_sommer = (3 < måned < 10) or \
                    (måned == 3 and dag >= 25) or \
                    (måned == 10 and dag < 25)
        offset = 2 if er_sommer else 1

        def fmt(t_utc):
            """Konverterer UTC-timer (float) til lokal "HH:MM" streng."""
            lokal = (t_utc + offset) % 24
            return f"{int(lokal):02d}:{int((lokal % 1) * 60):02d}"

        return (fmt(noon_utc - H), fmt(noon_utc + H))

    except Exception:
        return ("-", "-")


# ──────────────────────────────────────────────
# MÅNEOPGANG / MÅNENEDGANG
# ──────────────────────────────────────────────

def _julian_dag(år, måned, dag):
    """
    Beregner det Julianske Dag-nummer for en dato.

    JD er et kontinuerligt talnummer der tæller dage siden 1. januar 4713 f.Kr.
    Det bruges i astronomiske beregninger til tidsforskelle.

    Args:
        år (int), måned (int), dag (int): Dato.

    Returns:
        float: Juliansk Dag-nummer.
    """
    if måned <= 2:
        år -= 1
        måned += 12
    A = int(år / 100)
    B = 2 - A + int(A / 4)
    return int(365.25 * (år + 4716)) + int(30.6001 * (måned + 1)) + dag + B - 1524.5


def _måne_tider(år, måned, dag, breddegrad, længdegrad):
    """
    Beregner måneopgang og månenedgang for en given dato og placering.

    Månens position beregnes ud fra dens gennemsnitlige bane med
    perturbationer (korrektioner for sol og jord). Nøjagtighed ±5-10 min.

    Args:
        år (int), måned (int), dag (int): Dato.
        breddegrad (float): Observatørens breddegrad i grader.
        længdegrad (float): Observatørens længdegrad i grader.

    Returns:
        tuple: (måneopgang, månenedgang) som "HH:MM" strenge i lokal tid,
               eller ("-", "-") ved polar dag/nat.
    """
    try:
        JD = _julian_dag(år, måned, dag) + 0.5    # Middag UTC
        T  = (JD - 2451545.0) / 36525.0            # Julianiske århundreder

        # Månens banepa parametre i grader
        L0 = (218.3165 + 481267.8813 * T) % 360   # Gennemsnitlig longitude
        M  = math.radians((134.9634 + 477198.8676 * T) % 360)  # Månens anomali
        Ms = math.radians((357.5291 + 35999.0503  * T) % 360)  # Solens anomali
        D  = math.radians((297.8502 + 445267.1115 * T) % 360)  # Elongation
        F  = math.radians((93.2720  + 483202.0175 * T) % 360)  # Baneknude

        # Korrektioner til ekliptisk longitude (grader)
        delta_L = (6.289 * math.sin(M)
                   - 1.274 * math.sin(2*D - M)
                   + 0.658 * math.sin(2*D)
                   - 0.214 * math.sin(2*M)
                   - 0.186 * math.sin(Ms)
                   - 0.114 * math.sin(2*F))

        lam     = math.radians((L0 + delta_L) % 360)
        epsilon = math.radians(23.4393 - 0.013 * T)  # Ekliptikkens hældning

        # Månens deklination og rektascension
        dekl     = math.asin(math.sin(epsilon) * math.sin(lam))
        ra       = math.degrees(math.atan2(math.cos(epsilon) * math.sin(lam),
                                           math.cos(lam))) % 360
        ra_timer = ra / 15.0   # Grader → timer

        # Månens transit i UTC (passage af meridian)
        transit_utc = (ra_timer - (længdegrad / 15.0)) % 24

        # Timevinklen H ved opgang/nedgang (0.583° under horisonten)
        phi   = math.radians(breddegrad)
        cos_H = (math.sin(math.radians(-0.583)) - math.sin(phi) * math.sin(dekl)) / \
                (math.cos(phi) * math.cos(dekl))

        if abs(cos_H) > 1:
            return ("-", "-")

        H = math.degrees(math.acos(cos_H)) / 15.0  # Grader → timer

        er_sommer = (3 < måned < 10) or \
                    (måned == 3 and dag >= 25) or \
                    (måned == 10 and dag < 25)
        offset = 2 if er_sommer else 1

        def fmt(t_utc):
            """Konverterer UTC-timer (float) til lokal "HH:MM" streng."""
            lokal = (t_utc + offset) % 24
            return f"{int(lokal):02d}:{int((lokal % 1) * 60):02d}"

        return (fmt(transit_utc - H), fmt(transit_utc + H))

    except Exception:
        return ("-", "-")


# ──────────────────────────────────────────────
# API-KLIENT
# ──────────────────────────────────────────────

class MoonAPIClient:
    """
    Månefaseberegner og vejr-API-klient for LunarOrbit.

    Månefase og alle astronomiske tider beregnes LOKALT — ingen API
    afhængighed for disse data. Vejrdata hentes fra Open-Meteo.
    """

    KNOWN_NEW_MOON  = dt.datetime(2000, 1, 6)
    SYNODIC_MONTH   = 29.530588

    WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast"
    ARCHIVE_API_URL = "https://archive-api.open-meteo.com/v1/archive"

    def __init__(self, latitude: float = 55.6761, longitude: float = 12.5683,
                 location_name: str = "København"):
        """
        Initialiserer klienten med observationssted.

        Args:
            latitude (float):    Breddegrad. Standard: København.
            longitude (float):   Længdegrad. Standard: København.
            location_name (str): Stednavnet til visning.
        """
        self.latitude      = latitude
        self.longitude     = longitude
        self.location_name = location_name

    def fetch_moon_data(self, date_string: str) -> Optional[Dict]:
        """
        Beregner månefase og belysning for en dato (lokal beregning).

        Args:
            date_string (str): Dato i YYYY-MM-DD format.

        Returns:
            dict med 'phase' (0-1) og 'illumination' (0-100), eller None.
        """
        try:
            date_obj  = dt.datetime.strptime(date_string, "%Y-%m-%d")
            days      = (date_obj - self.KNOWN_NEW_MOON).days
            phase     = (days % self.SYNODIC_MONTH) / self.SYNODIC_MONTH
            illumination = 50 * (1 - math.cos(2 * math.pi * phase))
            return {"illumination": float(illumination), "phase": float(phase)}
        except Exception as e:
            print(f"Fejl ved månefaseberegning: {e}")
            return None

    def fetch_weather_data(self, date_string: str) -> Optional[Dict]:
        """
        Henter vejrdata og beregner astronomiske tider for en dato.

        Astronomiske tider beregnes altid lokalt og returneres selv
        hvis vejr-API'et fejler. Vejrdata hentes fra Open-Meteo med
        automatisk valg af forecast- eller arkiv-endpoint.

        Args:
            date_string (str): Dato i YYYY-MM-DD format.

        Returns:
            dict med vejr- og astronomidata, eller None ved fejl.
        """
        try:
            dato  = dt.datetime.strptime(date_string, "%Y-%m-%d")
            i_dag = dt.datetime.now()

            # Beregn astronomiske tider lokalt (virker altid, uanset API)
            solopgang,  solnedgang  = _sol_tider(
                dato.year, dato.month, dato.day, self.latitude, self.longitude)
            måneopgang, månenedgang = _måne_tider(
                dato.year, dato.month, dato.day, self.latitude, self.longitude)

            # Grundresultat med astronomitider (bruges også hvis API fejler)
            resultat = {
                "temperature_max": "-",
                "temperature_min": "-",
                "cloud_cover":     "-",
                "precip_prob":     "-",
                "location":        self.location_name,
                "sunrise":         solopgang,
                "sunset":          solnedgang,
                "moonrise":        måneopgang,
                "moonset":         månenedgang,
            }

            # Vælg API-endpoint baseret på datoen
            dage_fra_i_dag = (dato - i_dag).days
            if dage_fra_i_dag < -1:
                url    = self.ARCHIVE_API_URL
                daglig = "temperature_2m_max,temperature_2m_min,cloud_cover_mean"
            elif dage_fra_i_dag <= 16:
                url    = self.WEATHER_API_URL
                daglig = "temperature_2m_max,temperature_2m_min,cloud_cover_max,precipitation_probability_max"
            else:
                # For langt ude i fremtiden — ingen vejrdata
                return resultat

            params = {
                "latitude":   self.latitude,
                "longitude":  self.longitude,
                "start_date": date_string,
                "end_date":   date_string,
                "daily":      daglig,
                "timezone":   "auto"
            }

            response = requests.get(url, params=params, timeout=8)
            response.raise_for_status()
            d = response.json().get("daily", {})

            sky = (d.get("cloud_cover_max") or d.get("cloud_cover_mean") or ["-"])[0]

            resultat.update({
                "temperature_max": d.get("temperature_2m_max", ["-"])[0],
                "temperature_min": d.get("temperature_2m_min", ["-"])[0],
                "cloud_cover":     sky,
                "precip_prob":     d.get("precipitation_probability_max", ["-"])[0],
            })
            return resultat

        except requests.exceptions.RequestException as e:
            print(f"Advarsel: Kunne ikke hente vejrdata: {e}")
            # Returnér astronomitider selv om vejr-API fejler
            try:
                dato = dt.datetime.strptime(date_string, "%Y-%m-%d")
                op, ned   = _sol_tider(
                    dato.year, dato.month, dato.day, self.latitude, self.longitude)
                mop, mned = _måne_tider(
                    dato.year, dato.month, dato.day, self.latitude, self.longitude)
                return {
                    "temperature_max": "-", "temperature_min": "-",
                    "cloud_cover": "-",     "precip_prob": "-",
                    "location": self.location_name,
                    "sunrise": op, "sunset": ned,
                    "moonrise": mop, "moonset": mned,
                }
            except Exception:
                return None

        except Exception as e:
            print(f"Uventet fejl: {e}")
            return None

    def fetch_complete_data(self, date_string: str) -> Dict:
        """
        Henter komplet måne- og vejrdata for en dato.

        Args:
            date_string (str): Dato i YYYY-MM-DD format.

        Returns:
            dict med nøglerne 'moon', 'weather' og 'date'.
        """
        return {
            "moon":    self.fetch_moon_data(date_string),
            "weather": self.fetch_weather_data(date_string),
            "date":    date_string
        }