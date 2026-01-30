class CondenserExceptions:
    def __init__(self, pressure_condenser: float | None, temperature_cooling_water_1: float | None, pif: float | None):
        self.pressure_condenser = pressure_condenser
        self.temperature_cooling_water_1 = temperature_cooling_water_1
        self.pif = pif
        
        self.pressure_flow_path_1: float | None = None

    def calculate_pressure(self) -> float | None:
        # Условие 1: pressure_condenser > 0
        if self.pressure_condenser is not None and self.pressure_condenser > 0:
            self.pressure_flow_path_1 = self.pressure_condenser
            return self.pressure_flow_path_1

        # Условие 2: pressure_condenser = None, temperature_cooling_water_1 = None, PIF > 0
        if (self.pressure_condenser is None and
                self.temperature_cooling_water_1 is None and
                self.pif is not None and self.pif > 0):
            self.pressure_flow_path_1 = self.pif
            return self.pressure_flow_path_1

        return None