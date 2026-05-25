"""
Teste simples de conexão com a API do Gemini.
"""
import google.generativeai as genai
from config import GEMINI_API_KEY


def main():
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-2.5-flash")
    prompt = "Explique em uma frase o que é um requisito de software."
    response = model.generate_content(prompt)
    print(response.text)


if __name__ == "__main__":
    main()
