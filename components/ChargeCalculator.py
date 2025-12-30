import numpy as np

class ChargeCalculator:
    def __init__(self):
        self.pixels_mm = 414.20  # Calibration factor (pixels to mm)
        self.pressure_torr = 760  # Atmospheric pressure in Torr
        self.distance_mm = 4.902  # Plate distance in mm
        self.distance_m = self.distance_mm * 1e-3  # Convert mm to meters
        self.voltage = 500  # Applied voltage in volts
        self.E = self.voltage / self.distance_m  # Electric field strength
        self.roomtempc = 20  # Room temperature in Celsius
        self.density_oil = 0.861e3  # Density of oil in kg/m^3
        self.a_gravity = 9.81  # Acceleration due to gravity in m/s^2

    def corrected_viscosity(self, vd):
        if vd <= 0:
            raise ValueError(f"Invalid downward velocity (vd): {vd}. Must be greater than 0.")
        # Initial viscosity without correction
        eta_0 = 1.8228e-5 + ((4.790e-8) * (self.roomtempc - 21))
        # Radius without correction
        radius_uncorrected = np.sqrt((9 * eta_0 * vd) / (2 * self.density_oil * self.a_gravity))
        # Corrected viscosity
        correction_factor = 1 + (5.908e-5 / (radius_uncorrected * self.pressure_torr))
        return eta_0 / correction_factor

    def find_radius(self, vd, viscosity_air):
        top = (9 * viscosity_air * vd)
        bot = (2 * self.density_oil * self.a_gravity)
        radius = np.sqrt(top / bot)
        return radius

    def find_mass(self, radius):
        top = self.density_oil * 4 * np.pi * np.power(radius, 3)
        bot = 3
        mass = top / bot
        return mass

    def find_charge_and_integer(self, vu, vd):
        if vd <= 0 or vu <= 0:
            raise ValueError(f"\nInvalid velocities: \n\tvu={vu}, vd={vd}. \n\tBoth must be greater than 0.")
        viscosity_air = self.corrected_viscosity(vd)
        radius = self.find_radius(vd, viscosity_air)
        mass = self.find_mass(radius)
        charge = ((mass * self.a_gravity) + (6 * np.pi * viscosity_air * radius * vu)) / self.E
        integer = charge / 1.602176634e-19  # Elementary charge
        return charge, integer
