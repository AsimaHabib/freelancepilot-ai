
import re

TASKS_BY_TYPE = {
    "E-commerce website": {
        "tasks": [
            "Finalize requirements and collect design references",
            "Design the website (homepage, product page, cart, and checkout)",
            "Develop the frontend",
            "Set up the backend and product management system",
            "Integrate the payment gateway",
            "Perform testing (mobile devices, browsers, and payment flow)",
            "Conduct client review, apply revisions, and launch the website",
        ],
        "deliverables": [
            "Live e-commerce website",
            "Admin access",
            "Basic user guide",
        ],
    },
    "Website": {
        "tasks": [
            "Finalize requirements and sitemap",
            "Create design mockups",
            "Develop the website",
            "Add content",
            "Perform testing and check responsiveness",
            "Conduct client review and launch the website",
        ],
        "deliverables": [
            "Live website",
            "Source files / access",
        ],
    },
    "Logo / Branding": {
        "tasks": [
            "Prepare the brand brief and conduct research",
            "Create initial logo concepts",
            "Collect client feedback and make revisions",
            "Prepare the final logo",
            "Export the final files",
        ],
        "deliverables": [
            "Final logo",
            "PNG, SVG, and source files",
        ],
    },
    "Graphic design": {
        "tasks": [
            "Collect the design brief",
            "Create draft designs",
            "Collect client feedback and make revisions",
            "Export the final files",
        ],
        "deliverables": [
            "Final designs in the required formats",
        ],
    },
    "Content writing": {
        "tasks": [
            "Collect the content brief and keywords",
            "Conduct research and prepare an outline",
            "Write the first draft",
            "Edit and proofread the content",
            "Collect client feedback and make revisions",
        ],
        "deliverables": [
            "Final articles / content",
            "Delivery according to the required word count",
        ],
    },
    "Video editing": {
        "tasks": [
            "Receive and review the raw footage",
            "Create a rough cut",
            "Apply color correction, audio adjustments, music, and effects",
            "Collect client feedback and make revisions",
            "Export the final video",
        ],
        "deliverables": [
            "Final video in the required format",
        ],
    },
    "Digital marketing": {
        "tasks": [
            "Define goals and target audience",
            "Develop a strategy and content plan",
            "Create ad creatives and social media posts",
            "Launch the campaign",
            "Track performance and prepare a report",
        ],
        "deliverables": [
            "Campaign setup",
            "Performance report",
        ],
    },
    "Mobile app": {
        "tasks": [
            "Finalize the feature list and requirements",
            "Design the UI/UX",
            "Develop the mobile application",
            "Integrate the backend / API",
            "Test the application",
            "Submit the app to the store and launch it",
        ],
        "deliverables": [
            "Working mobile application",
            "Source code",
            "App store submission support",
        ],
    },
    "Unknown": {
        "tasks": [
            "Clarify project details with the client",
            "Finalize the project scope and deliverables",
        ],
        "deliverables": [
            "To be defined after clarification",
        ],
    },
}


def _to_days(deadline):
    """Convert deadline text into days (e.g., '2 weeks' -> 14)."""
    if not deadline:
        return None

    match = re.match(r"(\d+)\s*(hour|day|week|month)", deadline.lower())

    if not match:
        return None

    number, unit = int(match.group(1)), match.group(2)

    if unit == "hour":
        return max(1, number // 24)

    return number * {"day": 1, "week": 7, "month": 30}[unit]


def _to_amount(budget):
    if not budget:
        return None

    digits = re.sub(r"[^\d.]", "", budget)

    try:
        return float(digits)
    except ValueError:
        return None


def detect_risks(analysis: dict) -> list:
    risks = []

    project_type = analysis.get("project_type")
    requirements = analysis.get("requirements", [])

    days = _to_days(analysis.get("deadline"))
    amount = _to_amount(analysis.get("budget"))

    if not analysis.get("budget"):
        risks.append(
            "The budget is not defined, which may cause confusion during pricing."
        )

    if not analysis.get("deadline"):
        risks.append(
            "The deadline is not defined, which may lead to mismatched expectations."
        )

    if analysis.get("deadline") == "ASAP (urgent)":
        risks.append(
            "The deadline is marked as ASAP. Agree on a realistic completion date first."
        )

    if (
        days is not None
        and days <= 7
        and project_type in (
            "E-commerce website",
            "Website",
            "Mobile app",
        )
    ):
        risks.append(
            "The deadline is short for this type of project, so the timeline may be tight."
        )

    if "Payment integration" in requirements:
        risks.append(
            "Payment integration may require additional time for testing and gateway approval."
        )

    if (
        amount is not None
        and project_type == "E-commerce website"
        and amount < 500
    ):
        risks.append(
            "The budget may be too low for this scope. Clearly define and limit the project scope."
        )

    if not requirements:
        risks.append(
            "The requirements are unclear, which creates a risk of scope creep."
        )

    if "Revisions" not in requirements:
        risks.append(
            "Revision limits are not specified. Clearly include them in the agreement."
        )

    return risks


def generate_plan(analysis: dict) -> dict:
    project_type = analysis.get("project_type", "Unknown")

    template = TASKS_BY_TYPE.get(
        project_type,
        TASKS_BY_TYPE["Unknown"],
    )

    return {
        "tasks": template["tasks"],
        "deliverables": template["deliverables"],
        "risks": detect_risks(analysis),
        "note": "These are initial suggestions, not guaranteed outcomes.",
    }