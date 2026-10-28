
QUESTIONS_BY_TYPE = {
    "E-commerce website": [
        "How many products need to be uploaded?",
        "Which payment methods are required (card, PayPal, or cash on delivery)?",
        "What is the shipping and delivery setup?",
        "What features are required in the admin dashboard?",
        "Do you have any preferred designs or reference websites?",
    ],
    "Website": [
        "How many pages are required?",
        "Do you have any preferred designs or reference websites?",
        "Will the client provide the content (text and images), or will the freelancer create it?",
        "Do you already have a domain and hosting?",
    ],
    "Logo / Branding": [
        "What is the business name and industry?",
        "What are your preferred colors and design style?",
        "How many logo concepts are required?",
        "How many revisions should be included?",
        "Which final file formats are required (PNG, SVG, AI)?",
    ],
    "Graphic design": [
        "How many designs are required, and what sizes or formats do you need?",
        "Do you have brand colors and fonts?",
        "How many revisions should be included?",
    ],
    "Content writing": [
        "How many words or articles are required?",
        "What tone should the content have (formal, casual, or friendly)?",
        "Who is the target audience?",
        "Are there any keywords or SEO requirements?",
    ],
    "Video editing": [
        "What should be the final video length?",
        "How much raw footage is available, and in which format?",
        "Which platform is the video intended for (YouTube, Instagram, or TikTok)?",
        "How many revisions should be included?",
    ],
    "Digital marketing": [
        "What is the main campaign goal (sales, leads, or brand awareness)?",
        "Which platforms will be used?",
        "Is there a separate budget for advertising spend?",
        "Which KPIs will be used to measure success?",
    ],
    "Mobile app": [
        "Is the app for Android, iOS, or both?",
        "What is the list of core features?",
        "Does the backend or API already exist?",
        "Has the UI design already been created?",
    ],
    "Unknown": [
        "What is the exact project type?",
        "What are the required final deliverables?",
    ],
}


def detect_missing_info(analysis: dict) -> dict:
    missing = []

    if not analysis.get("budget"):
        missing.append("Budget")
    if not analysis.get("deadline"):
        missing.append("Deadline")
    if not analysis.get("requirements"):
        missing.append("Specific requirements / features")
    if analysis.get("project_type") == "Unknown":
        missing.append("Project type")

    questions = []

    if "Budget" in missing:
        questions.append("What is your budget?")

    if "Deadline" in missing:
        questions.append("When should the project be completed?")

    questions += QUESTIONS_BY_TYPE.get(
        analysis.get("project_type"),
        QUESTIONS_BY_TYPE["Unknown"]
    )

    return {
        "missing_fields": missing,
        "suggested_questions": questions,
    }