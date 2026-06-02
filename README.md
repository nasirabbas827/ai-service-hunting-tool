# AI-Service-Hunting-tool  

A lightweight web application that helps users discover, evaluate, and visualize AI‑powered services (e.g., APIs, SaaS tools, and gig listings). The tool provides a searchable dashboard, user authentication, and data visualizations built on top of a simple SQLite database.

---  

## Overview  

The **AI-Service-Hunting-tool** enables users to:  

- Register and log in to a personal dashboard.  
- Search for AI service listings (gigs) and view detailed information.  
- Submit feedback on services.  
- Visualize aggregated data (e.g., popularity, ratings) through interactive charts.  

All UI components are built with HTML templates, while the backend logic resides in `app.py`. The data model is defined in `Database/extractor_db.sql`.

---  

## Features  

| ✅ | Feature |
|---|---------|
| **User Management** | Register, login, and personal dashboard (`register.html`, `user_login.html`, `user_dashboard.html`). |
| **Search & Detail View** | Search AI gigs and view full details (`view_gig.html`). |
| **Feedback System** | Submit and store feedback (`feedback.html`). |
| **Data Visualization** | Interactive charts for service metrics (`visualization.html`). |
| **Responsive Layout** | Base template (`base.html`) ensures a consistent look across pages. |
| **Simple Persistence** | SQLite database defined in `Database/extractor_db.sql`. |
| **Extensible Architecture** | Clear separation of concerns – HTML templates, Python routes, and SQL schema. |

---  

## Tech Stack  

| Layer | Technology |
|-------|------------|
| **Frontend** | HTML5, CSS (via Bootstrap or custom styles) |
| **Backend** | Python 3.x, Flask |
| **Database** | SQLite (schema in `Database/extractor_db.sql`) |
| **Visualization** | Chart.js / Plotly (integrated in `visualization.html`) |
| **Version Control** | Git / GitHub |

---  

## Installation  

1. **Clone the repository**  

   ```bash
   git clone https://github.com/your-username/AI-Service-Hunting-tool.git
   cd AI-Service-Hunting-tool
   ```

2. **Create a virtual environment** (recommended)  

   ```bash
   python -m venv venv
   source venv/bin/activate   # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**  

   ```bash
   pip install -r requirements.txt
   ```

   *If `requirements.txt` is missing, install the core packages manually:*  

   ```bash
   pip install flask
   pip install pandas   # optional, for data handling
   pip install chartjs   # or plotly, depending on the visualization library used
   ```

4. **Set up the database**  

   ```bash
   sqlite3 Database/extractor_db.sql < Database/extractor_db.sql
   ```

   This creates an `extractor.db` file (or the name you prefer) in the `Database` folder.

5. **Configure environment variables**  

   Create a `.env` file in the project root (or export variables in your shell) with at least:

   ```env
   FLASK_APP=app.py
   FLASK_ENV=development
   SECRET_KEY=YOUR_OWN_SECRET_KEY
   # If you use any external API:
   # EXTERNAL_API_KEY=YOUR_OWN_API_KEY
   ```

6. **Run the application**  

   ```bash
   flask run
   ```

   The app will be available at `http://127.0.0.1:5000`.

---  

## Usage  

1. **Open the web UI** – Navigate to `http://127.0.0.1:5000` in your browser.  
2. **Register** – Click *Register* and fill out the form (`register.html`).  
3.