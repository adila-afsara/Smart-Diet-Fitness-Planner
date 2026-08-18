from django.test import SimpleTestCase
from unittest.mock import patch

from main.agents import health_tracking_agent


class HealthTrackingAgentTests(SimpleTestCase):

    def setUp(self):
        self.user_data = {
            "starting_weight": 68,
            "current_weight": 66.5,
            "height": 165,
            "health_goal": "Stay Healthy",
            "health_condition": "None",
        }

    # --------------------------------------------------
    # DAY 7 REPORT TEST
    # --------------------------------------------------

    @patch("main.agents.call_gemini")
    def test_day7_report_prompt(self, mock_call_gemini):

        mock_call_gemini.return_value = "Mock Day 7 Feedback"

        logs = {
            "meal_follow_days": 5,
            "exercise_days": 4,
            "avg_water": 1.8,
            "weight_change": -1.5,
        }

        result = health_tracking_agent(
            self.user_data,
            logs,
            report_days=7
        )

        # Gemini should be called exactly once
        mock_call_gemini.assert_called_once()

        # Get the prompt sent to Gemini
        prompt = mock_call_gemini.call_args[0][0]

        self.assertIn(
            "Day 7 Progress Report",
            prompt
        )

        self.assertIn(
            "Day 1 to Day 7",
            prompt
        )

        self.assertIn(
            "5 out of 7",
            prompt
        )

        self.assertIn(
            "4 out of 7",
            prompt
        )

        self.assertEqual(
            result,
            "Mock Day 7 Feedback"
        )


    # --------------------------------------------------
    # DAY 15 FINAL REPORT TEST
    # --------------------------------------------------

    @patch("main.agents.call_gemini")
    def test_day15_report_prompt(self, mock_call_gemini):

        mock_call_gemini.return_value = "Mock Final Feedback"

        logs = {
            "meal_follow_days": 12,
            "exercise_days": 10,
            "avg_water": 2.0,
            "weight_change": -1.5,
        }

        result = health_tracking_agent(
            self.user_data,
            logs,
            report_days=15
        )

        mock_call_gemini.assert_called_once()

        prompt = mock_call_gemini.call_args[0][0]

        self.assertIn(
            "Final 15-Day Progress Report",
            prompt
        )

        self.assertIn(
            "Day 1 to Day 15",
            prompt
        )

        self.assertIn(
            "12 out of 15",
            prompt
        )

        self.assertIn(
            "10 out of 15",
            prompt
        )

        self.assertEqual(
            result,
            "Mock Final Feedback"
        )


    # --------------------------------------------------
    # WATER UNIT TEST
    # --------------------------------------------------

    @patch("main.agents.call_gemini")
    def test_water_is_sent_as_liters_per_day(
        self,
        mock_call_gemini
    ):

        mock_call_gemini.return_value = "Mock Feedback"

        logs = {
            "meal_follow_days": 5,
            "exercise_days": 4,
            "avg_water": 1.8,
            "weight_change": -1.5,
        }

        health_tracking_agent(
            self.user_data,
            logs,
            report_days=7
        )

        prompt = mock_call_gemini.call_args[0][0]

        self.assertIn(
            "1.8 liters per day",
            prompt
        )


    # --------------------------------------------------
    # WEIGHT CHANGE TEST
    # --------------------------------------------------

    @patch("main.agents.call_gemini")
    def test_weight_change_included_in_prompt(
        self,
        mock_call_gemini
    ):

        mock_call_gemini.return_value = "Mock Feedback"

        logs = {
            "meal_follow_days": 5,
            "exercise_days": 4,
            "avg_water": 1.8,
            "weight_change": -1.5,
        }

        health_tracking_agent(
            self.user_data,
            logs,
            report_days=7
        )

        prompt = mock_call_gemini.call_args[0][0]

        self.assertIn(
            "-1.5 kg",
            prompt
        )


    # --------------------------------------------------
    # DEFAULT REPORT TYPE TEST
    # --------------------------------------------------

    @patch("main.agents.call_gemini")
    def test_invalid_report_days_defaults_to_day7(
        self,
        mock_call_gemini
    ):

        mock_call_gemini.return_value = "Mock Feedback"

        logs = {
            "meal_follow_days": 3,
            "exercise_days": 3,
            "avg_water": 1.5,
            "weight_change": 0,
        }

        health_tracking_agent(
            self.user_data,
            logs,
            report_days=10
        )

        prompt = mock_call_gemini.call_args[0][0]

        self.assertIn(
            "Day 7 Progress Report",
            prompt
        )

        self.assertIn(
            "3 out of 7",
            prompt
        )
