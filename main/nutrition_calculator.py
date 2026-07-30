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
