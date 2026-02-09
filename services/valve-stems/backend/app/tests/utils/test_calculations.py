from typing import Optional, List
import logging
from app.services.calculator import ValveCalculator
from app.schemas import CalculationParams, ValveInfo, CalculationResult
import unittest
from math import sqrt, pi

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TestValveCalculator(unittest.TestCase):
    def setUp(self):
        params = CalculationParams(
            temperature_start=555,
            t_air=40,
            count_valves=2,
            p_ejector=[0.97, 0.97],
            p_values=[130, 10, 1.03]
        )
        valve_info = ValveInfo(
            id=1,
            name="Test Valve 1",
            round_radius=2,
            clearance=0.215,
            diameter=40,
            len_part1=313.5,
            len_part2=50,
            len_part3=97.5
        )
        self.calculator = ValveCalculator(params, valve_info)

    def test_perform_calculations(self):
        result = self.calculator.perform_calculations()

        expected_Gi = [0.5365648691, 0.07402597315, 0.003495929025]
        expected_Pi_in = [130, 10, 1.03]
        expected_Ti = [555, 503.6, 40]
        expected_Hi = [3487.026558, 3487.026558, 40.24]

        for i in range(len(expected_Gi)):
            self.assertAlmostEqual(result.Gi[i], expected_Gi[i], places=3)
        for i in range(len(expected_Pi_in)):
            self.assertAlmostEqual(result.Pi_in[i], expected_Pi_in[i], places=2)
        for i in range(len(expected_Ti)):
            self.assertAlmostEqual(result.Ti[i], expected_Ti[i], places=1)
        for i in range(len(expected_Hi)):
            self.assertAlmostEqual(result.Hi[i], expected_Hi[i], places=0)

        expected_deaerator_props = [0.9250777918, 503.6, 832.8619847*4.1868, 10]
        for i, expected_value in enumerate(expected_deaerator_props):
            self.assertAlmostEqual(result.deaerator_props[i], expected_value, places=1)

        expected_ejector_props = [{"g": 0.1550438044, "t": 426.4662, "h": 3333.60, "p": 0.97}]
        self.assertEqual(len(result.ejector_props), len(expected_ejector_props))
        for i, expected in enumerate(expected_ejector_props):
            actual = result.ejector_props[i]
            self.assertAlmostEqual(actual['g'], expected['g'], places=2)
            self.assertAlmostEqual(actual['t'], expected['t'], places=1)
            self.assertAlmostEqual(actual['h'], expected['h'], places=0)
            self.assertAlmostEqual(actual['p'], expected['p'], places=2)


class TestValveCalculatorTwo(unittest.TestCase):
    def setUp(self):
        params = CalculationParams(
            temperature_start=555,
            t_air=40,
            count_valves=2,
            p_ejector=[0.97],
            p_values=[130, 1.03]
        )
        valve_info = ValveInfo(
            id=2,
            name="Test Valve 2",
            round_radius=2,
            clearance=0.23,
            diameter=50,
            len_part1=190,
            len_part2=110
        )
        self.calculator = ValveCalculator(params, valve_info)

    def test_perform_calculations_two(self):
        result = self.calculator.perform_calculations()

        expected_Gi = [0.9634638651, 0.004586641266]
        expected_Pi_in = [130, 1.03]
        expected_Ti = [555.005, 39.980]
        expected_Hi = [832.8619847*4.1868, 40.24]

        for i in range(len(expected_Gi)):
            self.assertAlmostEqual(result.Gi[i], expected_Gi[i], places=3)
        for i in range(len(expected_Pi_in)):
            self.assertAlmostEqual(result.Pi_in[i], expected_Pi_in[i], places=2)
        for i in range(len(expected_Ti)):
            self.assertAlmostEqual(result.Ti[i], expected_Ti[i], places=0)
        for i in range(len(expected_Hi)):
            self.assertAlmostEqual(result.Hi[i], expected_Hi[i], places=0)

        expected_ejector_props = [
            {"g": 1.936101013, "t": 552.5649, "h": 860.2968256*4.1868, "p": 0.97}
        ]

        self.assertEqual(len(result.ejector_props), len(expected_ejector_props))
        for i, expected in enumerate(expected_ejector_props):
            actual = result.ejector_props[i]
            self.assertAlmostEqual(actual['g'], expected['g'], places=2)
            self.assertAlmostEqual(actual['t'], expected['t'], places=0)
            self.assertAlmostEqual(actual['h'], expected['h'], places=0)
            self.assertAlmostEqual(actual['p'], expected['p'], places=2)

