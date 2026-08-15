import os
import requests 
import json
import re
from dotenv import load_dotenv
from .nutrition_calculator import (
    calculate_bmr,
    calculate_tdee,
    calculate_daily_calories,
    calculate_protein_goal
)

load_dotenv(override=True)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


# Fallback — read directly from .env if os.getenv fails
if not GEMINI_API_KEY:
    with open('.env', 'r') as f:
        for line in f:
            if line.startswith('GEMINI_API_KEY='):
                GEMINI_API_KEY = line.strip().split('=', 1)[1]
                break

GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-lite:generateContent?key={GEMINI_API_KEY}"

def call_gemini(prompt):
    """
    
    This is the BASE function that talks to Gemini API.
    
    """
    payload = {
       "contents": [{
           "parts": [{"text": prompt}]
       }],
       "generationConfig": {
           "maxOutputTokens": 8192
       }
   }
    headers = {"Content-Type": "application/json"}

    try:
        response = requests.post(GEMINI_URL, json=payload, headers=headers)
        if response.status_code == 200:
            data = response.json()
            return data['candidates'][0]['content']['parts'][0]['text']
        else:
            return f"Error: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Error: {str(e)}"

def medical_specialist_agent(user_profile):
    """
    Medical Specialist Recommendation Agent.

    Uses Google Search grounding to find current,
    publicly available healthcare professional
    information in Bangladesh.
    """

    prompt = f"""
You are the Medical Specialist Recommendation Agent for DietMate BD.

Your job has TWO separate stages:

STAGE 1:
Determine which healthcare professional categories are appropriate
for this user's health condition and health goal.

STAGE 2:
Use Google Search to find REAL, CURRENT, PUBLICLY LISTED healthcare
professionals in Bangladesh matching those categories.

You MUST search the web before returning recommendations.


=========================================
USER PROFILE
=========================================

Age:
{user_profile.get("age")}

Gender:
{user_profile.get("gender")}

Height:
{user_profile.get("height")} cm

Weight:
{user_profile.get("weight")} kg

Health Goal:
{user_profile.get("health_goal")}

Health Condition:
{user_profile.get("health_condition")}

Activity Level:
{user_profile.get("activity_level")}

Food Preferences:
{user_profile.get("food_preferences")}

Foods to Avoid:
{user_profile.get("avoid_foods")}

Preferred Location:
{user_profile.get("location") or "Bangladesh"}

User Search:
{user_profile.get("search_query") or "None"}

Requested Specialty:
{user_profile.get("specialty_query") or "None"}


=========================================
RECOMMENDATION LOGIC
=========================================

Use the user's health condition to determine appropriate
professional categories.

Examples:

Diabetes
→ Endocrinologist + Dietitian/Nutritionist

High Blood Pressure
→ Cardiologist or Internal Medicine Specialist
+ Dietitian/Nutritionist

High Cholesterol
→ Cardiologist/Internal Medicine Specialist
+ Dietitian/Nutritionist

Obesity
→ Dietitian/Nutritionist
+ appropriate physician where useful

Underweight
→ Dietitian/Nutritionist
+ General/Internal Medicine Physician where appropriate

Thyroid Disorder
→ Endocrinologist
+ Dietitian/Nutritionist

Kidney Disease
→ Nephrologist
+ qualified Dietitian/Nutritionist

Heart Disease
→ Cardiologist
+ Dietitian/Nutritionist

Digestive Problems
→ Gastroenterologist
+ Dietitian/Nutritionist

Food Allergy
→ appropriate physician/allergy specialist where available
+ Dietitian/Nutritionist

PCOS
→ Gynecologist and/or Endocrinologist
+ Dietitian/Nutritionist

No medical condition
→ Dietitian/Nutritionist.
A fitness professional may also be recommended for general
fitness goals if appropriate.


=========================================
GOOGLE SEARCH REQUIREMENTS
=========================================

You MUST use Google Search.

Search specifically for healthcare professionals practicing
in Bangladesh.

Prioritize the user's requested location.

Try searches using combinations such as:

professional name/category
+ hospital
+ location
+ Bangladesh

Prefer information from:

1. Official hospital websites
2. Official clinic websites
3. Official institutional doctor directories
4. Official professional profile pages

Avoid relying on random blogs or unverified directory pages
when an official institutional source is available.


=========================================
STRICT VERIFICATION RULES
=========================================

1. Recommend ONLY professionals you can identify from
   current web search results.

2. Never invent a doctor's name.

3. Never construct or guess a website URL.

4. The "website" value must be an EXACT page discovered
   through web search.

5. Prefer the doctor's official hospital/profile page
   for "website".

6. If no individual profile page exists, an official
   hospital or clinic page may be used.

7. Never invent a phone number.

8. "contact_number" may contain:

   - the professional's publicly listed appointment number, OR
   - the official hospital/clinic appointment number.

9. Only return a phone number when it appears in a
   public web source associated with that professional
   or institution.

10. Never invent an email address.

11. Never invent consultation fees.

12. Never invent available days or schedules.

13. Never invent ratings.

14. If information cannot be verified, return null.

15. Null is ALWAYS better than guessed information.


=========================================
SOURCE REQUIREMENT
=========================================

The "source" field is extremely important.

For every professional:

- source must contain the EXACT URL of the webpage
  used to verify the professional.

- Prefer official hospital/clinic sources.

- Never write "Gemini AI" in the source field.

- Never invent source URLs.

If no trustworthy source URL can be identified,
return null.


=========================================
SEARCH FILTER RULES
=========================================

The user's search request is:

{user_profile.get("search_query") or "No specific search"}

The requested specialty is:

{user_profile.get("specialty_query") or "No specific specialty"}

The location is:

{user_profile.get("location") or "Bangladesh"}

If the user provided a specific search term,
specialty, hospital, doctor name, or location,
you MUST prioritize it.

Do NOT ignore these search parameters.


=========================================
NUMBER OF RESULTS
=========================================

Recommend between 3 and 5 professionals when enough
verified results can be found.

If only 1 or 2 trustworthy professionals can be verified,
return only those.

DO NOT invent additional professionals just to reach 3 results.


=========================================
SUMMARY
=========================================

Write a personalized summary of 3-5 sentences.

The summary should:

- mention the user's health condition
- mention the user's health goal
- explain which professional categories are relevant
- mention that nearby professionals were prioritized
- encourage consultation with a qualified healthcare professional

Do NOT diagnose the user.

Do NOT claim the recommendation replaces professional care.


=========================================
OUTPUT REQUIREMENTS
=========================================

Return ONLY the JSON requested by the response schema.

For each professional:

full_name:
Real professional's complete name.

title:
Qualifications if clearly available.

specialist_type:
Examples:
Dietitian
Nutritionist
Cardiologist
Endocrinologist
Gynecologist
Nephrologist
Gastroenterologist
General Physician
Physiotherapist
Fitness Trainer

specialty:
More specific clinical specialty when available.

hospital_clinic:
Current hospital or clinic affiliation.

location:
City or area.

consultation_fee_bdt:
Only if publicly verified.
Otherwise null.

website:
Exact discovered official profile or institutional URL.
Never construct one.

contact_number:
Publicly listed professional or institutional
appointment/contact number.
Otherwise null.

email:
Only publicly verified professional/institutional email.
Otherwise null.

available_days:
Only when clearly stated by a reliable source.
Otherwise null.

rating:
Only when a reliable source explicitly provides one.
Otherwise null.

notes:
Briefly explain why this professional is relevant
to this user's health condition or goal.

source:
Exact webpage URL used to verify this result.

Search the web carefully now and return only verified results.
"""

    return call_gemini_with_search(prompt)


