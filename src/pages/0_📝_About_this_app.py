import streamlit as st

st.set_page_config(
    page_title="ChatGPT for middle-school math education - About this app",
    page_icon="📝",
)

st.markdown(
    """# About this app

This Streamlit app is a demo that applies OpenAI's ChatGPT to provide math conversation and problem-solving hints to students.

The core technical approach is to use ["retrieval augmented generation"](https://www.promptingguide.ai/techniques/rag) to improve the relevance of the responses to middle-school math students.

#### People

This app was created by Zachary Levonian (LEVI Engineering Hub) and Owen Henkel (Rori/Rising Academies).

Contact Zach (<levon003@umn.edu>) with any questions.

#### Code and data

This app's code is hosted [on GitHub](https://github.com/levon003/llm-math-education).
Feel free to open an [issue](https://github.com/levon003/llm-math-education/issues) with questions, comments, or requests.

This app currently uses data from three sources:
 - Sample student queries are from [MathNation](https://www.mathnation.com/).
 - Prealgebra textbook is from [OpenStax](https://openstax.org/details/books/prealgebra-2e).
 - Rori micro-lessons were provided by [Rising Academies](https://www.risingacademies.com/).
""",
)
