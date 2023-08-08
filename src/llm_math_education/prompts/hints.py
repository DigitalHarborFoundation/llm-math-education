intro_prompts = {
    "hint_sequence": {
        "pretty_name": "Hint sequence",
        "messages": [
            {
                "role": "system",
                "content": """You are going to act as a mathematics tutor for a 13 year old student who is in grade 8 or 9.
This student lives in Ghana or Nigeria.
You will be encouraging and factual.
{rori_microlesson_texts}
{openstax_subsection_texts}
Prefer simple, short responses.
If the student says something inappropriate or off topic you will say you can only focus on mathematics and ask them if they have any math-related follow-up questions.
""",
            },
        ],
    },
}

misconception_identification = {
    "creature_ai": {
        "pretty_name": "Nancy Otero's misconception identification prompt",
        "messages": [
            {
                "role": "user",
                "content": """I’ll give you a spreadsheet with a list of MaEs. Each MaE has an ID, an explanation of the MaE, and 4 examples of the MaE.
                Then I'll show you a student incorrect answer to a math question.
                I want you to tell me how many of the {mae_count} MaEs you can identify in the answers, identify as many as you can.
                  Please process the answer and tell me:
 If the answer is correct
 If the answer is not correct: how many MaEs can you identify? Which ones and why?
 Spreadsheet:
 {mae_spreadsheet_string}
""",
            },
        ],
    },
}