# ════════════════════════════════════════
# 🧠 AGENT 1 — NUTRITION & DIET AGENT
# ════════════════════════════════════════

def nutrition_agent(user_profile):

    print("Nutrition Agent Started")
    # Calculate nutrition targets

    bmr = calculate_bmr(
        float(user_profile.get("weight")),
        float(user_profile.get("height")),
        int(user_profile.get("age")),
        user_profile.get("gender")
    )
    print("BMR =", bmr)

    tdee = calculate_tdee(
        bmr,
        user_profile.get("activity_level")
    )
    print("TDEE =", tdee)
    daily_calories = calculate_daily_calories(
                    tdee,
                    user_profile.get("health_goal")
    )
    print("Calories =", daily_calories)
   
    protein_goal = calculate_protein_goal(
                float(user_profile.get("weight")),
                user_profile.get("health_goal")
    )
    print("Protein =", protein_goal)
    print("===== Nutrition Calculation =====")
    print("BMR:", bmr)
    print("TDEE:", tdee)
    print("Daily Calories:", daily_calories)
    print("Protein Goal:", protein_goal)
    print("===============================")
    prompt = f"""
You are a professional nutritionist creating a 15-day diet plan for a Bangladeshi user.

User Details:
- Age: {user_profile.get('age')} years
- Weight: {user_profile.get('weight')} kg
- Height: {user_profile.get('height')} cm
- Gender: {user_profile.get('gender')}
- Health Goal: {user_profile.get('health_goal')}
Nutrition Targets:
- Estimated BMR: {bmr} kcal/day
- Estimated TDEE: {tdee} kcal/day
- Daily Calorie Target: {daily_calories} kcal/day
- Daily Protein Target: {protein_goal} g

- Health Condition: {user_profile.get('health_condition')}
- Weekly Budget: ৳{user_profile.get('weekly_budget')} BDT
- Preferred Foods: {user_profile.get('food_preferences')}
- Foods to Avoid: {user_profile.get('avoid_foods')}

IMPORTANT RULES:
1. Use preferred foods as BASE ingredients
2. Add other healthy local Bangladeshi foods for nutrition balance
3. NEVER use foods from the avoid list
4. Every day must have Breakfast, Lunch, Dinner and Snack
5. All foods must be locally available in Bangladesh
6. Total daily cost must stay within daily budget (weekly budget / 7)
7. Adjust meals for health condition:
   - Diabetes: low sugar, low refined carbs, high fiber
   - High Blood Pressure: low sodium, high potassium
   - High Cholesterol: low saturated fat, high omega-3
   - None: balanced healthy meals
8. Bangladeshi people commonly enjoy chai (tea) with breakfast or as a snack, and roti as a staple — include chai for breakfast/snack time where appropriate, and use roti as a regular option across meals, unless it conflicts with the user's health condition or avoid list
9. The total calories from Breakfast, Lunch, Snack and Dinner for each day should be approximately equal to the Daily Calorie Target (within ±50 kcal).

10. The total daily protein should be close to the Daily Protein Target.

11. Distribute calories approximately as:
- Breakfast: 25%
- Lunch: 35%
- Snack: 10%
- Dinner: 30%

12. Do not exceed the user's daily budget while meeting the calorie and protein targets.
CRITICAL: You MUST respond with ONLY a valid JSON array. No other text before or after.
The JSON must follow this exact format:

[
  {{
    "day": 1,
    "meals": [
      {{
        "meal_type": "Breakfast",
        "meal_name": "Boiled Eggs with Roti",
        "ingredients": "2 boiled eggs, 2 roti, 1 cup tea",
        "calories": 320,
        "protein": 14,
        "carbs": 35,
        "fats": 10,
        "cost_bdt": 45
      }},
      {{
        "meal_type": "Lunch",
        "meal_name": "Rice with Dal and Shak",
        "ingredients": "1 cup rice, 1 bowl dal, mixed shak",
        "calories": 480,
        "protein": 18,
        "carbs": 75,
        "fats": 8,
        "cost_bdt": 70
      }},
      {{
        "meal_type": "Snack",
        "meal_name": "Banana with Peanuts",
        "ingredients": "1 banana, handful peanuts",
        "calories": 180,
        "protein": 5,
        "carbs": 28,
        "fats": 6,
        "cost_bdt": 25
      }},
      {{
        "meal_type": "Dinner",
        "meal_name": "Fish Curry with Rice",
        "ingredients": "1 piece fish, 1 cup rice, vegetables",
        "calories": 500,
        "protein": 28,
        "carbs": 65,
        "fats": 12,
        "cost_bdt": 80
      }}
    ]
  }}
]

IMPORTANT: Generate ALL 15 days. Start from day 1 to day 15.
Each day must have exactly 4 meals: Breakfast, Lunch, Snack, Dinner.
Do not stop before day 15. Generate the complete JSON array now.
"""
    # Call twice if needed - first get days 1-8, then 9-15
    response1 = call_gemini(prompt + "\nGenerate days 1 to 8 only.")
    response2 = call_gemini(prompt + "\nGenerate days 9 to 15 only. Start the JSON array from day 9.")

    # Try to combine both responses
    try:
        clean1 = response1.strip()
        if clean1.startswith('```'):
            clean1 = clean1.split('```')[1]
            if clean1.startswith('json'):
                clean1 = clean1[4:]
        clean1 = clean1.strip().rstrip(',').rstrip(']')

        clean2 = response2.strip()
        if clean2.startswith('```'):
            clean2 = clean2.split('```')[1]
            if clean2.startswith('json'):
                clean2 = clean2[4:]
        clean2 = clean2.strip().lstrip('[')

        combined = clean1 + ',' + clean2
        return combined
    except:
        return response1


