from django.core.management.base import BaseCommand

from agenticbrainrot.surveys.models import SurveyQuestion
from agenticbrainrot.surveys.models import SurveyResponse

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
        "text": "What country are you based in?",
        "question_type": "text",
        "context": "profile",
        "category": "Demographics",
        "is_required": True,
        "display_order": 4,
    },
    {
        "text": "Is your educational background in computer science or a related field?",
        "question_type": "single_choice",
        "choices": [
            ["yes", "Yes"],
            ["no_stem", "No – different science or engineering field"],
            ["no_non_stem", "No – unrelated field"],
        ],
        "context": "profile",
        "category": "Demographics",
        "is_required": True,
        "display_order": 5,
    },
    # === Programming Experience ===
    {
        "text": "How many years of programming experience do you have?",
        "question_type": "number",
        "scale_min": 0,
        "scale_max": 60,
        "context": "profile",
        "category": "Programming Experience",
        "is_required": True,
        "display_order": 10,
    },
    {
        "text": "How many years have you been writing Python specifically?",
        "question_type": "number",
        "scale_min": 0,
        "scale_max": 60,
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
        "text": "Approximately how many hours per week do you spend writing code?",
        "question_type": "number",
        "context": "profile",
        "category": "Programming Experience",
        "is_required": True,
        "display_order": 15,
    },
    # === AI Tool Usage ===
    {
        "text": "How long have you been using AI coding tools?",
        "question_type": "single_choice",
        "choices": [
            ["<3months", "Less than 3 months"],
            ["3-6months", "3-6 months"],
            ["6-12months", "6-12 months"],
            ["1-2years", "1-2 years"],
            ["2+years", "2+ years"],
            ["tried_stopped", "I used to but stopped"],
            ["never", "Never"],
        ],
        "context": "profile",
        "category": "AI Tool Usage",
        "is_required": True,
        "display_order": 20,
    },
    {
        "text": "In a typical coding session, roughly what percentage of your final code is AI-generated? (0–100)",
        "question_type": "number",
        "scale_min": 0,
        "scale_max": 100,
        "min_label": "0% (I write everything myself)",
        "max_label": "100% (all AI-generated)",
        "context": "profile",
        "category": "AI Tool Usage",
        "is_required": True,
        "display_order": 25,
    },
    # === Problem Solving ===
    {
        "text": ("How often do you review and understand AI-generated code before using it?"),
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
        "category": "AI Tool Usage",
        "is_required": True,
        "display_order": 32,
    },
    # === Study Motivation ===
    {
        "text": ("Do you believe that heavy use of AI coding tools could negatively affect programming skills?"),
        "question_type": "single_choice",
        "choices": [
            ["strongly_disagree", "Strongly disagree"],
            ["disagree", "Disagree"],
            ["neutral", "Neutral / undecided"],
            ["agree", "Agree"],
            ["strongly_agree", "Strongly agree"],
        ],
        "context": "profile",
        "category": "AI Tool Usage",
        "is_required": True,
        "display_order": 41,
    },
    # === Coding Habits ===
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
            ["very_confident", "Very confident"],
            ["confident", "Confident"],
            ["neutral", "Neutral / undecided"],
            ["not_confident", "Not confident"],
            ["not_at_all_confident", "Not at all confident"],
        ],
        "context": "post_challenge",
        "category": "Challenge Reflection",
        "is_required": True,
        "display_order": 2,
    },
    {
        "text": "Did you look anything up to complete this challenge?",
        "question_type": "single_choice",
        "choices": [
            ["no_help", "No – solved from memory alone"],
            ["checked_docs", "Yes – checked documentation or syntax reference"],
            ["searched_web", "Yes – searched the web (Google, Stack Overflow, etc.)"],
            ["used_ai", "Yes – used an AI tool (ChatGPT, Copilot, Claude, etc.)"],
            ["multiple", "Yes – a mix of the above"],
        ],
        "context": "post_challenge",
        "category": "Challenge Reflection",
        "is_required": True,
        "display_order": 3,
    },
    {
        "text": "Do you think your recent use of AI coding tools affected how easy you found this challenge?",
        "question_type": "single_choice",
        "choices": [
            ["harder", "Yes – harder (I'm more reliant on AI than I realised)"],
            ["no_difference", "No noticeable effect"],
            ["unsure", "Unsure"],
            ["easier", "Yes – easier (AI use has sharpened my skills)"],
            ["no_ai", "I don't regularly use AI tools"],
        ],
        "context": "post_challenge",
        "category": "Challenge Reflection",
        "is_required": True,
        "display_order": 4,
    },
]

POST_SESSION_QUESTIONS = [
    {
        "text": "In the past month, roughly what percentage of the code you wrote was AI-generated? (Enter 0 if you wrote everything yourself.)",
        "question_type": "number",
        "context": "post_session",
        "category": "Session Habits",
        "is_required": True,
        "display_order": 1,
    },
    {
        "text": ("How would you rate your overall coding confidence right now?"),
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
        "text": ("How did you find the difficulty of the challenges in this session overall?"),
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
        "text": ("Can you estimate what percentage of the code you generate with AI you check over?"),
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
    {
        "text": (
            "Do you ever deliberately code without AI assistance, even when AI tools are available to you?"
        ),
        "question_type": "single_choice",
        "choices": [
            ["never", "No – I use AI whenever it is available"],
            ["rarely", "Rarely (less than once a month)"],
            ["sometimes", "Sometimes (once or twice a month)"],
            ["often", "Often (most weeks)"],
            ["always", "Always – I maintain a regular AI-free coding practice"],
        ],
        "context": "post_session",
        "category": "Protective Behaviours",
        "is_required": True,
        "display_order": 7,
    },
    {
        "text": (
            "Roughly what percentage of your coding time do you keep deliberately AI-free by choice? "
            "(Enter 0 if you do not deliberately code without AI.)"
        ),
        "question_type": "number",
        "context": "post_session",
        "category": "Protective Behaviours",
        "is_required": True,
        "display_order": 8,
    },
    {
        "text": (
            "Are you taking any specific steps to maintain or protect your coding skills alongside your use of AI tools? "
            "If so, please describe what you do. (e.g. personal projects without AI, code katas, reading others' code, teaching, competitive programming, etc.)"
        ),
        "question_type": "textarea",
        "context": "post_session",
        "category": "Protective Behaviours",
        "is_required": False,
        "display_order": 9,
    },
]


class Command(BaseCommand):
    help = "Seed default survey questions (idempotent)."

    def handle(self, *args, **options):
        all_questions = PROFILE_QUESTIONS + POST_CHALLENGE_QUESTIONS + POST_SESSION_QUESTIONS
        created_count = 0
        skipped_count = 0
        known_texts = {q["text"] for q in all_questions}

        stale_qs = SurveyQuestion.objects.exclude(text__in=known_texts)
        SurveyResponse.objects.filter(question__in=stale_qs).delete()
        deleted, _ = stale_qs.delete()

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
                f"Done. Created: {created_count}, Skipped (already exist): {skipped_count}, Deleted: {deleted}",
            ),
        )
