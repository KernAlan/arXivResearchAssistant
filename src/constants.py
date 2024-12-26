# ArXiv URL abbreviations for main topics
ARXIV_TOPICS = {
    "Computer Science": "cs",
    "Mathematics": "math",
    "Physics": "physics",
    "Quantitative Biology": "q-bio",
    "Quantitative Finance": "q-fin",
    "Statistics": "stat",
    "Electrical Engineering": "eess",
    "Economics": "econ",
}

# ArXiv URL abbreviations for physics subtopics
PHYSICS_TOPICS = {
    "Astrophysics": "astro-ph",
    "Condensed Matter": "cond-mat",
    "General Relativity": "gr-qc",
    "High Energy Physics - Experiment": "hep-ex",
    "High Energy Physics - Theory": "hep-th",
    "Mathematical Physics": "math-ph",
    "Nuclear Theory": "nucl-th",
    "Quantum Physics": "quant-ph",
}

def get_topic_abbreviation(topic: str) -> str:
    """Get arXiv abbreviation for topic"""
    if topic == "Physics":
        raise ValueError("Must specify a physics subtopic")
    elif topic in PHYSICS_TOPICS:
        return PHYSICS_TOPICS[topic]
    elif topic in ARXIV_TOPICS:
        return ARXIV_TOPICS[topic]
    else:
        raise ValueError(f"Invalid topic: {topic}") 