# ════════════════════════════════════════
# 🏃 AGENT 2 — FITNESS AGENT
# ════════════════════════════════════════
def fitness_agent(user_profile, strategy, strategy_rules):
    """

    This agent generates a personalized 15-day fitness plan
    based on the user's fitness level and workout location!
    """
    prompt = f"""
You are a professional fitness trainer creating a 15-day workout plan for a Bangladeshi user.

User Details:
- Age: {user_profile.get('age')} years
- Weight: {user_profile.get('weight')} kg
- Health Goal: {user_profile.get('health_goal')}
- Fitness Level: {user_profile.get('activity_level')}
- Workout Location: {user_profile.get('workout_location')}
- Health Condition: {user_profile.get('health_condition')}
- Training Strategy: {strategy}
- Strategy Rules: {strategy_rules}

IMPORTANT RULES:
1. Create a 15-day workout plan
2. Follow the selected training strategy and its strategy rules exactly.
3. If workout location is Home: no gym equipment needed
4. If workout location is Gym: include equipment exercises
5. Include rest days (every 3rd day) — mark these with "is_rest_day": true and an empty exercises list
6. For each exercise show: name, duration in minutes, sets, reps, estimated calories burned
7. If user has health condition, adjust intensity accordingly

CRITICAL: You MUST respond with ONLY a valid JSON array. No other text before or after.
The JSON must follow this exact format:

[
  {{
    "day": 1,
    "is_rest_day": false,
    "exercises": [
      {{
        "exercise_name": "Morning Walk",
        "duration_minutes": 15,
        "sets": null,
        "reps": null,
        "calories_burned": 60
      }},
      {{
        "exercise_name": "Bodyweight Squats",
        "duration_minutes": 10,
        "sets": 3,
        "reps": 10,
        "calories_burned": 50
      }}
    ]
  }},
  {{
    "day": 3,
    "is_rest_day": true,
    "exercises": []
  }}
]

IMPORTANT: Generate ALL 15 days. Start from day 1 to day 15.
Do not stop before day 15. Generate the complete JSON array now.
"""
    response1 = call_gemini(prompt + "\nGenerate days 1 to 8 only.")
    response2 = call_gemini(prompt + "\nGenerate days 9 to 15 only. Start the JSON array from day 9.")

    try:
        clean1 = response1.strip()
        if clean1.startswith('```'):
            clean1 = clean1.split('```')[1]
            if clean1.startswith('json'):
                clean1 = clean1[4:]
        clean1 = clean1.strip().rstrip(',').rstrip(']')

        clean2 = response2.strip()
        if clean2.startswith('```'):
            clean2 = clean2.split('```')[1]
            if clean2.startswith('json'):
                clean2 = clean2[4:]
        clean2 = clean2.strip().lstrip('[')

        combined = clean1 + ',' + clean2
        return combined
    except:
        return response1
