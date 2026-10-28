import re

DELIVERABLE_KEYWORDS = {
    "Logo": ["logo"],
    "Social media posts": ["social media", "instagram", "facebook post", "post design", "posts"],
    "Business cards": ["business card", "visiting card"],
    "Letterhead / stationery": ["letterhead", "stationery", "envelope"],
    "Brochure / flyer": ["brochure", "flyer", "leaflet", "pamphlet"],
    "Poster / banner": ["poster", "banner", "billboard"],
    "Brand guidelines": ["brand guide", "brand guidelines", "style guide"],
    "Website pages": ["website", "web page", "landing page", "pages"],
    "Payment integration": ["payment", "stripe", "paypal", "checkout"],
    "Admin dashboard": ["admin", "dashboard"],
    "User login": ["login", "signup", "sign up", "authentication"],
    "SEO": ["seo"],
    "Blog / articles": ["blog", "article", "content writing"],
    "Video editing": ["video", "reel", "youtube"],
    "Animation": ["animation", "motion graphics"],
    "Mobile app": ["mobile app", "android app", "ios app"],
    "Hosting / domain setup": ["hosting", "domain"],
    "Maintenance / support": ["maintenance", "support", "updates after"],
}

REVISION_SIGNALS = [
    "revision", "revisions", "change again", "one more change",
    "redo", "redesign", "start over", "different version",
]


def find_deliverables(text: str) -> set:
    text = text.lower()
    return {
        name
        for name, keywords in DELIVERABLE_KEYWORDS.items()
        if any(k in text for k in keywords)
    }


def find_revision_limit(text: str):
    match = re.search(r"(\d+)\s*(?:rounds?\s+of\s+)?revisions?", text, re.IGNORECASE)
    return int(match.group(1)) if match else None


def build_reply(verdict: str, out_of_scope: list, revision_note: bool) -> str:
    if verdict == "In scope":
        return (
            "Thanks for your message! This is covered in our original agreement, "
            "so I will get started on it right away."
        )

    if verdict == "Unclear":
        return (
            "Thanks for your message! Could you share a few more details about "
            "what you need? Once I understand it, I can confirm whether it fits "
            "our current agreement."
        )

    items = ", ".join(out_of_scope)
    return (
        f"Thanks for your message! The following items were not part of our original "
        f"agreement: {items}. I would be happy to help with them as an additional "
        f"service. I can send you a quick quote and timeline for the extra work. "
        f"Meanwhile, I will continue with the agreed scope."
    )


def check_scope(agreement: str, new_request: str) -> dict:
    agreed = find_deliverables(agreement)
    requested = find_deliverables(new_request)

    in_scope = sorted(requested & agreed)
    out_of_scope = sorted(requested - agreed)

    # Revision check
    request_lower = new_request.lower()
    asks_revision = any(s in request_lower for s in REVISION_SIGNALS)
    limit = find_revision_limit(agreement)
    revision_note = None
    if asks_revision:
        if limit is not None:
            revision_note = (
                f"Client is asking for changes. Your agreement includes {limit} revision(s). "
                f"Check how many have already been used."
            )
        else:
            revision_note = (
                "Client is asking for changes, but your agreement has no revision limit. "
                "Add one to future agreements."
            )

    # Verdict
    if not requested:
        verdict = "Unclear"
        explanation = "No specific deliverable was detected in the new request."
    elif not out_of_scope:
        verdict = "In scope"
        explanation = "Everything requested appears in the original agreement."
    elif not in_scope:
        verdict = "Out of scope"
        explanation = "None of the requested items appear in the original agreement."
    else:
        verdict = "Partially out of scope"
        explanation = "Some requested items are in the agreement, but others are not."

    return {
        "verdict": verdict,
        "explanation": explanation,
        "agreed_deliverables": sorted(agreed),
        "requested_deliverables": sorted(requested),
        "in_scope": in_scope,
        "out_of_scope": out_of_scope,
        "revision_note": revision_note,
        "suggested_reply": build_reply(verdict, out_of_scope, bool(revision_note)),
        "note": "This is an automated suggestion. Always check your actual agreement.",
    }