from django.core.management.base import BaseCommand

from agenticbrainrot.surveys.models import SurveyQuestion

PROFILE_QUESTIONS = [
    # === Demographics ===
    {
        "text": "What is your age range?",
        "question_type": "single_choice",
        "choices": [
            ["18-24", "18-24"],
            ["25-34", "25-34"],
            ["35-44", "35-44"],
            ["45-54", "45-54"],
            ["55-64", "55-64"],
            ["65+", "65+"],
        ],
        "context": "profile",
        "category": "Demographics",
        "is_required": True,
        "display_order": 1,
    },
    {
        "text": "What is your highest level of education?",
        "question_type": "single_choice",
        "choices": [
            ["secondary", "Secondary school / GCSE"],
            ["sixth_form", "Sixth form / A-levels"],
            ["undergraduate", "Undergraduate degree"],
            ["postgraduate", "Postgraduate degree"],
            ["doctorate", "Doctorate"],
            ["other", "Other"],
        ],
        "context": "profile",
        "category": "Demographics",
        "is_required": True,
        "display_order": 2,
    },
    {
        "text": "What is your current occupation or role?",
        "question_type": "text",
        "context": "profile",
        "category": "Demographics",
        "is_required": True,
        "display_order": 3,
    },
    {
        "text": "What country are you based in?",
        "question_type": "text",
        "context": "profile",
        "category": "Demographics",
        "is_required": True,
        "display_order": 4,
    },
    # === Programming Experience ===
    {
        "text": "How many years of programming experience do you have?",
        "question_type": "single_choice",
        "choices": [
            ["<1", "Less than 1 year"],
            ["1-3", "1-3 years"],
            ["3-5", "3-5 years"],
            ["5-10", "5-10 years"],
            ["10+", "10+ years"],
        ],
        "context": "profile",
        "category": "Programming Experience",
        "is_required": True,
        "display_order": 10,
    },
    {
        "text": "Which programming languages do you use regularly?",
        "question_type": "multi_choice",
        "choices": [
            ["python", "Python"],
            ["javascript", "JavaScript/TypeScript"],
            ["java", "Java"],
            ["csharp", "C#"],
            ["cpp", "C/C++"],
            ["go", "Go"],
            ["rust", "Rust"],
            ["ruby", "Ruby"],
            ["php", "PHP"],
            ["other", "Other"],
        ],
        "context": "profile",
        "category": "Programming Experience",
        "is_required": True,
        "display_order": 11,
    },
    {
        "text": "How would you rate your Python proficiency?",
        "question_type": "single_choice",
        "choices": [
            ["beginner", "Beginner"],
            ["somewhat_beginner", "Somewhat beginner"],
            ["intermediate", "Intermediate"],
            ["advanced", "Advanced"],
            ["expert", "Expert"],
        ],
        "context": "profile",
        "category": "Programming Experience",
        "is_required": True,
        "display_order": 12,
    },
    {
        "text": "What is your primary programming context?",
        "question_type": "single_choice",
        "choices": [
            ["professional", "Professional / work"],
            ["academic", "Academic / research"],
            ["hobby", "Hobby / personal projects"],
            ["student", "Student"],
            ["other", "Other"],
        ],
        "context": "profile",
        "category": "Programming Experience",
        "is_required": True,
        "display_order": 13,
    },
    {
        "text": "How often do you write code?",
        "question_type": "single_choice",
        "choices": [
            ["daily", "Daily"],
            ["few_per_week", "A few times a week"],
            ["weekly", "Weekly"],
            ["few_per_month", "A few times a month"],
            ["rarely", "Rarely"],
        ],
        "context": "profile",
        "category": "Programming Experience",
        "is_required": True,
        "display_order": 14,
    },
    # === AI Tool Usage ===
    {
        "text": "Do you currently use AI coding assistants?",
        "question_type": "single_choice",
        "choices": [
            ["yes_regularly", "Yes, regularly"],
            ["yes_occasionally", "Yes, occasionally"],
            ["tried_stopped", "I've tried them but stopped"],
            ["never", "No, never"],
        ],
        "context": "profile",
        "category": "AI Tool Usage",
        "is_required": True,
        "display_order": 20,
    },
    {
        "text": "Which AI coding tools have you used?",
        "question_type": "multi_choice",
        "choices": [
            ["github_copilot", "GitHub Copilot"],
            ["chatgpt", "ChatGPT"],
            ["claude", "Claude"],
            ["cursor", "Cursor"],
            ["codewhisperer", "Amazon CodeWhisperer"],
            ["tabnine", "Tabnine"],
            ["gemini", "Gemini"],
            ["other", "Other"],
            ["none", "None"],
        ],
        "context": "profile",
        "category": "AI Tool Usage",
        "is_required": False,
        "display_order": 21,
    },
    {
        "text": "How long have you been using AI coding tools?",
        "question_type": "single_choice",
        "choices": [
            ["<3months", "Less than 3 months"],
            ["3-6months", "3-6 months"],
            ["6-12months", "6-12 months"],
            ["1-2years", "1-2 years"],
            ["2+years", "2+ years"],
            ["na", "Not applicable"],
        ],
        "context": "profile",
        "category": "AI Tool Usage",
        "is_required": True,
        "display_order": 22,
    },
    {
        "text": "What do you primarily use AI coding tools for?",
        "question_type": "multi_choice",
        "choices": [
            ["code_completion", "Code completion / autocomplete"],
            ["code_generation", "Generating code from descriptions"],
            ["debugging", "Debugging / error fixing"],
            ["code_review", "Code review / suggestions"],
            ["documentation", "Writing documentation"],
            ["learning", "Learning new concepts"],
            ["refactoring", "Refactoring"],
            ["other", "Other"],
        ],
        "context": "profile",
        "category": "AI Tool Usage",
        "is_required": False,
        "display_order": 23,
    },
    {
        "text": ("How much do you rely on AI tools when coding?"),
        "question_type": "single_choice",
        "choices": [
            ["not_at_all", "Not at all"],
            ["slightly", "Slightly"],
            ["moderately", "Moderately"],
            ["very", "Very"],
            ["heavily", "Heavily"],
        ],
        "context": "profile",
        "category": "AI Tool Usage",
        "is_required": True,
        "display_order": 24,
    },
    # === Problem Solving ===
    {
        "text": ("When stuck on a coding problem, what do you typically do first?"),
        "question_type": "single_choice",
        "choices": [
            ["search_docs", "Search documentation"],
            ["search_web", "Search the web (Stack Overflow, etc.)"],
            ["ask_ai", "Ask an AI assistant"],
            ["ask_colleague", "Ask a colleague"],
            ["trial_error", "Trial and error"],
            ["step_away", "Step away and think"],
        ],
        "context": "profile",
        "category": "Problem Solving",
        "is_required": True,
        "display_order": 30,
    },
    {
        "text": (
            "How confident are you in solving programming " "problems without any external help?"
        ),
        "question_type": "single_choice",
        "choices": [
            ["not_at_all_confident", "Not at all confident"],
            ["not_confident", "Not confident"],
            ["neutral", "Neutral / undecided"],
            ["confident", "Confident"],
            ["very_confident", "Very confident"],
        ],
        "context": "profile",
        "category": "Problem Solving",
        "is_required": True,
        "display_order": 31,
    },
    {
        "text": (
            "How often do you review and understand AI-generated code " "before using it?"
        ),
        "question_type": "single_choice",
        "choices": [
            ["always", "Always"],
            ["usually", "Usually"],
            ["sometimes", "Sometimes"],
            ["rarely", "Rarely"],
            ["never", "Never"],
            ["na", "I don't use AI tools"],
        ],
        "context": "profile",
        "category": "Problem Solving",
        "is_required": True,
        "display_order": 32,
    },
    # === Study Motivation ===
    {
        "text": "Why are you participating in this study?",
        "question_type": "multi_choice",
        "choices": [
            ["curiosity", "Curiosity about my coding skills"],
            ["improve", "Want to improve my coding"],
            ["ai_impact", "Interested in AI's impact on coding"],
            ["research", "Supporting academic research"],
            ["track_progress", "Want to track my progress over time"],
            ["other", "Other"],
        ],
        "context": "profile",
        "category": "Study Motivation",
        "is_required": True,
        "display_order": 40,
    },
    {
        "text": (
            "Do you believe that heavy use of AI coding tools " "could negatively affect programming skills?"
        ),
        "question_type": "single_choice",
        "choices": [
            ["strongly_disagree", "Strongly disagree"],
            ["disagree", "Disagree"],
            ["neutral", "Neutral / undecided"],
            ["agree", "Agree"],
            ["strongly_agree", "Strongly agree"],
        ],
        "context": "profile",
        "category": "Study Motivation",
        "is_required": True,
        "display_order": 41,
    },
    # === Coding Habits ===
    {
        "text": "How do you typically test your code?",
        "question_type": "multi_choice",
        "choices": [
            ["unit_tests", "Write unit tests"],
            ["manual", "Manual testing"],
            ["debugger", "Use a debugger"],
            ["print", "Print statements"],
            ["ai_review", "Ask AI to review"],
            ["no_testing", "I don't usually test"],
        ],
        "context": "profile",
        "category": "Coding Habits",
        "is_required": True,
        "display_order": 50,
    },
    {
        "text": (
            "When writing code, how often do you plan your " "approach before starting to type?"
        ),
        "question_type": "single_choice",
        "choices": [
            ["always", "Always"],
            ["usually", "Usually"],
            ["sometimes", "Sometimes"],
            ["rarely", "Rarely"],
            ["never", "Never"],
        ],
        "context": "profile",
        "category": "Coding Habits",
        "is_required": True,
        "display_order": 51,
    },
    {
        "text": "What editor or IDE do you primarily use?",
        "question_type": "single_choice",
        "choices": [
            ["vscode", "VS Code"],
            ["pycharm", "PyCharm / IntelliJ"],
            ["vim", "Vim / Neovim"],
            ["emacs", "Emacs"],
            ["sublime", "Sublime Text"],
            ["cursor", "Cursor"],
            ["other", "Other"],
        ],
        "context": "profile",
        "category": "Coding Habits",
        "is_required": True,
        "display_order": 52,
    },
    {
        "text": (
            "How comfortable are you reading and understanding " "code written by others?"),
        "question_type": "single_choice",
        "choices": [
            ["not_at_all_comfortable", "Not at all comfortable"],
            ["not_comfortable", "Not comfortable"],
            ["undecided", "Undecided"],
            ["comfortable", "Comfortable"],
            ["very_comfortable", "Very comfortable"],
        ],
        "context": "profile",
        "category": "Coding Habits",
        "is_required": True,
        "display_order": 53,
    },
    {
        "text": "How comfortable are you with debugging code?",
        "question_type": "single_choice",
        "choices": [
            ["not_at_all_comfortable", "Not at all comfortable"],
            ["not_comfortable", "Not comfortable"],
            ["undecided", "Undecided"],
            ["comfortable", "Comfortable"],
            ["very_comfortable", "Very comfortable"],
        ],
        "context": "profile",
        "category": "Coding Habits",
        "is_required": True,
        "display_order": 54,
    },
]


