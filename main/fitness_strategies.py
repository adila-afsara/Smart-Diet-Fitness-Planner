from abc import ABC, abstractmethod


class FitnessStrategy(ABC):

    @abstractmethod
    def generate_plan(self, user_profile):
        pass


class BeginnerStrategy(FitnessStrategy):

    def generate_plan(self, user_profile):
        from .agents import fitness_agent

        return fitness_agent(
            user_profile,
            "Beginner",
            "Light walks, bodyweight exercises and stretching. "
            "Workout duration should be 30-35 minutes."
        )


class IntermediateStrategy(FitnessStrategy):

    def generate_plan(self, user_profile):
        from .agents import fitness_agent

        return fitness_agent(
            user_profile,
            "Intermediate",
            "HIIT, jogging and moderate strength training. "
            "Workout duration should be 40-45 minutes."
        )


class AdvancedStrategy(FitnessStrategy):

    def generate_plan(self, user_profile):
        from .agents import fitness_agent

        return fitness_agent(
            user_profile,
            "Advanced",
            "Intense cardio and strength training. "
            "Workout duration should be 55-60 minutes."
        )
def get_fitness_strategy(activity_level):
    if activity_level == "Beginner":
        return BeginnerStrategy()

    elif activity_level == "Intermediate":
        return IntermediateStrategy()

    elif activity_level == "Advanced":
        return AdvancedStrategy()

    return BeginnerStrategy()    
