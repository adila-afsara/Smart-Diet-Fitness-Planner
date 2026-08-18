from django.test import TestCase


class ProgressCalculationTests(TestCase):

    def test_day7_meal_follow_rate(self):
        meal_follow_days = 5

        rate = round(
            (meal_follow_days / 7) * 100
        )

        self.assertEqual(rate, 71)


    def test_day15_meal_follow_rate(self):
        meal_follow_days = 12

        rate = round(
            (meal_follow_days / 15) * 100
        )

        self.assertEqual(rate, 80)


    def test_weight_loss_calculation(self):
        starting_weight = 68.0
        ending_weight = 66.5

        weight_change = (
            ending_weight - starting_weight
        )

        self.assertEqual(
            weight_change,
            -1.5
        )


    def test_weight_gain_calculation(self):
        starting_weight = 68.0
        ending_weight = 70.0

        weight_change = (
            ending_weight - starting_weight
        )

        self.assertEqual(
            weight_change,
            2.0
        )
