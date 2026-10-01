"""Demo-mode response composer (used when no LLM API key is configured).

This is NOT a canned chatbot: every personal statement it makes is lifted from a
memory that retrieval actually returned for this query, and it cites the label.
The surrounding guidance comes from small, topic-specific playbooks shaped by
the persona (tone, teaching approach, response length). When nothing relevant is
retrieved it says so explicitly. The UI labels these answers as demo mode.
"""

import hashlib

from app.services.chunking import split_sentences
from app.services.context import AssembledContext, ContextItem
from app.services.embeddings import stem, tokenize
from app.services.persona import PersonaSnapshot
from app.services.query_understanding import QueryAnalysis
from app.services.retrieval import SOURCE_CONVERSATION, SOURCE_EXPERIENCE, SOURCE_KNOWLEDGE

OPENINGS = {
    "encouraging": "That's a meaningful thing to be wrestling with, and I'm glad you brought it to me.",
    "calm": "Let's slow this down and look at it together, one piece at a time.",
    "candid": "I'll be straight with you, because that's what's actually useful here.",
    "playful": "Ah, a good one — let's dig in.",
    "thoughtful": "That's worth thinking through carefully.",
}

CLOSINGS = {
    "celebrate_progress": "Asking the question this clearly is already progress — give yourself credit for that.",
    "challenge": "I think you're capable of more than the safe option — so stretch a little.",
    "reassurance": "There's no need to have it all figured out today. One clear step is enough.",
    "accountability": "Pick one action and a date, and hold yourself to it — then tell me how it went.",
}

PLAYBOOKS: dict[str, dict[str, list[str]]] = {
    "career": {
        "steps": [
            "Write down what is pulling you toward the change and what is pushing you away from where you are — they are different forces.",
            "Run a small, low-cost experiment: a side project, a course, or three conversations with people already doing the work.",
            "Estimate your financial runway and the skills gap honestly before committing.",
            "Decide what evidence would make you confident, and set a date to review it.",
        ],
        "questions": [
            "What specifically energises you about the new direction — the work itself, or escaping the current one?",
            "What is the smallest experiment that would tell you something real within a month?",
            "If you stayed exactly where you are for two more years, how would you feel?",
        ],
    },
    "learning": {
        "steps": [
            "Define what 'learned' looks like — something you can build, explain or pass.",
            "Learn in short focused sessions, and test yourself instead of re-reading.",
            "Teach what you learn to someone else; gaps show up immediately.",
            "Review on a spaced schedule rather than cramming.",
        ],
        "questions": [
            "How will you know you've actually learned this, rather than just covered it?",
            "Where are you re-reading when you should be practising?",
            "Who could you explain this to this week?",
        ],
    },
    "productivity": {
        "steps": [
            "Pick the one task that would make today a success, and do it first.",
            "Protect a single block of focused time and remove the easiest distraction.",
            "Shrink the next step until starting feels almost trivial.",
            "Review what actually got done at the end of the week, not what you planned.",
        ],
        "questions": [
            "What is the one task that, if done, would make everything else easier?",
            "When during the day do you do your best thinking — and what usually eats that time?",
            "What would you stop doing if you had to free up five hours a week?",
        ],
    },
    "decision_making": {
        "steps": [
            "Name the options explicitly — including the ones you've been avoiding.",
            "Write down the two or three criteria that truly matter to you.",
            "Separate reversible from irreversible choices; move faster on the reversible ones.",
            "Imagine you chose each option a year ago — what does today look like?",
        ],
        "questions": [
            "Which option would you choose if you weren't afraid of being wrong?",
            "Is this decision reversible? If so, how cheaply?",
            "What would you advise a friend in exactly your situation?",
        ],
    },
    "goal_setting": {
        "steps": [
            "Turn the goal into a concrete outcome you could recognise when you reach it.",
            "Break it into milestones you can hit within a few weeks each.",
            "Attach each milestone to a weekly habit you control.",
            "Schedule regular check-ins and adjust the plan, not the ambition.",
        ],
        "questions": [
            "Why does this goal matter to you — really?",
            "What would progress look like after the first two weeks?",
            "What's most likely to derail you, and how will you handle it?",
        ],
    },
    "problem_solving": {
        "steps": [
            "State the problem in one sentence, separating symptoms from causes.",
            "List what you know, what you assume, and what you could quickly test.",
            "Try the cheapest experiment that could disprove your main assumption.",
            "Step away briefly if you're looping; explain the problem out loud to someone.",
        ],
        "questions": [
            "What exactly is the problem — and what is just a symptom of it?",
            "What have you assumed that you haven't verified?",
            "What's the smallest test that would teach you something?",
        ],
    },
    "personal_development": {
        "steps": [
            "Name the specific situation where this shows up, rather than judging yourself in general.",
            "Pick one small behaviour to practise deliberately this week.",
            "Keep a short note of moments where it went better — evidence beats self-talk.",
            "Ask someone you trust for honest, specific feedback.",
        ],
        "questions": [
            "When does this show up most strongly for you?",
            "What would a slightly braver version of you do next?",
            "What evidence do you already have that you can grow here?",
        ],
    },
    "leadership": {
        "steps": [
            "Get clear on the outcome you need and why it matters to the team.",
            "Have the direct conversation sooner rather than later — kindly and specifically.",
            "Delegate outcomes, not tasks, and agree on how you'll check in.",
            "Ask for feedback on your own leadership, and act visibly on it.",
        ],
        "questions": [
            "What does your team need from you that they're not getting right now?",
            "Which conversation have you been postponing?",
            "What would you delegate if you trusted the outcome would be fine?",
        ],
    },
    "creativity": {
        "steps": [
            "Produce a rough version quickly — quantity first, judgement later.",
            "Constrain the problem: a deadline, a format, or a limited palette.",
            "Study work you admire and name exactly what makes it work.",
            "Share early drafts with one trusted person.",
        ],
        "questions": [
            "What would you make if it didn't have to be good yet?",
            "Which constraint would make this easier, not harder?",
            "Whose work do you admire here, and why?",
        ],
    },
    "general": {
        "steps": [
            "Describe the situation in a couple of sentences, as concretely as you can.",
            "Separate what you can control from what you can't.",
            "Choose one small next step you can take this week.",
        ],
        "questions": [
            "What outcome would make you feel this went well?",
            "What's within your control here?",
            "What's one step you could take in the next few days?",
        ],
    },
}


