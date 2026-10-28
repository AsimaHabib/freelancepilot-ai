# 
import re
from missing_info import detect_missing_info
from planner import generate_plan
PROJECT_TYPES = {
    "E-commerce website": ["e-commerce", "ecommerce", "online store", "online shop", "shopify", "woocommerce"],
    "Website": ["website", "web site", "landing page", "web app", "wordpress"],
    "Logo / Branding": ["logo", "branding", "brand identity"],
    "Graphic design": ["poster", "flyer", "banner", "business card", "social media post", "thumbnail"],
    "Content writing": ["blog", "article", "content writing", "copywriting", "seo content"],
    "Video editing": ["video", "reel", "youtube", "editing", "animation"],
    "Digital marketing": ["marketing", "ads", "facebook ads", "google ads", "campaign", "seo"],
    "Mobile app": ["mobile app", "android app", "ios app", "app development"],
}

REQUIREMENT_KEYWORDS = {
    "Payment integration": ["payment", "stripe", "paypal", "checkout"],
    "User login / signup": ["login", "signup", "sign up", "authentication", "register"],
    "Admin dashboard": ["admin", "dashboard"],
    "Responsive design": ["responsive", "mobile friendly", "mobile-friendly"],
    "SEO": ["seo"],
    "Contact form": ["contact form"],
    "Logo design": ["logo"],
    "Revisions": ["revision", "revisions"],
}


def detect_project_type(text: str) -> str:
    text = text.lower()
    for project_type, keywords in PROJECT_TYPES.items():
        if any(k in text for k in keywords):
            return project_type
    return "Unknown"


def extract_budget(text: str):
    patterns = [
        r"(?:budget|pay|paying|offer)[^\d$€£]{0,20}([$€£]?\s?\d[\d,]*(?:\.\d+)?)\s?(usd|dollars|\$)?",
        r"([$€£]\s?\d[\d,]*(?:\.\d+)?)",
        r"(\d[\d,]*(?:\.\d+)?)\s?(?:usd|dollars)",
    ]
    for p in patterns:
        match = re.search(p, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


def extract_deadline(text: str):
    match = re.search(
        r"(?:within|in|by|before)\s+(\d+)\s*(day|days|week|weeks|month|months|hour|hours)",
        text,
        re.IGNORECASE,
    )
    if match:
        return f"{match.group(1)} {match.group(2)}"
    if re.search(r"\b(asap|urgent|urgently|immediately)\b", text, re.IGNORECASE):
        return "ASAP (urgent)"
    return None


def extract_requirements(text: str) -> list:
    text = text.lower()
    found = []
    for requirement, keywords in REQUIREMENT_KEYWORDS.items():
        if any(k in text for k in keywords):
            found.append(requirement)
    return found


def analyze_message(message: str) -> dict:
    return {
        "project_type": detect_project_type(message),
        "budget": extract_budget(message),
        "deadline": extract_deadline(message),
        "requirements": extract_requirements(message),
    }

def analyze_message(message: str) -> dict:
    analysis = {
        "project_type": detect_project_type(message),
        "budget": extract_budget(message),
        "deadline": extract_deadline(message),
        "requirements": extract_requirements(message),
    }
    analysis.update(detect_missing_info(analysis))
    analysis["plan"] = generate_plan(analysis)
    return analysis