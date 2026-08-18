from django.test import SimpleTestCase
from unittest.mock import patch

from main.agents import (
    ChatbotInterface,
    GeminiAdapter,
    chatbot_agent,
)


class GeminiAdapterTests(SimpleTestCase):

    # --------------------------------------------------
    # ADAPTER IMPLEMENTATION TEST
    # --------------------------------------------------

    def test_gemini_adapter_implements_chatbot_interface(self):
        adapter = GeminiAdapter()

        self.assertIsInstance(
            adapter,
            ChatbotInterface
        )


    # --------------------------------------------------
    # ADAPTER FORWARDS PROMPT TO GEMINI
    # --------------------------------------------------

    @patch("main.agents.call_gemini")
    def test_adapter_calls_gemini_with_correct_prompt(
        self,
        mock_call_gemini
    ):
        mock_call_gemini.return_value = "Mock Gemini Response"

        adapter = GeminiAdapter()

        result = adapter.get_response(
            "Hello NutriBot"
        )

        mock_call_gemini.assert_called_once_with(
            "Hello NutriBot"
        )

        self.assertEqual(
            result,
            "Mock Gemini Response"
        )


class ChatbotAgentTests(SimpleTestCase):

    def setUp(self):
        self.user_progress = {
            "current_day": 5,
            "weight_change": 0,
            "meal_rate": 80,
            "exercise_rate": 60,
        }


    # --------------------------------------------------
    # USER NAME AND MESSAGE TEST
    # --------------------------------------------------

    @patch("main.agents.GeminiAdapter.get_response")
    def test_chatbot_prompt_contains_user_information(
        self,
        mock_get_response
    ):
        mock_get_response.return_value = "Mock Chatbot Response"

        result = chatbot_agent(
            "Test User",
            "How am I doing?",
            self.user_progress
        )

        mock_get_response.assert_called_once()

        prompt = mock_get_response.call_args[0][0]

        self.assertIn(
            "Test User",
            prompt
        )

        self.assertIn(
            "How am I doing?",
            prompt
        )

        self.assertEqual(
            result,
            "Mock Chatbot Response"
        )


    # --------------------------------------------------
    # CURRENT DAY TEST
    # --------------------------------------------------

    @patch("main.agents.GeminiAdapter.get_response")
    def test_chatbot_prompt_contains_current_day(
        self,
        mock_get_response
    ):
        mock_get_response.return_value = "Mock Response"

        chatbot_agent(
            "Test User",
            "Show my progress",
            self.user_progress
        )

        prompt = mock_get_response.call_args[0][0]

        self.assertIn(
            "Current Day: Day 5 of 15",
            prompt
        )


    # --------------------------------------------------
    # MEAL AND EXERCISE PROGRESS TEST
    # --------------------------------------------------

    @patch("main.agents.GeminiAdapter.get_response")
    def test_chatbot_prompt_contains_progress_rates(
        self,
        mock_get_response
    ):
        mock_get_response.return_value = "Mock Response"

        chatbot_agent(
            "Test User",
            "Show my progress",
            self.user_progress
        )

        prompt = mock_get_response.call_args[0][0]

        self.assertIn(
            "Meal Plan Follow Rate: 80%",
            prompt
        )

        self.assertIn(
            "Exercise Completion Rate: 60%",
            prompt
        )


    # --------------------------------------------------
    # CHATBOT USES ADAPTER
    # --------------------------------------------------

    @patch("main.agents.GeminiAdapter.get_response")
    def test_chatbot_uses_gemini_adapter(
        self,
        mock_get_response
    ):
        mock_get_response.return_value = "Adapter Response"

        result = chatbot_agent(
            "Test User",
            "Hello",
            self.user_progress
        )

        mock_get_response.assert_called_once()

        self.assertEqual(
            result,
            "Adapter Response"
        )
