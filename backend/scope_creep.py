import re

NUMBER_WORDS = {
    "a": 1, "an": 1, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
}

DELIVERABLE_KEYWORDS = {
    "Logo": ["logo"],
    "Social media posts": ["social media", "instagram post", "facebook post", "post design"],
    "Business cards": ["business card", "visiting card"],
    "Letterhead / stationery": ["letterhead", "stationery", "envelope"],
    "Brochure / flyer": ["brochure", "flyer", "leaflet", "pamphlet"],
    "Poster / banner": ["poster", "banner", "billboard"],
    "Brand guidelines": ["brand guide", "brand guidelines", "style guide"],
    "Packaging design": ["packaging", "label design"],
    "UI/UX design": ["ui design", "ux design", "figma", "mockup", "wireframe"],
    "Website": ["website", "web page", "landing page"],
    "Payment integration": ["payment", "stripe", "paypal", "checkout"],
    "Admin dashboard": ["admin", "dashboard"],
    "User login": ["login", "signup", "sign up", "authentication"],
    "SEO": ["seo"],
    "Blog / articles": ["blog", "article", "content writing"],
    "Newsletter / email": ["newsletter", "email template"],
    "Video editing": ["video", "reel", "youtube"],
    "Animation": ["animation", "motion graphics"],
    "Subtitles / voice-over": ["subtitle", "voice over", "voice-over", "voiceover"],
    "Mobile app": ["mobile app", "android app", "ios app"],
    "Ads / campaign": ["ads", "campaign"],
    "Hosting / domain setup": ["hosting", "domain"],
    "Maintenance / support": ["maintenance", "ongoing support", "updates after"],
    "Source files": ["source file", "editable file", "psd"],
}

# Words that show the client wants changes to existing work
REVISION_SIGNALS = [
    "revision", "change", "tweak", "adjust", "bigger", "smaller", "color",
    "colour", "font", "resize", "fix", "typo", "modify", "replace", "redo",
    "redesign", "start over", "different version", "one more change",
]

# Nouns that usually come with a quantity, mapped to one common name
QUANTITY_NOUNS = {
    "logo": "logo", "variation": "variation", "version": "variation",
    "option": "variation", "concept": "concept", "design": "design",
    "page": "page", "video": "video", "post": "post", "article": "article",
    "banner": "banner", "poster": "poster", "flyer": "flyer",
}

QTY_RE = re.compile(
    r"\b(\d+|a|an|one|two|three|four|five|six|seven|eight|nine|ten)\s+"
    r"(?:\w+\s+){0,2}?"
    r"(logos?|variations?|versions?|options?|concepts?|designs?|pages?|videos?|"
    r"posts?|articles?|banners?|posters?|flyers?)\b"
)


def contains(text: str, keyword: str) -> bool:
    """Whole-word match, plurals allowed ('ads' will not match 'downloads')."""
    return re.search(rf"\b{re.escape(keyword)}s?\b", text) is not None


def find_deliverables(text: str) -> set:
    text = text.lower()
    return {
        name
        for name, keywords in DELIVERABLE_KEYWORDS.items()
        if any(contains(text, k) for k in keywords)
    }


def find_quantities(text: str):
    """Returns ({noun: highest number}, {nouns asked as 'more/extra/additional'})."""
    counts, additive = {}, set()
    for m in QTY_RE.finditer(text.lower()):
        raw = m.group(1)
        number = int(raw) if raw.isdigit() else NUMBER_WORDS[raw]
        word = m.group(2)
        noun = QUANTITY_NOUNS[word[:-1] if word.endswith("s") else word]
        counts[noun] = max(counts.get(noun, 0), number)
        if re.search(r"\b(more|extra|additional)\b", m.group(0)):
            additive.add(noun)
    return counts, additive


def quantity_flags(agreement: str, request: str) -> list:
    agreed, _ = find_quantities(agreement)
    wanted, additive = find_quantities(request)
    flags = []
    for noun, number in wanted.items():
        covered = agreed.get(noun)
        if noun in additive:
            flags.append(f"Extra {noun}(s) requested on top of the agreed work")
        elif covered is None and number >= 2:
            flags.append(
                f"{number} {noun}(s) requested, but the agreement does not say how many are included"
            )
        elif covered is not None and number > covered:
            flags.append(
                f"{number} {noun}(s) requested, but the agreement covers {covered}"
            )
    return flags


def find_revision_limit(text: str):
    words = "|".join(k for k in NUMBER_WORDS if k not in ("a", "an"))
    m = re.search(
        rf"(\d+|{words})\s*(?:rounds?\s+of\s+)?revisions?", text, re.IGNORECASE
    )
    if not m:
        return None
    raw = m.group(1).lower()
    return int(raw) if raw.isdigit() else NUMBER_WORDS[raw]


def build_reply(verdict: str, out_of_scope: list, asks_revision: bool) -> str:
    if verdict == "In scope":
        if asks_revision:
            return (
                "Thanks for your feedback! This change is covered by the revisions "
                "in our agreement, so I will update it and send you the new version."
            )
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

    items = "; ".join(out_of_scope)
    return (
        "Thanks for your message! Part of this goes beyond our original agreement "
        f"({items}). I would be happy to help with it as an additional service. "
        "I can send you a quick quote and timeline for the extra work. "
        "Meanwhile, I will continue with the agreed scope."
    )


def check_scope(agreement: str, new_request: str) -> dict:
    agreed = find_deliverables(agreement)
    requested = find_deliverables(new_request)

    in_scope = sorted(requested & agreed)
    new_items = sorted(requested - agreed)
    qty_flags = quantity_flags(agreement, new_request)
    out_of_scope = new_items + qty_flags

    request_lower = new_request.lower()
    asks_revision = any(contains(request_lower, s) for s in REVISION_SIGNALS)

    limit = find_revision_limit(agreement)
    revision_note = None
    if asks_revision:
        if limit is not None:
            revision_note = (
                f"The client is asking for changes. Your agreement includes {limit} "
                f"revision(s). Check how many have already been used."
            )
        else:
            revision_note = (
                "The client is asking for changes, but your agreement has no revision "
                "limit. Add one to future agreements."
            )

    # Verdict
    if new_items and in_scope:
        verdict = "Partially out of scope"
        explanation = "Some requested items are in the agreement, but others are not."
    elif new_items:
        verdict = "Out of scope"
        explanation = "None of the requested items appear in the original agreement."
    elif qty_flags:
        verdict = "Possibly out of scope"
        explanation = (
            "The deliverable is in the agreement, but the amount requested may "
            "go beyond what was agreed."
        )
    elif requested:
        verdict = "In scope"
        explanation = (
            "Everything requested appears in the original agreement."
            if not asks_revision
            else "This looks like a change to agreed work, which counts as a revision."
        )
    elif asks_revision:
        verdict = "In scope"
        explanation = "This looks like a small change to existing work, which counts as a revision."
    else:
        verdict = "Unclear"
        explanation = "No specific deliverable was detected in the new request."

    return {
        "verdict": verdict,
        "explanation": explanation,
        "agreed_deliverables": sorted(agreed),
        "requested_deliverables": sorted(requested),
        "in_scope": in_scope,
        "out_of_scope": out_of_scope,
        "revision_note": revision_note,
        "suggested_reply": build_reply(verdict, out_of_scope, asks_revision),
        "note": "This is an automated suggestion. Always check your actual agreement.",
    }