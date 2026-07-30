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

def calculate_tdee(bmr, activity_level):
    """
    Calculate Total Daily Energy Expenditure (TDEE)
    based on activity level.
    """

    activity_factors = {
        "sedentary": 1.20,
        "lightly active": 1.375,
        "moderately active": 1.55,
        "very active": 1.725,
        "extra active": 1.90,
    }

    factor = activity_factors.get(activity_level.lower(), 1.20)

    return round(bmr * factor)
