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
