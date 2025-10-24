import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Get API key from .env file
api_key = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI client *with* your API key
client = OpenAI(api_key=api_key)

# Create response
response = client.responses.create(
    model="gpt-5",
    input="Write a short bedtime story about a unicorn."
)

# Print result
print(response.output[0].content[0].text)
from openai import OpenAI

client = OpenAI(
  api_key="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"
)

response = client.responses.create(
  model="gpt-5-nano",
  input="write a haiku about ai",
  store=True,
)

print(response.output_text);
