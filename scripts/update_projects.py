"""Atualiza cards SVG dos projetos em destaque e dos projetos recentes."""

import html
import json
import re
import textwrap
import urllib.request
from pathlib import Path
from urllib.parse import quote

USERNAME = "vilhegas"
ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
CONFIG = ROOT / "featured_projects.json"
CARDS = ROOT / "assets" / "projects"

SECTIONS = {
    "featured": ("<!-- FEATURED:START -->", "<!-- FEATURED:END -->"),
    "recent": ("<!-- PROJECTS:START -->", "<!-- PROJECTS:END -->"),
}


def fetch_repositories():
    url = (
        f"https://api.github.com/users/{USERNAME}/repos"
        "?type=owner&sort=created&direction=desc&per_page=100"
    )
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "vilhegas-readme-project-cards",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        repositories = json.load(response)
    return [
        item for item in repositories
        if not item.get("fork")
        and not item.get("archived")
        and item.get("name", "").lower() != USERNAME.lower()
    ]


def classify(repo):
    content = " ".join([
        repo.get("name", ""),
        repo.get("description") or "",
        " ".join(repo.get("topics") or []),
    ]).lower()
    rules = [
        (("power-bi", "power bi", "dashboard", "business intelligence", "petshop"),
         ("Business Intelligence", "BI", "#85a9c6")),
        (("teste-ab", "teste_a_b", "a/b", "hipotes", "estatistic", "statistic", "bootstrap", "experiment", "nps"),
         ("Estatística", "Σ", "#8bb49b")),
        (("agent", "agente", "llm", "inteligencia artificial", "artificial intelligence", "generative ai"),
         ("Inteligência Artificial", "AI", "#94bea6")),
        (("machine learning", "machine-learning", "regressao", "regression", "classification", "classificacao", "predict", "credit-risk", "credit risk", "payflow"),
         ("Machine Learning", "ML", "#b2a0c8")),
        (("react", "nextjs", "next.js", "frontend", "web", "api", "fastapi", "node"),
         ("Desenvolvimento", "</>", "#88b4bb")),
        (("dados", "data", "python", "sql", "etl"),
         ("Ciência de Dados", "DS", "#94b2d2")),
    ]
    for keywords, values in rules:
        if any(keyword in content for keyword in keywords):
            return values
    return "Projeto", "◆", "#a1abb9"


def shorten_lines(value, max_chars=125):
    clean = " ".join((value or "Projeto disponível no GitHub.").split())
    clean = textwrap.shorten(clean, width=max_chars, placeholder="…")
    lines = textwrap.wrap(clean, width=80, max_lines=2, placeholder="…")
    return (lines + ["", ""])[:2]


def svg_card(repo):
    label, icon, color = classify(repo)
    title = textwrap.shorten(repo["name"], width=43, placeholder="…")
    a, b = shorten_lines(repo.get("description"))
    e = lambda value: html.escape(value, quote=True)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="900" height="105"
 viewBox="0 0 900 105" role="img" aria-label="{e(repo['name'])}">
 <rect x="1" y="1" width="898" height="103" rx="12" fill="#161b22" stroke="#353d46" stroke-width="2"/>
 <rect x="16" y="23" width="60" height="60" rx="11" fill="#262e37"/>
 <text x="46" y="60" text-anchor="middle" fill="{color}"
   font-family="Arial,DejaVu Sans,sans-serif" font-size="21" font-weight="bold">{e(icon)}</text>
 <text x="94" y="38" fill="#93bfdf"
   font-family="Arial,DejaVu Sans,sans-serif" font-size="19" font-weight="bold">{e(title)}</text>
 <text x="94" y="63" fill="#d0d7de"
   font-family="Arial,DejaVu Sans,sans-serif" font-size="14">{e(a)}</text>
 <text x="94" y="83" fill="#d0d7de"
   font-family="Arial,DejaVu Sans,sans-serif" font-size="14">{e(b)}</text>
 <rect x="682" y="14" width="175" height="27" rx="14" fill="#232a33" stroke="{color}"/>
 <text x="769" y="32" text-anchor="middle" fill="#e6edf3"
   font-family="Arial,DejaVu Sans,sans-serif" font-size="12">{e(label)}</text>
 <path d="M863 77 L879 61 M869 61 H879 V71" stroke="#a1abb9" stroke-width="2"
   stroke-linecap="round" stroke-linejoin="round" fill="none"/>
</svg>
'''


def choose_projects(repositories):
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    requested = config.get("projects", [])
    if not isinstance(requested, list) or not all(isinstance(v, str) for v in requested):
        raise ValueError("featured_projects.json deve conter uma lista de nomes em 'projects'.")
    if len(requested) > 3:
        raise ValueError("Escolha no máximo três projetos em destaque.")
    repo_by_name = {repo["name"].lower(): repo for repo in repositories}
    featured = []
    for name in requested:
        repo = repo_by_name.get(name.lower())
        if repo and repo not in featured:
            featured.append(repo)
        else:
            print(f"Aviso: repositório em destaque não encontrado ou duplicado: {name}")
    featured_names = {item["name"].lower() for item in featured}
    recent = [repo for repo in repositories if repo["name"].lower() not in featured_names][:3]
    return featured, recent


def replace_section(readme, key, body):
    start, end = SECTIONS[key]
    if readme.count(start) != 1 or readme.count(end) != 1:
        raise ValueError(f"Marcadores de {key} ausentes ou duplicados no README.")
    if readme.index(start) >= readme.index(end):
        raise ValueError(f"Marcadores de {key} estão invertidos no README.")
    pattern = re.escape(start) + r".*?" + re.escape(end)
    return re.sub(pattern, lambda _: start + "\n\n" + body + "\n\n" + end,
                  readme, count=1, flags=re.DOTALL)


def render(repositories):
    featured, recent = choose_projects(repositories)
    original = README.read_text(encoding="utf-8")
    # Validar os dois blocos antes de escrever arquivos.
    for key in SECTIONS:
        start, end = SECTIONS[key]
        if original.count(start) != 1 or original.count(end) != 1 or original.index(start) >= original.index(end):
            raise ValueError(f"Marcadores inválidos para {key} no README.")
    CARDS.mkdir(parents=True, exist_ok=True)
    keep = set()
    content = original
    for key, selected in (("featured", featured), ("recent", recent)):
        fragments = []
        for repo in selected:
            filename = f"{key}-{repo['name']}.svg"
            keep.add(filename)
            path = CARDS / filename
            svg = svg_card(repo)
            if not path.exists() or path.read_text(encoding="utf-8") != svg:
                path.write_text(svg, encoding="utf-8")
            image_url = "assets/projects/" + quote(filename)
            fragments.append(f"[![{repo['name']}]({image_url})]({repo['html_url']})")
        body = "\n\n".join(fragments) if fragments else "*Nenhum projeto para exibir.*"
        content = replace_section(content, key, body)
    for file in CARDS.glob("*.svg"):
        if file.name not in keep:
            file.unlink()
    if content != original:
        README.write_text(content, encoding="utf-8")
    print(f"Atualizado: {len(featured)} destaques e {len(recent)} recentes.")


def main():
    render(fetch_repositories())


if __name__ == "__main__":
    main()
