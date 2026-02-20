# Python Implementation Instructions: LunarOrbit Logic

## Objective
Assist in developing the backend logic and system control for the LunarOrbit application using Python.

## Technical Stack Prefereces
- **API Interaction:** Use `requests` for fetching astronomical data.
- **Time Management:** Use the `datetime` module for system clock sync and time-travel calculations.
- **GUI/Frontend:** (Specify your chosen library, e.g., `CustomTkinter`, `PyQt`, or `Flask` for web).
- **Architecture:** Use Object-Oriented Programming (OOP). Separate the API Client, the Moon Calculation Engine, and the UI Controller.

## Specific Task Instructions
- **Data Parsing:** Transform raw JSON from the API into usable percentages (0-100% illumination) and phase names.
- **The "Clock" Widget:** Implement a non-blocking thread or a recurring mainloop function that updates the system time in the UI corner without lagging the main visualization.
- **Logic Validation:** Ensure that if a user "scrubs" to a future date, the Python logic correctly recalculates the phase based on synodic month constants (approx. 29.53 days) or new API calls.

## Documentation
Every function must have a docstring explaining its parameters and return values.