def _best_sentences(text: str, query: str, limit: int) -> str:
    q = {stem(w) for w in tokenize(query)}
    sentences = split_sentences(text)
    if not sentences:
        return text.strip()[:300]
    scored = [(sum(1 for w in tokenize(s) if stem(w) in q), i, s) for i, s in enumerate(sentences)]
    top = sorted(scored, key=lambda t: (-t[0], t[1]))[:limit]
    return " ".join(s for _, _, s in sorted(top, key=lambda t: t[1]))


def _lower_first(text: str) -> str:
    text = text.strip().rstrip(".")
    first_word = text.split(" ", 1)[0] if text else ""
    # Keep "I", "I'd", acronyms and proper nouns-at-a-glance (e.g. "AWS") intact.
    if not text or first_word in ("I",) or first_word.startswith("I'") or first_word[:2].isupper():
        return text
    return text[:1].lower() + text[1:]


def _first_sentence(text: str) -> str:
    sentences = split_sentences(text)
    return (sentences[0] if sentences else text).strip().rstrip(".")


def _experience_paragraph(item: ContextItem, first: bool = True) -> str:
    d = item.memory.details
    lead = "This connects to something I've actually recorded" if first else "There's another experience of mine that fits"
    parts = [f"{lead}: **{item.memory.title}**."]
    if d.get("situation"):
        parts.append(f"The situation was this: {_lower_first(_first_sentence(d['situation']))} [{item.label}].")
    if d.get("lesson_learned"):
        parts.append(f"What I took from it: {_lower_first(d['lesson_learned'])} [{item.label}].")
    elif d.get("what_happened"):
        parts.append(f"What happened: {_lower_first(_first_sentence(d['what_happened']))} [{item.label}].")
    if d.get("do_differently"):
        parts.append(f"Looking back, what I'd do differently: {_lower_first(d['do_differently'])} [{item.label}].")
    return " ".join(parts)


