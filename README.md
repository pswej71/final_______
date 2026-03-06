# Real-Time Solar Inverter Monitoring System

A complete full-stack solution for monitoring solar inverter telemetry, featuring a real-time React dashboard, FastAPI backend, Scikit-Learn based Machine Learning Anomaly Detection, and Generative AI suggestions using Google Gemini.

## 🛠 Tech Stack

- **Backend**: Python, FastAPI, SQLAlchemy (configurable for PostgreSQL/SQLite)
- **Frontend**: React.js (Vite), Recharts, Vanilla CSS (Premium Dark Mode)
- **Machine Learning**: Scikit-Learn (`IsolationForest`) for anomaly detection
- **AI Analytics**: Google Generative AI (Gemini 1.5 Flash)
- **Streaming**: WebSockets for live live updates
- **Deployment Ready**: Fully configured for local runs and Google Colab (`ngrok` integration).

## 🚀 Getting Started Locally

### 1. Setup Backend
1. Open a terminal in the `backend/` folder.
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # Windows:
   .\venv\Scripts\activate
   # Mac/Linux:
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up the environment variables:
   - Edit `backend/.env` to include your `GEMINI_API_KEY` and your `DATABASE_URL` (if you want to use PostgreSQL instead of the default SQLite).
5. Start the FastAPI server:
   ```bash
   uvicorn main:app --reload
   ```

### 2. Setup Frontend
1. Open a terminal in the `frontend/` folder.
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the development server:
   ```bash
   npm run dev
   ```
4. Open your browser to `http://localhost:5173`.

### 3. Generate Mock Data & Simulation
By default, the dashboard polls the `/api/simulator/generate` endpoint every 5 seconds, which dynamically adds new telemetry records to the database and streams them to the dashboard, testing both REST APIs and real-time frontend charts.

## 📓 Google Colab Integration

If you want to run the backend and ML training in Google Colab:
1. Upload the `notebooks/Colab_Solar_Monitoring.ipynb` notebook to Google Colab.
2. Upload the `data/generate_mock_csv.py` to Colab and run it to get historical datasets.
3. The Notebook demonstrates loading CSVs, training `IsolationForest`, and launching the FastAPI server directly inside Colab via `pyngrok`.
4. Grab the generated `ngrok` URL from the Notebook output and paste it into your `frontend/src/api.js` for the frontend to connect remotely to Colab!