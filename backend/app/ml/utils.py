from __future__ import annotations

import re


def dedupe_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for x in items:
        k = x.strip()
        if not k:
            continue
        key = k.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(k)
    return out


def normalize_skill(skill: str) -> str:
    s = skill.strip()
    s = re.sub(r"\s+", " ", s)
    return s


def normalize_skill_set(skills: list[str]) -> list[str]:
    return dedupe_preserve_order([normalize_skill(s) for s in skills if s.strip()])


_SKILL_SYNONYMS: dict[str, str] = {
    "ml": "Machine Learning",
    "machine learning": "Machine Learning",
    "nlp": "NLP",
    "natural language processing": "NLP",
    "js": "JavaScript",
    "javascript": "JavaScript",
    "node": "Node.js",
    "nodejs": "Node.js",
    "py": "Python",
    "python3": "Python",
    "sklearn": "scikit-learn",
    "scikit learn": "scikit-learn",
    "c plus plus": "C++",
    "cplusplus": "C++",
}


def canonicalize_skill(skill: str) -> str:
    key = normalize_skill(skill).lower()
    return _SKILL_SYNONYMS.get(key, normalize_skill(skill))


def skill_aliases() -> dict[str, str]:
    return dict(_SKILL_SYNONYMS)


def default_skill_dictionary() -> list[str]:
    # Curated manual dictionary used for both resume and JD extraction.
    # This intentionally augments spaCy ruler signals with domain-specific keywords.
    return [
        # Languages
        "Python",
        "Java",
        "JavaScript",
        "TypeScript",
        "C++",
        "C",
        "C#",
        "Go",
        "Rust",
        "SQL",
        # Backend
        "FastAPI",
        "Django",
        "Flask",
        "Node.js",
        "Express",
        "REST",
        "GraphQL",
        # Frontend
        "React",
        "Next.js",
        "Vue.js",
        "Angular",
        "Tailwind CSS",
        "HTML",
        "CSS",
        # Data / ML
        "Machine Learning",
        "Deep Learning",
        "NLP",
        "spaCy",
        "scikit-learn",
        "TensorFlow",
        "PyTorch",
        "pandas",
        "NumPy",
        "TF-IDF",
        "cosine similarity",
        "LLM",
        "GenAI",
        "RAG",
        # DevOps / Cloud
        "Docker",
        "Kubernetes",
        "CI/CD",
        "AWS",
        "Azure",
        "GCP",
        "S3",
        "Lambda",
        "EC2",
        "GitHub Actions",
        "Jenkins",
        # Observability
        "logging",
        "monitoring",
        "metrics",
        "Prometheus",
        "Grafana",
    ]