# class TestValveCalculatorThree(unittest.TestCase):
#     def setUp(self):
#         params = CalculationParams(
#             temperature_start=555,
#             t_air=40,
#             count_valves=4,
#             p_ejector=[0.97, 0.97, 0.97],
#             p_values=[130, 7, 0.97, 1.03]
#         )
#         valve_info = ValveInfo(
#             id=3,
#             name="Test Valve 3",
#             round_radius=2,
#             clearance=0.205,
#             diameter=36,
#             len_part1=438.5,
#             len_part2=50,
#             len_part3=25,
#             len_part4=37.5
#         )
#         self.calculator = ValveCalculator(params, valve_info)
#
#     def test_perform_calculations_three(self):
#         result = self.calculator.perform_calculations()
#
#         expected_Gi = [0.3857, 0.0426, 0.0005, 0.0038]
#         expected_Pi_in = [13.0, 0.7, 0.097, 0.103]
#         expected_Ti = [555.0, 501.0, 498.0, 40.0]
#         expected_Hi = [3484.5, 3484.5, 3484.5, 40.24]
#
#         for i in range(len(expected_Gi)):
#             self.assertAlmostEqual(result.Gi[i], expected_Gi[i], places=3)
#         for i in range(len(expected_Pi_in)):
#             self.assertAlmostEqual(result.Pi_in[i], expected_Pi_in[i], places=2)
#         for i in range(len(expected_Ti)):
#             self.assertAlmostEqual(result.Ti[i], expected_Ti[i], places=0)
#         for i in range(len(expected_Hi)):
#             self.assertAlmostEqual(result.Hi[i], expected_Hi[i], places=0)
#
#         expected_deaerator_props = [1.370, 501.0, 3484.5, 0.7]
#         for i, expected_value in enumerate(expected_deaerator_props):
#             self.assertAlmostEqual(result.deaerator_props[i], expected_value, places=1)
#
#         expected_ejector_props = [
#             {"g": 0.157, "t": 498.0, "h": 3484.5, "p": 0.097},
#             {"g": 0.013, "t": 98.8, "h": 447.2, "p": 0.097}
#         ]
#
#         self.assertEqual(len(result.ejector_props), len(expected_ejector_props))
#         for i, expected in enumerate(expected_ejector_props):
#             actual = result.ejector_props[i]
#             self.assertAlmostEqual(actual['g'], expected['g'], places=2)
#             self.assertAlmostEqual(actual['t'], expected['t'], places=0)
#             self.assertAlmostEqual(actual['h'], expected['h'], places=0)
#             self.assertAlmostEqual(actual['p'], expected['p'], places=2)
#
#
# class TestValveCalculatorFour(unittest.TestCase):
#     def setUp(self):
#         params = CalculationParams(
#             temperature_start=555,
#             t_air=40,
#             count_valves=2,
#             p_ejector=[0.97, 0.97],
#             p_values=[130, 8.35, 1.03]
#         )
#         valve_info = ValveInfo(
#             id=4,
#             name="Test Valve 4",
#             round_radius=2,
#             clearance=0.28,
#             diameter=38,
#             len_part1=161.5,
#             len_part2=102.5,
#             len_part3=50.5
#         )
#         self.calculator = ValveCalculator(params, valve_info)
#
#     def test_perform_calculations_four(self):
#         result = self.calculator.perform_calculations()
#
#         expected_Gi = [1.0857, 0.0640, 0.0058]
#         expected_Pi_in = [13.0, 0.835, 0.103]
#         expected_Ti = [555.0, 501.7, 40.0]
#         expected_Hi = [3484.5, 3484.5, 40.24]
#
#         for i in range(len(expected_Gi)):
#             self.assertAlmostEqual(result.Gi[i], expected_Gi[i], places=3)
#         for i in range(len(expected_Pi_in)):
#             self.assertAlmostEqual(result.Pi_in[i], expected_Pi_in[i], places=2)
#         for i in range(len(expected_Ti)):
#             self.assertAlmostEqual(result.Ti[i], expected_Ti[i], places=0)
#         for i in range(len(expected_Hi)):
#             self.assertAlmostEqual(result.Hi[i], expected_Hi[i], places=0)
#
#         expected_deaerator_props = [2.043, 501.7, 3484.5, 0.835]
#         for i, expected_value in enumerate(expected_deaerator_props):
#             self.assertAlmostEqual(result.deaerator_props[i], expected_value, places=1)
#
#         expected_ejector_props = [{"g": 0.139, "t": 360.9, "h": 3198.2, "p": 0.097}]
#
#         self.assertEqual(len(result.ejector_props), len(expected_ejector_props))
#         for i, expected in enumerate(expected_ejector_props):
#             actual = result.ejector_props[i]
#             self.assertAlmostEqual(actual['g'], expected['g'], places=2)
#             self.assertAlmostEqual(actual['t'], expected['t'], places=0)
#             self.assertAlmostEqual(actual['h'], expected['h'], places=0)
#             self.assertAlmostEqual(actual['p'], expected['p'], places=2)


if __name__ == '__main__':
    unittest.main()