# ════════════════════════════════════════
# 📊 AGENT 3 — HEALTH TRACKING AGENT
# ════════════════════════════════════════
def health_tracking_agent(user_data, logs):
    """
    
    This agent analyzes the user's daily logs and generates
    progress reports with AI feedback!
    """
    prompt = f"""
You are a health tracking expert analyzing a Bangladeshi user's progress.

User Details:
- Starting Weight: {user_data.get('starting_weight')} kg
- Current Weight: {user_data.get('current_weight')} kg
- Height: {user_data.get('height')} cm
- Health Goal: {user_data.get('health_goal')}
- Health Condition: {user_data.get('health_condition')}

Progress Logs (last 7 days):
- Days meal plan followed: {logs.get('meal_follow_days')} out of 7
- Days exercise completed: {logs.get('exercise_days')} out of 7
- Average water intake: {logs.get('avg_water')} glasses per day
- Weight change: {logs.get('weight_change')} kg

Please provide:
1. BMI calculation and category
2. Analysis of their progress
3. What they did well
4. What needs improvement
5. Specific recommendations for next cycle
6. Motivational message
7. Keep it friendly, encouraging and specific to Bangladeshi context

Generate the progress report now.
"""
    return call_gemini(prompt)


#Interface For Chatbot Gemini Adapter
from abc import ABC, abstractmethod


