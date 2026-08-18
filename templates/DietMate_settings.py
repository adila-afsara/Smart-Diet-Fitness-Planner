<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Settings — DietMate BD</title>

  <link
    href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Inter:wght@400;500;600;700&display=swap"
    rel="stylesheet"
  />

  <style>
    :root {
      --white: #FFFFFF;
      --offwhite: #FFFDF5;
      --yellow: #F5C518;
      --yellow-light: #FEF9E7;
      --red: #D62828;
      --red-light: #FDEAEA;
      --orange: #F77F00;
      --orange-light: #FFF0DC;
      --green: #2E8B57;
      --green-light: #E8F5EE;
      --green-hover: #216640;
      --text: #1A1A1A;
      --muted: #666666;
      --border: #EEE8DA;
      --sidebar-w: 240px;
    }

    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }

    body {
      font-family: 'Inter', sans-serif;
      background: var(--offwhite);
      color: var(--text);
      display: flex;
      min-height: 100vh;
    }

    /* =========================================
       SIDEBAR
       ========================================= */

    .sidebar {
      width: var(--sidebar-w);
      background: var(--white);
      border-right: 3px solid var(--green);
      display: flex;
      flex-direction: column;
      position: fixed;
      top: 0;
      left: 0;
      bottom: 0;
      z-index: 100;
    }

    .sidebar-logo {
      padding: 22px 20px 16px;
      border-bottom: 2px solid var(--offwhite);
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .logo-icon {
      width: 38px;
      height: 38px;
      background: var(--red);
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 18px;
      border: 2px solid var(--yellow);
    }

    .logo-text {
      font-family: 'Playfair Display', serif;
      font-size: 18px;
      font-weight: 700;
      color: var(--red);
    }

    .logo-text span {
      color: var(--green);
    }

    .folk-strip {
      height: 8px;
      background: repeating-linear-gradient(
        90deg,
        var(--red) 0px,
        var(--red) 8px,
        var(--yellow) 8px,
        var(--yellow) 16px,
        var(--orange) 16px,
        var(--orange) 24px,
        var(--green) 24px,
        var(--green) 32px
      );
    }

    .sidebar-nav {
      flex: 1;
      padding: 16px 0;
      display: flex;
      flex-direction: column;
      gap: 2px;
      overflow-y: auto;
    }

    .nav-item {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 11px 20px;
      font-size: 14px;
      font-weight: 500;
      color: var(--muted);
      cursor: pointer;
      border-left: 3px solid transparent;
      transition: all 0.2s;
      text-decoration: none;
    }

    .nav-item:hover {
      color: var(--green);
      background: var(--offwhite);
      border-left-color: var(--orange);
    }

    .nav-item.active {
      color: var(--red);
      background: var(--red-light);
      border-left-color: var(--red);
      font-weight: 600;
    }

    .nav-icon {
      font-size: 18px;
      flex-shrink: 0;
    }

    .nav-section-label {
      font-size: 10px;
      font-weight: 600;
      color: var(--muted);
      letter-spacing: 1.5px;
      text-transform: uppercase;
      padding: 14px 20px 4px;
    }

    .sidebar-user {
      padding: 16px 20px;
      border-top: 2px solid var(--offwhite);
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .user-avatar {
      width: 36px;
      height: 36px;
      background: var(--orange);
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 16px;
      border: 2px solid var(--yellow);
      flex-shrink: 0;
    }

    .user-name {
      font-size: 13px;
      font-weight: 600;
    }

    .user-goal {
      font-size: 11px;
      color: var(--muted);
      margin-top: 2px;
    }

    /* =========================================
       MAIN AREA
       ========================================= */

    .main {
      margin-left: var(--sidebar-w);
      flex: 1;
      display: flex;
      flex-direction: column;
      min-width: 0;
    }

    .topbar {
      background: var(--white);
      border-bottom: 3px solid var(--green);
      padding: 16px 32px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      position: sticky;
      top: 0;
      z-index: 50;
      box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }

    .topbar-left h2 {
      font-family: 'Playfair Display', serif;
      font-size: 22px;
      margin-bottom: 3px;
    }

    .topbar-left p {
      font-size: 13px;
      color: var(--muted);
    }

    .back-btn {
      text-decoration: none;
      color: var(--green);
      border: 2px solid var(--green);
      background: var(--white);
      border-radius: 8px;
      padding: 9px 16px;
      font-size: 13px;
      font-weight: 600;
      transition: all 0.2s;
    }

    .back-btn:hover {
      background: var(--green);
      color: white;
    }

    .content {
      padding: 28px 32px 40px;
      width: 100%;
      max-width: 1150px;
    }

    /* =========================================
       MESSAGES
       ========================================= */

    .message {
      padding: 13px 16px;
      border-radius: 9px;
      margin-bottom: 18px;
      font-size: 13px;
      font-weight: 500;
    }

    .message.success {
      background: var(--green-light);
      color: var(--green);
      border: 1px solid #B9DFC9;
    }

    .message.error {
      background: var(--red-light);
      color: var(--red);
      border: 1px solid #F2B7B7;
    }

    .message.warning {
      background: var(--yellow-light);
      color: #7D6100;
      border: 1px solid #F1D778;
    }

    .message.info {
      background: var(--orange-light);
      color: #A95000;
      border: 1px solid #F6C18E;
    }

    /* =========================================
       SETTINGS CARDS
       ========================================= */

    .settings-intro {
      background: var(--yellow-light);
      border: 1px solid #ECD56A;
      border-radius: 12px;
      padding: 16px 18px;
      margin-bottom: 24px;
      display: flex;
      gap: 12px;
      align-items: flex-start;
    }

    .settings-intro-icon {
      font-size: 24px;
      line-height: 1;
    }

    .settings-intro h3 {
      font-family: 'Playfair Display', serif;
      font-size: 17px;
      margin-bottom: 4px;
    }

    .settings-intro p {
      color: var(--muted);
      font-size: 13px;
      line-height: 1.6;
    }

    .settings-form {
      display: flex;
      flex-direction: column;
      gap: 22px;
    }

    .settings-card {
      background: var(--white);
      border: 2px solid var(--border);
      border-radius: 14px;
      padding: 24px;
    }

    .card-header {
      display: flex;
      align-items: center;
      gap: 12px;
      padding-bottom: 16px;
      margin-bottom: 20px;
      border-bottom: 1px solid var(--border);
    }

    .card-icon {
      width: 42px;
      height: 42px;
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 21px;
      flex-shrink: 0;
    }

    .icon-red {
      background: var(--red-light);
    }

    .icon-green {
      background: var(--green-light);
    }

    .icon-orange {
      background: var(--orange-light);
    }

    .card-header h3 {
      font-family: 'Playfair Display', serif;
      font-size: 18px;
      margin-bottom: 3px;
    }

    .card-header p {
      font-size: 12px;
      color: var(--muted);
    }

    .form-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 18px;
    }

    .form-group {
      display: flex;
      flex-direction: column;
      gap: 7px;
    }

    .form-group.full-width {
      grid-column: 1 / -1;
    }

    .form-label {
      font-size: 12px;
      font-weight: 600;
      color: var(--text);
    }

    .required {
      color: var(--red);
    }

    .form-input,
    .form-select,
    .form-textarea {
      width: 100%;
      border: 2px solid var(--offwhite);
      background: var(--offwhite);
      border-radius: 8px;
      padding: 10px 12px;
      font-family: 'Inter', sans-serif;
      font-size: 13px;
      color: var(--text);
      outline: none;
      transition: all 0.2s;
    }

    .form-input:focus,
    .form-select:focus,
    .form-textarea:focus {
      background: var(--white);
      border-color: var(--orange);
    }

    .form-textarea {
      resize: vertical;
      min-height: 92px;
      line-height: 1.5;
    }

    .field-help {
      font-size: 11px;
      color: var(--muted);
      line-height: 1.4;
    }

    /* =========================================
       ACTION BUTTONS
       ========================================= */

    .form-actions {
      background: var(--white);
      border: 2px solid var(--border);
      border-radius: 14px;
      padding: 18px 24px;
      display: flex;
      justify-content: flex-end;
      align-items: center;
      gap: 12px;
    }

    .cancel-btn {
      text-decoration: none;
      padding: 10px 20px;
      border: 2px solid var(--orange);
      color: var(--orange);
      background: transparent;
      border-radius: 8px;
      font-size: 13px;
      font-weight: 600;
      transition: all 0.2s;
    }

    .cancel-btn:hover {
      background: var(--orange);
      color: white;
    }

    .save-btn {
      padding: 11px 22px;
      border: none;
      color: white;
      background: var(--green);
      border-radius: 8px;
      font-family: 'Inter', sans-serif;
      font-size: 13px;
      font-weight: 700;
      cursor: pointer;
      transition: background 0.2s;
    }

    .save-btn:hover {
      background: var(--green-hover);
    }

    /* =========================================
       RESPONSIVE
       ========================================= */

    @media (max-width: 900px) {
      .form-grid {
        grid-template-columns: 1fr;
      }

      .form-group.full-width {
        grid-column: auto;
      }
    }

    @media (max-width: 760px) {
      .sidebar {
        width: 200px;
      }

      .main {
        margin-left: 200px;
      }

      .content {
        padding: 22px 18px;
      }

      .topbar {
        padding: 14px 18px;
      }
    }
  </style>
</head>

<body>

  <!-- =========================================
       SIDEBAR
       ========================================= -->

  <aside class="sidebar">

    <div class="sidebar-logo">
      <div class="logo-icon">🥗</div>
      <div class="logo-text">Diet<span>Mate</span> BD</div>
    </div>

    <div class="folk-strip"></div>

    <nav class="sidebar-nav">

      <div class="nav-section-label">Main</div>

      <a
        class="nav-item {% if request.resolver_match.url_name == 'dashboard' %}active{% endif %}"
        href="{% url 'dashboard' %}"
      >
        <span class="nav-icon">🏠</span>
        Dashboard
      </a>

      <a
        class="nav-item {% if request.resolver_match.url_name == 'diet_plan' %}active{% endif %}"
        href="{% url 'diet_plan' %}"
      >
        <span class="nav-icon">🍱</span>
        My Diet Plan
      </a>

      <a
        class="nav-item {% if request.resolver_match.url_name == 'fitness_plan' %}active{% endif %}"
        href="{% url 'fitness_plan' %}"
      >
        <span class="nav-icon">🏃</span>
        Fitness Plan
      </a>

      <a
        class="nav-item {% if request.resolver_match.url_name == 'progress' %}active{% endif %}"
        href="{% url 'progress' %}"
      >
        <span class="nav-icon">📊</span>
        Progress & BMI
      </a>

      <div class="nav-section-label">Tools</div>

      <a
        class="nav-item {% if request.resolver_match.url_name == 'chatbot' %}active{% endif %}"
        href="{% url 'chatbot' %}"
      >
        <span class="nav-icon">💬</span>
        Chatbot
      </a>

      <a
        class="nav-item {% if request.resolver_match.url_name == 'medical_specialist' or request.resolver_match.url_name == 'medical_specialist_detail' %}active{% endif %}"
        href="{% url 'medical_specialist' %}"
      >
        <span class="nav-icon">🏥</span>
        Find Dietitian
      </a>

      <a
        class="nav-item"
        href="{% url 'progress' %}#daily-log"
      >
        <span class="nav-icon">📅</span>
        Daily Log
      </a>

      <div class="nav-section-label">Account</div>

      <a
        class="nav-item {% if request.resolver_match.url_name == 'settings' %}active{% endif %}"
        href="{% url 'settings' %}"
      >
        <span class="nav-icon">⚙️</span>
        Settings
      </a>

      <a
        class="nav-item"
        href="{% url 'logout' %}"
      >
        <span class="nav-icon">🚪</span>
        Logout
      </a>

    </nav>

    <div class="sidebar-user">

      <div class="user-avatar">
        {% if profile.gender == "Female" %}
          👩
        {% elif profile.gender == "Male" %}
          👨
        {% else %}
          🧑
        {% endif %}
      </div>

      <div>
        <div class="user-name">{{ user.full_name }}</div>
        <div class="user-goal">
          Goal:
          {% if profile.health_goal %}
            {{ profile.health_goal }}
          {% else %}
            Not set
          {% endif %}
        </div>
      </div>

    </div>

  </aside>


  <!-- =========================================
       MAIN
       ========================================= -->

  <main class="main">

    <div class="topbar">

      <div class="topbar-left">
        <h2>⚙️ Account & Profile Settings</h2>
        <p>Update the information DietMate BD uses for your account and personalized plans.</p>
      </div>

      <a href="{% url 'dashboard' %}" class="back-btn">
        ← Back to Dashboard
      </a>

    </div>


    <div class="content">

      <!-- Django Messages -->
      {% if messages %}
        {% for message in messages %}
          <div class="message {{ message.tags }}">
            {{ message }}
          </div>
        {% endfor %}
      {% endif %}


      <div class="settings-intro">

        <div class="settings-intro-icon">💡</div>

        <div>
          <h3>Your DietMate Profile</h3>
          <p>
            Keep your information current so the application can use the latest
            details when displaying your account and creating personalized plans.
          </p>
        </div>

      </div>


      <!-- =========================================
           SETTINGS FORM
           ========================================= -->

      <form
        method="POST"
        action="{% url 'settings' %}"
        class="settings-form"
      >

        {% csrf_token %}


        <!-- =========================================
             ACCOUNT INFORMATION
             ========================================= -->

        <section class="settings-card">

          <div class="card-header">

            <div class="card-icon icon-red">
              👤
            </div>

            <div>
              <h3>Account Information</h3>
              <p>Update your basic account details.</p>
            </div>

          </div>


          <div class="form-grid">

            <div class="form-group">

              <label class="form-label" for="full_name">
                Full Name <span class="required">*</span>
              </label>

              <input
                class="form-input"
                type="text"
                id="full_name"
                name="full_name"
                value="{{ user.full_name }}"
                required
              />

            </div>


            <div class="form-group">

              <label class="form-label" for="email">
                Email Address <span class="required">*</span>
              </label>

              <input
                class="form-input"
                type="email"
                id="email"
                name="email"
                value="{{ user.email }}"
                required
              />

              <div class="field-help">
                This email is used to identify your DietMate account.
              </div>

            </div>

          </div>

        </section>


        <!-- =========================================
             HEALTH PROFILE
             ========================================= -->

        <section class="settings-card">

          <div class="card-header">

            <div class="card-icon icon-green">
              🩺
            </div>

            <div>
              <h3>Health Profile</h3>
              <p>Update the personal information used by DietMate.</p>
            </div>

          </div>


          <div class="form-grid">


            <!-- Age -->
            <div class="form-group">

              <label class="form-label" for="age">
                Age
              </label>

              <input
                class="form-input"
                type="number"
                id="age"
                name="age"
                min="1"
                value="{{ profile.age|default_if_none:'' }}"
              />

            </div>


            <!-- Gender -->
            <div class="form-group">

              <label class="form-label" for="gender">
                Gender
              </label>

              <select
                class="form-select"
                id="gender"
                name="gender"
              >

                <option value="">Select gender</option>

                <option
                  value="Female"
                  {% if profile.gender == "Female" %}selected{% endif %}
                >
                  Female
                </option>

                <option
                  value="Male"
                  {% if profile.gender == "Male" %}selected{% endif %}
                >
                  Male
                </option>

                <option
                  value="Other"
                  {% if profile.gender == "Other" %}selected{% endif %}
                >
                  Other
                </option>

              </select>

            </div>


            <!-- Height -->
            <div class="form-group">

              <label class="form-label" for="height">
                Height (cm)
              </label>

              <input
                class="form-input"
                type="number"
                step="0.1"
                min="1"
                id="height"
                name="height"
                value="{{ profile.height|default_if_none:'' }}"
              />

            </div>


            <!-- Weight -->
            <div class="form-group">

              <label class="form-label" for="weight">
                Current Weight (kg)
              </label>

              <input
                class="form-input"
                type="number"
                step="0.1"
                min="1"
                id="weight"
                name="weight"
                value="{{ profile.weight|default_if_none:'' }}"
              />

            </div>


            <!-- Health Goal -->
            <div class="form-group">

              <label class="form-label" for="health_goal">
                Health Goal
              </label>

              <input
                class="form-input"
                type="text"
                id="health_goal"
                name="health_goal"
                value="{{ profile.health_goal|default_if_none:'' }}"
                placeholder="e.g. Maintain Weight"
              />

            </div>


            <!-- Health Condition -->
            <div class="form-group">

              <label class="form-label" for="health_condition">
                Health Condition
              </label>

              <input
                class="form-input"
                type="text"
                id="health_condition"
                name="health_condition"
                value="{{ profile.health_condition|default_if_none:'' }}"
                placeholder="e.g. None"
              />

            </div>

          </div>

        </section>


        <!-- =========================================
             DIET & FITNESS PREFERENCES
             ========================================= -->

        <section class="settings-card">

          <div class="card-header">

            <div class="card-icon icon-orange">
              🍱
            </div>

            <div>
              <h3>Diet & Fitness Preferences</h3>
              <p>Update the preferences used when creating your plans.</p>
            </div>

          </div>


          <div class="form-grid">


            <!-- Activity Level -->
            <div class="form-group">

              <label class="form-label" for="activity_level">
                Activity Level
              </label>

              <select
                class="form-select"
                id="activity_level"
                name="activity_level"
              >

                <option value="">
                  Select activity level
                </option>

                <option
                  value="Beginner"
                  {% if profile.activity_level == "Beginner" %}selected{% endif %}
                >
                  Beginner
                </option>

                <option
                  value="Intermediate"
                  {% if profile.activity_level == "Intermediate" %}selected{% endif %}
                >
                  Intermediate
                </option>

                <option
                  value="Advanced"
                  {% if profile.activity_level == "Advanced" %}selected{% endif %}
                >
                  Advanced
                </option>

              </select>

            </div>


            <!-- Workout Location -->
            <div class="form-group">

              <label class="form-label" for="workout_location">
                Workout Location
              </label>

              <input
                class="form-input"
                type="text"
                id="workout_location"
                name="workout_location"
                value="{{ profile.workout_location|default_if_none:'' }}"
                placeholder="e.g. Home or Gym"
              />

            </div>


            <!-- Weekly Budget -->
            <div class="form-group">

              <label class="form-label" for="weekly_budget">
                Weekly Food Budget (BDT)
              </label>

              <input
                class="form-input"
                type="number"
                step="0.01"
                min="0"
                id="weekly_budget"
                name="weekly_budget"
                value="{{ profile.weekly_budget|default_if_none:'' }}"
              />

            </div>


            <!-- Location -->
            <div class="form-group">

              <label class="form-label" for="location">
                Location
              </label>

              <input
                class="form-input"
                type="text"
                id="location"
                name="location"
                value="{{ profile.location|default_if_none:'' }}"
                placeholder="e.g. Dhaka"
              />

            </div>


            <!-- Food Preferences -->
            <div class="form-group full-width">

              <label class="form-label" for="food_preferences">
                Food Preferences
              </label>

              <textarea
                class="form-textarea"
                id="food_preferences"
                name="food_preferences"
                placeholder="Enter your preferred foods or dietary preferences."
              >{{ profile.food_preferences|default_if_none:'' }}</textarea>

            </div>


            <!-- Avoid Foods -->
            <div class="form-group full-width">

              <label class="form-label" for="avoid_foods">
                Foods to Avoid
              </label>

              <textarea
                class="form-textarea"
                id="avoid_foods"
                name="avoid_foods"
                placeholder="Enter foods you prefer not to include."
              >{{ profile.avoid_foods|default_if_none:'' }}</textarea>

            </div>

          </div>

        </section>


        <!-- =========================================
             ACTIONS
             ========================================= -->

        <div class="form-actions">

          <a
            href="{% url 'dashboard' %}"
            class="cancel-btn"
          >
            Cancel
          </a>

          <button
            type="submit"
            class="save-btn"
          >
            💾 Save Changes
          </button>

        </div>

      </form>

    </div>

  </main>

</body>
</html>
