import logging
import unittest

from app.domain.valve_physics_engine import ValvePhysicsEngine
from app.domain.models import ValveGeometry, ThermoConditions

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestValveCalculator(unittest.TestCase):
    def setUp(self):
        # 1. Создаем геометрию в новых моделях (перевод в метры)
        self.geo = ValveGeometry(
            count_parts=3,
            diameter_m=40.0 / 1000.0,
            clearance_m=0.215 / 1000.0,
            radius_rounding_m=2.0 / 1000.0,
            len_parts_m=[313.5 / 1000.0, 50.0 / 1000.0, 97.5 / 1000.0]
        )
        
        # 2. Создаем термоввод в новых моделях (перевод в МПа и кДж)
        self.thermo = ThermoConditions(
            count_valves=2,
            p_in_mpa=[12.748, 0.9806, 0.1013],
            t_start_c=555.0,
            h_start_kj_kg=3487.0,
            t_air_c=40.0,
            p_suctions_mpa=[0.0951, 0.0951] # p_ejector
        )
        self.engine = ValvePhysicsEngine(self.geo, self.thermo)

    def test_perform_calculations(self):
        # Выполняем расчет
        raw_res = self.engine.execute()

        expected_Gi = [0.536, 0.074, 0.003]
        
        # Проверяем расходы (Gi)
        for i in range(len(expected_Gi)):
            self.assertAlmostEqual(raw_res.gi_t_h[i], expected_Gi[i], places=2)

        # Проверяем температуры
        self.assertAlmostEqual(raw_res.ti_c[0], 555.0, places=1)
        
        # Проверка деаэратора (dea_g, dea_t, dea_h, dea_p_mpa)
        self.assertGreater(raw_res.dea_g, 0)
        self.assertEqual(raw_res.dea_p_mpa, self.thermo.p_in_mpa[1])

class TestValveCalculatorTwo(unittest.TestCase):
    def setUp(self):
        self.geo = ValveGeometry(
            count_parts=2,
            diameter_m=50.0 / 1000.0,
            clearance_m=0.23 / 1000.0,
            radius_rounding_m=2.0 / 1000.0,
            len_parts_m=[190.0 / 1000.0, 110.0 / 1000.0]
        )
        self.thermo = ThermoConditions(
            count_valves=2,
            p_in_mpa=[12.748, 0.1013],
            t_start_c=555.0,
            h_start_kj_kg=3487.0,
            t_air_c=40.0,
            p_suctions_mpa=[0.0951]
        )
        self.engine = ValvePhysicsEngine(self.geo, self.thermo)

    def test_perform_calculations_two(self):
        raw_res = self.engine.execute()
        self.assertGreater(raw_res.gi_t_h[0], 0.9)
        self.assertEqual(len(raw_res.gi_t_h), 2)

if __name__ == '__main__':
    unittest.main()