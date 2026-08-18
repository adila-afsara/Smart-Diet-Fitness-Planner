from django.test import SimpleTestCase

from main.nutrition_calculator import (
    calculate_bmr,
    calculate_tdee,
    calculate_daily_calories,
    calculate_protein_goal,
)


class NutritionCalculatorTests(SimpleTestCase):

    # --------------------------------------------------
    # BMR TESTS
    # --------------------------------------------------

    def test_bmr_for_male(self):
        result = calculate_bmr(
            weight=70,
            height=175,
            age=25,
            gender="Male"
        )

        self.assertEqual(result, 1674)


    def test_bmr_for_female(self):
        result = calculate_bmr(
            weight=70,
            height=175,
            age=25,
            gender="Female"
        )

        self.assertEqual(result, 1508)


    # --------------------------------------------------
    # TDEE TESTS
    # --------------------------------------------------

    def test_tdee_beginner(self):
        result = calculate_tdee(
            bmr=1674,
            fitness_level="Beginner"
        )

        self.assertEqual(result, 2302)


    def test_tdee_intermediate(self):
        result = calculate_tdee(
            bmr=1674,
            fitness_level="Intermediate"
        )

        self.assertEqual(result, 2595)


    def test_tdee_advanced(self):
        result = calculate_tdee(
            bmr=1674,
            fitness_level="Advanced"
        )

        self.assertEqual(result, 2888)


    def test_tdee_unknown_level_uses_beginner_default(self):
        result = calculate_tdee(
            bmr=1674,
            fitness_level="Unknown"
        )

        self.assertEqual(result, 2302)


    # --------------------------------------------------
    # DAILY CALORIE LOGIC TESTS
    # --------------------------------------------------

    def test_daily_calories_lose_weight(self):
        result = calculate_daily_calories(
            tdee=2300,
            goal="Lose Weight"
        )

        self.assertEqual(result, 1800)


    def test_daily_calories_minimum_limit(self):
        result = calculate_daily_calories(
            tdee=1400,
            goal="Lose Weight"
        )

        self.assertEqual(result, 1200)


    def test_daily_calories_gain_weight(self):
        result = calculate_daily_calories(
            tdee=2300,
            goal="Gain Weight"
        )

        self.assertEqual(result, 2600)


    def test_daily_calories_stay_healthy(self):
        result = calculate_daily_calories(
            tdee=2300,
            goal="Stay Healthy"
        )

        self.assertEqual(result, 2300)


    # --------------------------------------------------
    # PROTEIN GOAL LOGIC TESTS
    # --------------------------------------------------

    def test_protein_goal_lose_weight(self):
        result = calculate_protein_goal(
            weight=70,
            goal="Lose Weight"
        )

        self.assertEqual(result, 112)


    def test_protein_goal_gain_weight(self):
        result = calculate_protein_goal(
            weight=70,
            goal="Gain Weight"
        )

        self.assertEqual(result, 126)


    def test_protein_goal_stay_healthy(self):
        result = calculate_protein_goal(
            weight=70,
            goal="Stay Healthy"
        )

        self.assertEqual(result, 84)
