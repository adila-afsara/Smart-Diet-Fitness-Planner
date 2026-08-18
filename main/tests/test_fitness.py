from django.test import SimpleTestCase
from unittest.mock import patch

from main.fitness_strategies import (
    FitnessStrategy,
    BeginnerStrategy,
    IntermediateStrategy,
    AdvancedStrategy,
    get_fitness_strategy,
)


class FitnessStrategySelectionTests(SimpleTestCase):

    # --------------------------------------------------
    # STRATEGY SELECTION TESTS
    # --------------------------------------------------

    def test_beginner_strategy_selected(self):
        strategy = get_fitness_strategy("Beginner")

        self.assertIsInstance(
            strategy,
            BeginnerStrategy
        )


    def test_intermediate_strategy_selected(self):
        strategy = get_fitness_strategy("Intermediate")

        self.assertIsInstance(
            strategy,
            IntermediateStrategy
        )


    def test_advanced_strategy_selected(self):
        strategy = get_fitness_strategy("Advanced")

        self.assertIsInstance(
            strategy,
            AdvancedStrategy
        )


    def test_unknown_level_defaults_to_beginner(self):
        strategy = get_fitness_strategy("Unknown")

        self.assertIsInstance(
            strategy,
            BeginnerStrategy
        )


class FitnessStrategyGeneratePlanTests(SimpleTestCase):

    # --------------------------------------------------
    # MOCK FITNESS AGENT
    # --------------------------------------------------

    @patch("main.agents.fitness_agent")
    def test_beginner_strategy_calls_fitness_agent(
        self,
        mock_fitness_agent
    ):
        mock_fitness_agent.return_value = "Mock Beginner Plan"

        user_profile = {
            "age": 25,
            "weight": 70,
            "health_goal": "Stay Healthy",
            "activity_level": "Beginner",
            "workout_location": "Home",
            "health_condition": "None",
        }

        strategy = BeginnerStrategy()

        result = strategy.generate_plan(
            user_profile
        )

        mock_fitness_agent.assert_called_once_with(
            user_profile,
            "Beginner",
            strategy.strategy_rules
        )

        self.assertEqual(
            result,
            "Mock Beginner Plan"
        )


    @patch("main.agents.fitness_agent")
    def test_intermediate_strategy_calls_fitness_agent(
        self,
        mock_fitness_agent
    ):
        mock_fitness_agent.return_value = "Mock Intermediate Plan"

        user_profile = {
            "age": 25,
            "weight": 70,
            "health_goal": "Stay Healthy",
            "activity_level": "Intermediate",
            "workout_location": "Gym",
            "health_condition": "None",
        }

        strategy = IntermediateStrategy()

        result = strategy.generate_plan(
            user_profile
        )

        mock_fitness_agent.assert_called_once_with(
            user_profile,
            "Intermediate",
            strategy.strategy_rules
        )

        self.assertEqual(
            result,
            "Mock Intermediate Plan"
        )


    @patch("main.agents.fitness_agent")
    def test_advanced_strategy_calls_fitness_agent(
        self,
        mock_fitness_agent
    ):
        mock_fitness_agent.return_value = "Mock Advanced Plan"

        user_profile = {
            "age": 25,
            "weight": 70,
            "health_goal": "Stay Healthy",
            "activity_level": "Advanced",
            "workout_location": "Gym",
            "health_condition": "None",
        }

        strategy = AdvancedStrategy()

        result = strategy.generate_plan(
            user_profile
        )

        mock_fitness_agent.assert_called_once_with(
            user_profile,
            "Advanced",
            strategy.strategy_rules
        )

        self.assertEqual(
            result,
            "Mock Advanced Plan"
        )
