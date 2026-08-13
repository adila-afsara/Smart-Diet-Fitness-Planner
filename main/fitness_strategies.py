from abc import ABC, abstractmethod


class FitnessStrategy(ABC):

    @abstractmethod
    def generate_plan(self, user_profile):
        pass


class BeginnerStrategy(FitnessStrategy):

    def generate_plan(self, user_profile):
        from .agents import fitness_agent

        return fitness_agent(user_profile)


class IntermediateStrategy(FitnessStrategy):

    def generate_plan(self, user_profile):
        from .agents import fitness_agent

        return fitness_agent(user_profile)


class AdvancedStrategy(FitnessStrategy):

    def generate_plan(self, user_profile):
        from .agents import fitness_agent

        return fitness_agent(user_profile)

def get_fitness_strategy(activity_level):
    if activity_level == "Beginner":
        return BeginnerStrategy()

    elif activity_level == "Intermediate":
        return IntermediateStrategy()

    elif activity_level == "Advanced":
        return AdvancedStrategy()

    return BeginnerStrategy()
