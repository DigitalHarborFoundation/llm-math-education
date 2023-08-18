intro_prompts = {
    "hint_sequence": {
        "pretty_name": "Hint sequence",
        "messages": [
            {
                "role": "system",
                "content": """You are an expert mathematics tutor who gives useful hints for middle-school students.

The following paragraphs are examples of content that may or not be relevant in helping the student write a hint.
{rori_microlesson_texts}
{openstax_subsection_texts}""",
            },
            {
                "role": "user",
                "content": """I just received this math lesson:
{lesson}

Provide a hint for this math question:
{question}

I answered {incorrect_answer}, which is incorrect. Generate four hints for the correct answer {correct_answer} by following the steps below:

FIRST: Tell me the goal of the problem.

SECOND: Tell me what information I need to accomplish the goal.

THIRD: Tell me what mathematical computation I need to do using the information I have to accomplish the goal.

FOURTH: Tell me how to do the mathematical computation and show that it results in the correct answer "{correct_answer}".""",
            },
        ],
    },
    "slip_correction": {
        "pretty_name": "Slip correction",
        "messages": [
            {
                "role": "system",
                "content": """You are an expert mathematics tutor who gives useful hints for middle-school students.

The following paragraphs are examples of content that may or not be relevant in helping the student write a hint.
{rori_microlesson_texts}
{openstax_subsection_texts}""",
            },
            {
                "role": "user",
                "content": """I just received this math lesson:
{lesson}

Provide a hint for this math question:
{question}

The correct answer is {correct_answer}, but I answered {incorrect_answer}.
I think I made a small slip-up. What did I do wrong?
Your answer should be one sentence and start with "Remember to".""",
            },
        ],
    },
    "misconception": {
        "pretty_name": "Misconception-based hint",
        "messages": [
            {
                "role": "system",
                "content": """""",
            },
        ],
    },
    "comparative_hint": {
        "pretty_name": "Comparative hint",
        "messages": [
            {
                "role": "system",
                "content": """You are an expert mathematics tutor who gives useful hints for middle-school students.

The following paragraphs are examples of content that may or not be relevant in helping the student write a hint.
{rori_microlesson_texts}
{openstax_subsection_texts}""",
            },
            {
                "role": "user",
                "content": """Provide a hint for this math question:
{question}

I answered {incorrect_answer}. I know the correct answer is {correct_answer}, but I need a hint to understand why.

Here's the relevant lesson for this problem:
{lesson}

FIRST: Repeat the worked example from the lesson.

SECOND: Compare my question to the worked example, explaining how it is different.

THIRD: Give me the steps to solve my question correctly, identifying the correct answer as {correct_answer} in the final step.""",
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