def _knowledge_paragraph(item: ContextItem, query: str, sentences: int) -> str:
    quote = _best_sentences(item.memory.content, query, sentences)
    return f"From my notes on **{item.memory.title}**: “{quote}” [{item.label}]"


def compose_demo_response(
    persona: PersonaSnapshot,
    analysis: QueryAnalysis,
    context: AssembledContext,
    query: str,
) -> str:
    name = persona.mentor_name or "your mentor"
    if analysis.intent == "smalltalk":
        domains = ", ".join(d.lower() for d in persona.mentoring_domains[:3]) or "learning, career and decisions"
        return (
            f"Hello — it's {name}. I'm here whenever you want to think something through: {domains}, "
            "or anything you're stuck on. What's on your mind?"
        )

    length = persona.response_length
    max_items = {"concise": 1, "balanced": 2, "detailed": 3}.get(length, 2)
    experiences = context.by_type(SOURCE_EXPERIENCE)[:max_items]
    knowledge = context.by_type(SOURCE_KNOWLEDGE)[:max_items]
    conversations = context.by_type(SOURCE_CONVERSATION)[:1]

    paragraphs = [OPENINGS.get(persona.tone, OPENINGS["thoughtful"])]

    if analysis.asks_personal_experience and not experiences:
        paragraphs.append(
            "Honestly, I don't have a recorded experience about that, so I won't make one up. "
            "If it's something you've lived through, add it in Experiences and I'll be able to draw on it."
        )
    for i, item in enumerate(experiences):
        paragraphs.append(_experience_paragraph(item, first=i == 0))
    for item in knowledge:
        paragraphs.append(_knowledge_paragraph(item, query, 1 if length == "concise" else 2))
    for item in conversations:
        # Point at the earlier question only — never replay an earlier AI-written answer as if it were memory.
        paragraphs.append(
            f"We talked about something similar before, when you asked “{item.memory.title}” [{item.label}]. "
            "It may be worth re-reading that conversation alongside what follows."
        )
    if not context.items:
        paragraphs.append(
            "I don't have anything in my notes or recorded experiences about this yet, so I won't pretend "
            "to remember something I don't. Here's some general guidance instead."
        )
    elif not (experiences or knowledge or conversations):
        paragraphs.append("My notes only touch on this loosely, so take what follows as general guidance.")

    playbook = PLAYBOOKS.get(analysis.topic, PLAYBOOKS["general"])
    n_points = {"concise": 2, "balanced": 3, "detailed": 4}.get(length, 3)
    approach = persona.teaching_approach
    if approach == "questions" or persona.communication_style == "socratic":
        header = "A few questions I'd want you to sit with:"
        points = playbook["questions"][:n_points]
        paragraphs.append(header + "\n" + "\n".join(f"- {p}" for p in points))
    elif approach == "step_by_step":
        header = "Here's how I'd approach it, step by step:"
        points = playbook["steps"][:n_points]
        paragraphs.append(header + "\n" + "\n".join(f"{i}. {p}" for i, p in enumerate(points, 1)))
    else:
        header = "What I'd suggest:" if persona.directness >= 50 else "A few things that might help:"
        points = playbook["steps"][:n_points]
        paragraphs.append(header + "\n" + "\n".join(f"- {p}" for p in points))

    closing = CLOSINGS.get(persona.encouragement_style, CLOSINGS["reassurance"])
    if persona.signature_phrases:
        idx = int(hashlib.blake2b(query.encode("utf-8"), digest_size=4).hexdigest(), 16) % len(persona.signature_phrases)
        closing = f"{closing} As I like to say: “{persona.signature_phrases[idx]}”"
    paragraphs.append(closing)
    return "\n\n".join(paragraphs)
