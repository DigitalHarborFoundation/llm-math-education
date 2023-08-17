import os

import dotenv
import openai
import outlines
import outlines.models.text_completion

dotenv.load_dotenv(".env")
openai.api_key = os.environ["OPENAI_API_KEY"]

# doesn't work in a juypter notebook, for async reasons
model_name = "gpt-3.5-turbo"
complete = outlines.models.text_completion.openai(model_name)
expert = complete("Name an expert in quantum gravity.", stop_at=["\n", "."])
print(expert)