class ChatbotInterface(ABC):

    @abstractmethod
    def get_response(self, prompt):
        pass


class GeminiAdapter(ChatbotInterface):

    def get_response(self, prompt):
        return call_gemini(prompt)
    
# ════════════════════════════════════════
# 💬 AGENT 4 — MOTIVATIONAL CHATBOT AGENT
# ════════════════════════════════════════
def chatbot_agent(user_name, user_message, user_progress):
    """

    This agent responds to user messages with personalized
    motivation, health tips, and encouragement!
    """
    prompt = f"""
You are NutriBot, a friendly and motivational AI health assistant for a Bangladeshi diet and fitness app.

User Name: {user_name}
User's Message: {user_message}

User's Current Progress:
- Current Day: Day {user_progress.get('current_day')} of 15
- Weight Lost/Gained: {user_progress.get('weight_change')} kg
- Meal Plan Follow Rate: {user_progress.get('meal_rate')}%
- Exercise Completion Rate: {user_progress.get('exercise_rate')}%

IMPORTANT RULES:
1. Be friendly, warm and encouraging
2. Keep responses short and motivating (2-4 sentences)
3. Reference their actual progress in your response
4. Give practical tips related to Bangladeshi lifestyle
5. If they missed a workout or meal — be understanding, not harsh
6. Celebrate their achievements enthusiastically
7. Always end with an encouraging statement
8. Never give medical advice — suggest consulting a doctor for medical issues

Respond to the user's message now.
"""
    gemini_adapter = GeminiAdapter()
    return gemini_adapter.get_response(prompt)
    
# ════════════════════════════════════════
# 🏥 AGENT 5 — DIETITIAN/Medical Specialist RECOMMENDER AGENT
# ════════════════════════════════════════

