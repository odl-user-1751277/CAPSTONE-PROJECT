import os
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("AZURE_OPENAI_KEY")
endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

print(f"🔍 Key: {api_key[:4]}... (hidden)")
print(f"🔍 Endpoint: {endpoint}")
print(f"🔍 Deployment: {deployment}")

client = AzureOpenAI(
    api_key=api_key,
    api_version="2023-05-15",
    azure_endpoint=endpoint,
)

try:
    response = client.chat.completions.create(
        model=deployment,
        messages=[{"role": "user", "content": "Say hello"}],
        temperature=0.5,
        max_tokens=10
    )
    print("✅ Connection successful! Response:")
    print(response.choices[0].message.content)
except Exception as e:
    print("❌ Connection failed:")
    print(e)