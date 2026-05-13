from google import genai

api_key = "AIzaSyDWs2sawCsDG9pN8yTq5RdRC_D0nhu4FpY"
client = genai.Client(api_key=api_key)

# List available models
try:
    models = client.models.list()
    print("Available models:")
    for model in models:
        print(f"  - {model.name}")
except Exception as e:
    print(f"Error listing models: {e}")
