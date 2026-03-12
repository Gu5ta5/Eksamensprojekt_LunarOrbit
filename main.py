"""
LunarOrbit - Entry point for applikationen.

Denne fil holdes bevidst minimal og bruges kun til at starte
brugergrænsefladen fra `UI.py`.
"""

from UI import LunarOrbitApp


if __name__ == "__main__":
    app = LunarOrbitApp()
    app.mainloop()
