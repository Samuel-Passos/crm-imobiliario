import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv("./robo_disponibilidade/.env")
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Define a function
def generate_image(prompt: str):
    """Gera uma imagem realista para um post imobiliário de luxo.
    
    Args:
        prompt: Descrição visual detalhada da imagem (luz, materiais, ambiente).
    """
    return {"status": "success", "url": "/static/generated/test.jpg"}

# Initialize model with tools
model = genai.GenerativeModel(
    model_name='gemini-flash-latest',
    tools=[generate_image]
)

print(f"Model tools: {model._tools}")
