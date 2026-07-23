import os
import requests
from dotenv import load_dotenv

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
    All our 4 agents will use this function!
    Like a phone — all agents use the same phone to call Gemini!
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


# ════════════════════════════════════════
# 🧠 AGENT 1 — NUTRITION & DIET AGENT
# ════════════════════════════════════════

def nutrition_agent(user_profile):
    prompt = f"""
You are a professional nutritionist creating a 15-day diet plan for a Bangladeshi user.

User Details:
- Age: {user_profile.get('age')} years
- Weight: {user_profile.get('weight')} kg
- Height: {user_profile.get('height')} cm
- Gender: {user_profile.get('gender')}
- Health Goal: {user_profile.get('health_goal')}
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
def fitness_agent(user_profile):
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

IMPORTANT RULES:
1. Create a 15-day workout plan
2. Match exercises to fitness level:
   - Beginner: light walks, bodyweight exercises, stretching (30-35 mins)
   - Intermediate: HIIT, jogging, weights (40-45 mins)
   - Advanced: intense cardio, strength training (55-60 mins)
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
    return call_gemini(prompt)
