from abc import ABC, abstractmethod


class FitnessStrategy(ABC):

    @abstractmethod
    def generate_plan(self, user_profile):
        pass

class BeginnerStrategy(FitnessStrategy):

    strategy_name = "Beginner"

    strategy_rules = (
        "Light walks, bodyweight exercises and stretching. "
        "Workout duration should be 30-35 minutes."
    )

    def generate_plan(self, user_profile):
        from .agents import fitness_agent

        return fitness_agent(
            user_profile,
            self.strategy_name,
            self.strategy_rules
        )


class IntermediateStrategy(FitnessStrategy):

    strategy_name = "Intermediate"

    strategy_rules = (
        "HIIT, jogging and moderate strength training. "
        "Workout duration should be 40-45 minutes."
    )

    def generate_plan(self, user_profile):
        from .agents import fitness_agent

        return fitness_agent(
            user_profile,
            self.strategy_name,
            self.strategy_rules
        )


class AdvancedStrategy(FitnessStrategy):

    strategy_name = "Advanced"

    strategy_rules = (
        "Intense cardio and strength training. "
        "Workout duration should be 55-60 minutes."
    )

    def generate_plan(self, user_profile):
        from .agents import fitness_agent

        return fitness_agent(
            user_profile,
            self.strategy_name,
            self.strategy_rules
        )
    
def get_fitness_strategy(activity_level):
    if activity_level == "Beginner":
        return BeginnerStrategy()

    elif activity_level == "Intermediate":
        return IntermediateStrategy()

    elif activity_level == "Advanced":
        return AdvancedStrategy()

    return BeginnerStrategy()    