def medical_specialist_agent(user_profile):
    """
    AI Agent:
    Analyzes the user's health profile and recommends
    REAL healthcare professionals in Bangladesh.

    Recommendations include dietitians, nutritionists,
    fitness trainers and medical specialists based on
    the user's health condition and location.
    """

    prompt = f"""
You are the Medical Recommendation AI Agent for DietMate BD.

Your responsibility is to analyze the user's health profile and recommend REAL healthcare professionals in Bangladesh who best match the user's health condition, health goal, lifestyle, and location.

Always prioritize evidence-based healthcare recommendations.

If possible, recommend professionals whose information is available on official hospital websites. If an official website cannot be identified, return null instead of inventing one.

When appropriate, try to recommend professionals from different categories rather than multiple professionals from the same category, unless the user's condition specifically requires otherwise.

Never make up medical specialists by your own if they don't exist in real life.


=================================
USER PROFILE
=================================

Age: {user_profile.get("age")}
Gender: {user_profile.get("gender")}
Height: {user_profile.get("height")} cm
Weight: {user_profile.get("weight")} kg
Health Goal: {user_profile.get("health_goal")}
Health Condition: {user_profile.get("health_condition")}
Activity Level: {user_profile.get("activity_level")}
Food Preferences: {user_profile.get("food_preferences")}
Foods to Avoid: {user_profile.get("avoid_foods")}
Location: {user_profile.get("location")}

=================================
YOUR TASK
=================================

Analyze the user's profile carefully and recommend REAL healthcare professionals in Bangladesh that best match the user's health condition, health goal, and location.

Possible healthcare professionals include:

- Dietitian
- Nutritionist
- Fitness Trainer
- General Physician
- Cardiologist
- Endocrinologist
- Neurologist
- Gastroenterologist
- Nephrologist
- Orthopedic Specialist
- Physiotherapist
- Gynecologist

=================================
RULES
=================================

1. Recommend only REAL healthcare professionals in Bangladesh.

2. Recommend between 3 and 5 professionals whenever possible.

3. Prioritize professionals located in or near the user's location.

4. If the user's health condition is "None", recommend:
   - Dietitian
   - Nutritionist
   - Fitness Trainer

5. If the user has a medical condition, recommend the appropriate specialist(s) together with a Dietitian or Nutritionist whenever beneficial.

6. Never invent doctor names, phone numbers, consultation fees, email addresses, ratings, websites, or hospital names.

7. If any information is unavailable, return null for that field.

8. Prefer official hospital websites or official doctor profile pages.

9. Do not recommend duplicate professionals.

10. In the "notes" field, briefly explain why each professional is suitable for this user.

11. Recommendations should assist users in finding healthcare professionals but should never replace consultation with a licensed medical professional.

12. Return ONLY valid JSON.

13. Do NOT include markdown.

14. Do NOT use ```json.

15. Do NOT write any explanation before or after the JSON.


=================================
RECOMMENDATION GUIDELINES
=================================

Examples only:

• Diabetes → Endocrinologist + Dietitian
• High Blood Pressure → Cardiologist + Dietitian
• High Cholesterol → Cardiologist + Dietitian
• Obesity → Dietitian + Fitness Trainer
• Underweight → Dietitian + Nutritionist
• Thyroid Disorder → Endocrinologist + Dietitian
• Kidney Disease → Nephrologist + Dietitian
• Heart Disease → Cardiologist + Dietitian
• Digestive Problems → Gastroenterologist + Dietitian
• Food Allergy → General Physician + Dietitian
• PCOS → Gynecologist + Dietitian
• None → Dietitian + Nutritionist + Fitness Trainer

=================================
SUMMARY REQUIREMENTS
=================================

Generate a personalized summary before listing the recommended specialists.

The summary should:

1. Be 3–5 complete sentences (around 60–100 words).

2. Be written in a warm, professional, and supportive tone.

3. Mention the user's:
   - health condition
   - health goal
   - lifestyle (if relevant)

4. Explain WHY these specialist categories were recommended.

5. Mention that nearby professionals are prioritized whenever possible.

6. Encourage the user to consult a licensed healthcare professional.

7. Do NOT mention the doctors' names.

8. Do NOT simply say "based on your profile."

Write the summary naturally as if speaking directly to the user inside the DietMate BD application.

=================================
OUTPUT FORMAT
=================================

{{
  "summary": "A personalized 3–5 sentence recommendation following the Summary Requirements above.",

  "recommended_specialists": [
    {{
      "full_name": "Dr. Example Name",

      "title": "MBBS, FCPS, MD or null",

      "specialist_type": "Cardiologist",

      "specialty": "Hypertension & Preventive Cardiology",

      "hospital_clinic": "Example Hospital",

      "location": "Dhaka",

      "consultation_fee_bdt": null,

      "website": "https://examplehospital.com/doctor-profile",

      "contact_number": null,

      "email": null,

      "available_days": null,

      "rating": null,

      "notes": "Recommended because the user has high blood pressure and wants to lose weight.",

      "source": "Gemini AI"
    }}
  ]
}}

IMPORTANT

- Your response MUST begin with '{{'
- Your response MUST end with '}}'
- Output ONLY valid JSON
"""
    # Pass enable_search=True specifically for doctor lookup
    return call_gemini(prompt)

def parse_gemini_json(ai_response):
    """
    Cleans and parses Gemini JSON responses.
    Returns a Python dictionary/list if successful,
    otherwise returns None.
    """

    if not ai_response:
        return None

    try:
        # Remove markdown code blocks
        clean = ai_response.strip()

        clean = re.sub(r"^```json", "", clean, flags=re.IGNORECASE)
        clean = re.sub(r"^```", "", clean)
        clean = re.sub(r"```$", "", clean)

        clean = clean.strip()

        return json.loads(clean)

    except Exception as e:
        print("Gemini JSON Error:", e)
        return None

def quote_agent():
    prompt = """
    Generate a short, inspiring health, diet, or fitness Quote of the Day
    tailored for a user in Bangladesh.

    The quote may be written in either Bangla or English.
    Vary the language naturally between different generated quotes.
    Keep it warm, practical, culturally relatable, and concise.

    Return ONLY valid JSON in this format:

    {
        "quote": "quote here",
        "author": "DietMate Health Tip"
    }

    Do not include markdown or any explanation.
    """

    return call_gemini(prompt)
