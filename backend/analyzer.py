import re

from missing_info import detect_missing_info
from planner import generate_plan

# The order matters: if two types score the same, the first one wins.
PROJECT_TYPES = {
    "E-commerce website": [
        "e-commerce", "ecommerce", "online store", "online shop", "web shop",
        "shopify", "woocommerce", "product catalog",
    ],
    "Mobile app": [
        "mobile app", "android app", "ios app", "app development",
        "flutter", "react native",
    ],
    "Website": [
        "website", "web site", "landing page", "web app", "wordpress",
        "web page", "portfolio site", "wix", "webflow",
    ],
    "Logo / Branding": ["logo", "branding", "brand identity", "brand kit"],
    "Graphic design": [
        "poster", "flyer", "banner", "business card", "social media post",
        "thumbnail", "brochure", "packaging", "infographic", "menu design",
    ],
    "Content writing": [
        "blog", "article", "content writing", "copywriting", "seo content",
        "product description", "newsletter", "ghostwriting",
    ],
    "Video editing": [
        "video editing", "edit my video", "reel", "youtube", "video",
        "animation", "motion graphics", "subtitles", "footage",
    ],
    "Digital marketing": [
        "marketing", "facebook ads", "google ads", "instagram ads", "ads",
        "campaign", "seo", "social media management", "lead generation",
    ],
}

REQUIREMENT_KEYWORDS = {
    "Payment integration": ["payment", "stripe", "paypal", "checkout", "jazzcash", "easypaisa"],
    "User login / signup": ["login", "log in", "signup", "sign up", "authentication", "register", "user accounts"],
    "Admin dashboard": ["admin", "dashboard"],
    "Responsive design": ["responsive", "mobile friendly", "mobile-friendly"],
    "SEO": ["seo"],
    "Contact form": ["contact form"],
    "Logo design": ["logo"],
    "Revisions": ["revision", "revisions"],
    "Multi-language": ["multi-language", "multilingual", "arabic", "urdu version"],
    "Hosting / domain": ["hosting", "domain"],
    "Maintenance": ["maintenance", "ongoing support"],
    "Source files": ["source file", "editable files", "psd"],
    "Animation": ["animation", "motion graphics"],
}

WEEKDAYS = "monday|tuesday|wednesday|thursday|friday|saturday|sunday"


def contains(text: str, keyword: str) -> bool:
    """Whole-word match, so 'ads' does not match 'downloads'. Plurals are allowed."""
    return re.search(rf"\b{re.escape(keyword)}s?\b", text) is not None


def detect_project_type(text: str) -> str:
    text = text.lower()
    scores = {
        project_type: sum(contains(text, k) for k in keywords)
        for project_type, keywords in PROJECT_TYPES.items()
    }
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "Unknown"


def _amount(number: str, k: str | None) -> str:
    value = float(number) * (1000 if k else 1)
    return f"{value:,.0f}" if value == int(value) else f"{value:,.2f}"


def extract_budget(text: str):
    # Turn "1,500" into "1500" so the number is read as one value
    text = re.sub(r"(?<=\d),(?=\d{3}\b)", "", text)

    # 1) Symbol or code first: $300, Rs 5000, PKR 20000, USD 150
    m = re.search(
        r"(\$|€|£|(?<![a-z])(?:rs\.?|pkr|usd))\s?(\d+(?:\.\d+)?)\s?(k)?\b",
        text,
        re.IGNORECASE,
    )
    if m:
        symbol = m.group(1).lower()
        amount = _amount(m.group(2), m.group(3))
        if symbol in ("$", "€", "£"):
            return f"{symbol}{amount}"
        label = {"rs": "Rs", "rs.": "Rs", "pkr": "PKR", "usd": "USD"}[symbol]
        return f"{label} {amount}"

    # 2) Number then unit: 300 dollars, 5000 rupees, 200 usd
    m = re.search(
        r"(?<![\w.])(\d+(?:\.\d+)?)\s?(k)?\s?(usd|dollars?|pkr|rupees?|rs)\b",
        text,
        re.IGNORECASE,
    )
    if m:
        unit = m.group(3).lower()
        label = "USD" if unit in ("usd", "dollar", "dollars") else "PKR" if unit.startswith("pkr") or unit.startswith("rupee") else "Rs"
        return f"{label} {_amount(m.group(1), m.group(2))}"

    # 3) "budget is 300" with no currency (but not "budget ... 10 days")
    m = re.search(
        r"budget[^\d]{0,25}?(\d+(?:\.\d+)?)\s?(k)?\b"
        r"(?!\s*(?:days?|weeks?|months?|hours?|pages?|words?|videos?|posts?|logos?))",
        text,
        re.IGNORECASE,
    )
    if m:
        return _amount(m.group(1), m.group(2))

    return None


def extract_deadline(text: str):
    t = text.lower()

    # "within 10 days", "in 2 weeks", "deadline is 5 days"
    m = re.search(
        r"\b(?:within|in|by|before|under|deadline(?: is| of)?|due in|need it in|ready in)\s+"
        r"(?:about |around |just )?(\d+)\s*(hours?|days?|weeks?|months?)\b",
        t,
    )
    if m:
        return f"{m.group(1)} {m.group(2)}"

    if re.search(r"\b(asap|urgent|urgently|immediately|right away|today|tonight)\b", t):
        return "ASAP (urgent)"
    if re.search(r"\btomorrow\b", t):
        return "1 day (tomorrow)"
    if re.search(r"\bthis week\b", t):
        return "1 week (this week)"
    if re.search(r"\bnext week\b", t):
        return "1 week (next week)"
    if re.search(r"\bend of (?:the )?month\b", t):
        return "End of the month"

    m = re.search(rf"\b(?:by|before|on|until)\s+({WEEKDAYS})\b", t)
    if m:
        return f"By {m.group(1).capitalize()}"

    return None


def extract_requirements(text: str) -> list:
    text = text.lower()
    return [
        requirement
        for requirement, keywords in REQUIREMENT_KEYWORDS.items()
        if any(contains(text, k) for k in keywords)
    ]


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