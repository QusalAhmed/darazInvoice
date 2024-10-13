import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
genai.configure(api_key=os.getenv('GENAI_API_KEY'))

model = genai.GenerativeModel(model_name="gemini-1.5-flash")

if __name__ == '__main__':
    title = 'A Beautiful chandelier Light'
    response = model.generate_content([f"I have a title of a product. The title is: {title}. The description of the product"])
    print(response.text)