POST_CHALLENGE_QUESTIONS = [
    {
        "text": "How difficult did you find this challenge?",
        "question_type": "single_choice",
        "choices": [
            ["very_easy", "Very easy"],
            ["easy", "Easy"],
            ["moderate", "Moderate"],
            ["difficult", "Difficult"],
            ["very_difficult", "Very difficult"],
        ],
        "context": "post_challenge",
        "category": "Challenge Reflection",
        "is_required": True,
        "display_order": 1,
    },
    {
        "text": "How confident are you in your solution?",
        "question_type": "single_choice",
        "choices": [
            ["not_at_all_confident", "Not at all confident"],
            ["not_confident", "Not confident"],
            ["neutral", "Neutral / undecided"],
            ["confident", "Confident"],
            ["very_confident", "Very confident"],
        ],
        "context": "post_challenge",
        "category": "Challenge Reflection",
        "is_required": True,
        "display_order": 2,
    },
]

POST_SESSION_QUESTIONS = [
    {
        "text": ("Since your last session, has your use of AI coding " "tools changed?"),
        "question_type": "single_choice",
        "choices": [
            ["increased", "Increased"],
            ["same", "Stayed the same"],
            ["decreased", "Decreased"],
            ["stopped", "Stopped using them"],
            ["started", "Started using them"],
            ["na", "Not applicable"],
        ],
        "context": "post_session",
        "category": "Session Habits",
        "is_required": True,
        "display_order": 1,
    },
    {
        "text": ("How would you rate your overall coding confidence " "right now?"),
        "question_type": "single_choice",
        "choices": [
            ["very_low", "Very low"],
            ["low", "Low"],
            ["moderate", "Moderate"],
            ["high", "High"],
            ["very_high", "Very high"],
        ],
        "context": "post_session",
        "category": "Session Habits",
        "is_required": True,
        "display_order": 2,
    },
    {
        "text": ("How did you find the difficulty of the challenges " "in this session overall?"),
        "question_type": "single_choice",
        "choices": [
            ["much_too_easy", "Much too easy"],
            ["too_easy", "Too easy"],
            ["about_right", "About right"],
            ["too_difficult", "Too difficult"],
            ["much_too_difficult", "Much too difficult"],
        ],
        "context": "post_session",
        "category": "Session Habits",
        "is_required": True,
        "display_order": 3,
    },
    {
        "text": "How much do you trust code generated by AI?",
        "question_type": "scale",
        "scale_min": 1,
        "scale_max": 5,
        "min_label": "Not at all",
        "mid_label": "Undecided",
        "max_label": "Very much so",
        "choices": [
            ["1", "Not at all"],
            ["2", "Not really"],
            ["3", "Undecided"],
            ["4", "Somewhat"],
            ["5", "Very much so"],
        ],
        "context": "post_session",
        "category": "AI Trust",
        "is_required": True,
        "display_order": 4,
    },
    {
        "text": (
            "Can you estimate what percentage of the code you "
            "generate with AI you check over?"
        ),
        "question_type": "number",
        "context": "post_session",
        "category": "AI Trust",
        "is_required": True,
        "display_order": 5,
    },
    {
        "text": "Any comments about this session?",
        "question_type": "text",
        "context": "post_session",
        "category": "Session Habits",
        "is_required": False,
        "display_order": 6,
    },
]


class Command(BaseCommand):
    help = "Seed default survey questions (idempotent)."

    def handle(self, *args, **options):
        all_questions = PROFILE_QUESTIONS + POST_CHALLENGE_QUESTIONS + POST_SESSION_QUESTIONS
        created_count = 0
        skipped_count = 0

        for q_data in all_questions:
            defaults = {
                "question_type": q_data["question_type"],
                "choices": q_data.get("choices", []),
                "scale_min": q_data.get("scale_min"),
                "scale_max": q_data.get("scale_max"),
                "min_label": q_data.get("min_label", ""),
                "max_label": q_data.get("max_label", ""),
                "mid_label": q_data.get("mid_label", ""),
                "category": q_data.get("category", ""),
                "is_required": q_data.get("is_required", True),
                "is_active": True,
            }
            _, created = SurveyQuestion.objects.get_or_create(
                text=q_data["text"],
                context=q_data["context"],
                display_order=q_data["display_order"],
                defaults=defaults,
            )
            if created:
                created_count += 1
            else:
                skipped_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. Created: {created_count}, " f"Skipped (already exist): {skipped_count}",
            ),
        )
