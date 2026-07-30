def calculate_bmr(weight, height, age, gender):
    """
    Calculate Basal Metabolic Rate (BMR)
    using the Mifflin-St Jeor Equation.
    """

    gender = gender.lower()

    if gender == "male":
        bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5
    else:
        bmr = (10 * weight) + (6.25 * height) - (5 * age) - 161

    return round(bmr)

def calculate_tdee(bmr, fitness_level):
    """
    Estimate TDEE from the user's fitness level.
    """

    fitness_factors = {
        "Beginner": 1.375,
        "Intermediate": 1.55,
        "Advanced": 1.725
    }

    factor = fitness_factors.get(fitness_level, 1.375)

    return round(bmr * factor)

def calculate_daily_calories(tdee, goal):
    """
    Calculate recommended daily calories
    according to the user's goal.
    """

    if goal == "Lose Weight":
        return max(tdee - 500, 1200)

    elif goal == "Gain Weight":
        return tdee + 300

    else:      # Stay Healthy
        return tdee

def calculate_protein_goal(weight, goal):
    """
    Calculate daily protein requirement.
    """

    if goal == "Lose Weight":
        return round(weight * 1.6)

    elif goal == "Gain Weight":
        return round(weight * 1.8)

    else:      # Stay Healthy
        return round(weight * 1.2)
