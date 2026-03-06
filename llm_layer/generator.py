import os
import google.generativeai as genai
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

genai.configure(api_key=os.getenv("GEMINI_API_KEY", "dummy_key"))
model = genai.GenerativeModel('gemini-1.5-pro-latest')

def generate_explanation(risk_score, shap_features, telemetry_summary):
    prompt_version = os.getenv("LLM_PROMPT_VERSION", "2")
    
    if prompt_version == "1":
        # Prompt Version 1: Basic explanation generation
        prompt = f"""
        Explain this inverter warning to an operator.
        Risk score: {risk_score}
        Telemetry summary: {telemetry_summary}
        Features that caused this:
        """
        for f in shap_features:
            prompt += f"- {f['feature']}: {f['importance']}\n"
    else:
        # Prompt Version 2: Improved prompt
        prompt = f"""
        You are an expert Solar Plant AI diagnostician. Analyze the following inverter risk prediction and generate a clear, concise natural language explanation for plant operators.

        Input Data:
        - Overall Risk Score: {risk_score} (0-1 scale)
        - Telemetry Summary: {telemetry_summary}
        - Top Risk Contributing Features (SHAP values):
        """
        for f in shap_features:
            prompt += f"  * {f['feature']}: {round(f['importance'], 4)}\n"
        
        prompt += """
        Output Requirements:
        1. Identify the likely inverter status (e.g. shutdown risk within 7 days).
        2. Correlate the top features with the telemetry.
        3. Recommend a specific preventive maintenance action.
        Keep it under 3 sentences. Tone must be professional and urgent.
        """
        
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logger.error(f"GenAI Error: {e}")
        return "Explanation could not be generated due to an AI service error. Please inspect the inverter."

def format_maintenance_ticket(inverter_id, risk_score, block, explanation):
    prompt = f"""
    Draft a short maintenance ticket based on the following:
    Inverter ID: {inverter_id}
    Block: {block}
    Risk: {risk_score}
    Explanation: {explanation}
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Maintenance Ticket\nInverter {inverter_id} in {block} requires inspection. Risk score: {risk_score}."
