import google.generativeai as genai

genai.configure(api_key='AIzaSyBWfKBE2NCwiCb11oCYXRPEX3d6BEpe_Mg')


model = genai.GenerativeModel(model_name="gemini-1.5-flash")
# title = 'For Vivo S1 Pro Transparent Cxunddo Shockproof Back Cover Phone Case - Camera'
# # response = model.generate_content([f"Give me only one product identification text of product title: {title}"])
# response = model.generate_content([f"Translate to Bangla: {title}", "Give me just translated text"])
# response = model.generate_content([f":Write me one new SEO friendly title based on: {title}"])
# print(response.text)