"""Rule-based proposal builder. Works without AI; AI can then write a nicer version."""
from analyzer import analyze_message


def build_milestones(tasks: list) -> list:
    if not tasks:
        return []
    groups = min(3, len(tasks))
    size = -(-len(tasks) // groups)  # round up
    chunks = [tasks[i : i + size] for i in range(0, len(tasks), size)]
    return [{"title": f"Milestone {i + 1}", "tasks": chunk} for i, chunk in enumerate(chunks)]


def _bullets(items: list) -> str:
    return "\n".join(f"- {item}" for item in items)


def build_draft(name: str, skills: str, analysis: dict, milestones: list) -> str:
    project_type = analysis.get("project_type", "Unknown")
    what = "your project" if project_type == "Unknown" else f"your {project_type.lower()} project"
    plan = analysis.get("plan", {})

    parts = ["Hi,", ""]
    parts.append(f"Thank you for sharing the details of {what}.")

    requirements = analysis.get("requirements") or []
    if requirements:
        parts.append(f"I noted these requirements: {', '.join(requirements)}.")

    if analysis.get("deadline"):
        parts.append(f"I understand you need it in this timeframe: {analysis['deadline']}.")
    if analysis.get("budget"):
        parts.append(
            f"I have also noted your budget ({analysis['budget']}). I will keep the plan within it, "
            "or tell you early if the scope needs adjusting."
        )

    if milestones:
        parts += ["", "Here is how I would approach it:"]
        for m in milestones:
            parts.append(f"{m['title']}: " + "; ".join(m["tasks"]))

    deliverables = plan.get("deliverables") or []
    if deliverables:
        parts += ["", "What you will receive:", _bullets(deliverables)]

    questions = (analysis.get("suggested_questions") or [])[:4]
    if questions:
        parts += ["", "Before I confirm a final quote and timeline, a few quick questions:", _bullets(questions)]

    if skills.strip():
        parts += ["", f"About me: {skills.strip()}"]

    parts += ["", "I look forward to hearing from you.", "", "Best regards,", name.strip() or "[Your name]"]
    return "\n".join(parts)


def build_proposal(message: str, name: str, skills: str) -> dict:
    analysis = analyze_message(message)
    plan = analysis.get("plan", {})
    milestones = build_milestones(plan.get("tasks") or [])
    return {
        "project_type": analysis.get("project_type"),
        "budget": analysis.get("budget"),
        "deadline": analysis.get("deadline"),
        "requirements": analysis.get("requirements", []),
        "milestones": milestones,
        "draft": build_draft(name, skills, analysis, milestones),
        "note": "This is a starting draft. Read it, add your own details and adjust before you send it.",
        "_analysis": analysis,  # used by the AI step, removed before returning
    }