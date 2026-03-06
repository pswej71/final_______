import os
import google.generativeai as genai

def get_suggestions(telemetry_data: list, alerts: list):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        return {
            "insight": "Gemini API key not configured.",
            "recommendation": "Please add a valid GEMINI_API_KEY to your backend/.env file to enable AI insights.",
            "severity": "Info",
            "trend": "Unknown"
        }
    
    genai.configure(api_key=api_key)
    # Use gemini-1.5-flash for faster responses
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    You are an expert Solar Inverter AI analytics assistant. 
    Analyze the following recent telemetry data and alerts for a solar inverter system.
    
    Critical Context:
    Include "Predictive Failure Risk" in your analysis. If the predictive risk is high (e.g. > 70%), focus on preventive maintenance.
    
    Recent Alerts:
    {alerts}
    
    Provide your response in strict JSON format with the exact following keys:
    "insight": A brief technical analysis of the telemetry and predictive risk trends.
    "recommendation": Actionable advice for the user (e.g. "Clean panels", "Check cooling fan", "Schedule technical inspection").
    "severity": 'Low', 'Medium', 'High', or 'Critical'.
    "trend": A short sentence describing the performance and risk trajectory.
    
    Do not include markdown or backticks (```json) in the response, just return the raw parseable JSON object.
    
    Data summary (length={len(telemetry_data)}):
    {str(telemetry_data)[:1200]} # Including failure_risk fields in the context
    """
    
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:-3].strip()
        elif text.startswith("```"):
            text = text[3:-3].strip()
            
        import json
        return json.loads(text)
    except Exception as e:
        return {
            "insight": "Failed to generate AI suggestion.",
            "recommendation": str(e),
            "severity": "Error",
            "trend": "Unknown"
        }
