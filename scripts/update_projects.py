
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
CARDS_DIR = ROOT / "assets" / "recent-projects"

START = "<!-- PROJECTS:START -->"
END = "<!-- PROJECTS:END -->"


def classify(repo):
    text = " ".join((
        repo.get("name") or "",
        repo.get("description") or "",
        " ".join(repo.get("topics") or [])
    )).lower()

    rules = [
        (
            ("power bi", "power-bi", "dashboard",
             "business intelligence", "petshop"),
            ("Business Intelligence", "BI", "#2f81f7")
        ),
        (
            ("teste-ab", "teste_a_b", "a/b",
             "hipotes", "estatistic", "statistic",
             "bootstrap", "experiment", "nps"),
            ("Estatística", "Σ", "#3fb950")
        ),
        (
            ("machine learning", "machine-learning",
             "regressao", "regression", "classification",
             "classificacao", "predict", "credit-risk",
             "credit risk", "payflow"),
            ("Machine Learning", "ML", "#a371f7")
        ),
        (
            ("react", "nextjs", "next.js", "frontend",
             "web", "api", "fastapi", "node"),
            ("Desenvolvimento", "</>", "#39c5cf")
        ),
        (
            ("dados", "data", "python", "sql", "etl"),
            ("Ciência de Dados", "DS", "#2f81f7")
        )
    ]

    for keywords, details in rules:
        if any(word in text for word in keywords):
            return details

    return "Projeto", "◆", "#8b949e"


def svg_card(repo):
    category, icon, accent = classify(repo)

    title = textwrap.shorten(
        repo["name"], width=43, placeholder="…"
    )

    description = " ".join(
        (repo.get("description")
         or "Projeto disponível no GitHub.").split()
    )

    description = textwrap.shorten(
        description, width=135, placeholder="…"
    )

    lines = textwrap.wrap(
        description,
        width=81,
        max_lines=2,
        placeholder="…"
    )

    line_one = lines[0] if lines else ""
    line_two = lines[1] if len(lines) > 1 else ""

    def e(value):
        return html.escape(value, quote=True)

    return f'''<svg xmlns="http://www.w3.org/2000/svg"
      width="900" height="126" viewBox="0 0 900 126"
      role="img"
      aria-label="{e(repo['name'] + ': ' + description)}">

      <rect x="1" y="1" width="898" height="124"
            rx="12" fill="#161b22"
            stroke="#30363d" stroke-width="2"/>

      <rect x="20" y="30" width="68" height="68"
            rx="12" fill="#21262d"/>

      <text x="54" y="72" text-anchor="middle"
            font-family="Arial, sans-serif"
            font-size="22" font-weight="bold"
            fill="{accent}">{e(icon)}</text>

      <text x="108" y="42"
            font-family="Arial, sans-serif"
            font-size="20" font-weight="bold"
            fill="#58a6ff">{e(title)}</text>

      <rect x="681" y="17"
            width="177" height="30" rx="15"
            fill="#21262d" stroke="{accent}"/>

      <text x="769" y="37" text-anchor="middle"
            font-family="Arial, sans-serif"
            font-size="13"
            fill="#f0f6fc">{e(category)}</text>

      <text x="108" y="77"
            font-family="Arial, sans-serif"
            font-size="14"
            fill="#c9d1d9">{e(line_one)}</text>

      <text x="108" y="99"
            font-family="Arial, sans-serif"
            font-size="14"
            fill="#c9d1d9">{e(line_two)}</text>

      <path d="M860 93 L876 77 M866 77 H876 V87"
            stroke="#8b949e" stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round" fill="none"/>
    </svg>
    '''


def fetch_projects():
    url = (
        f"https://api.github.com/users/{USERNAME}/repos"
        "?sort=created&direction=desc"
        "&per_page=100&type=owner"
    )

    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "vilhegas-profile-updater"
        }
    )

    with urllib.request.urlopen(
        request, timeout=30
    ) as response:
        repos = json.load(response)

    return [
        repo for repo in repos
        if not repo.get("fork")
        and not repo.get("archived")
        and repo["name"].lower() != USERNAME.lower()
    ][:5]


def update_readme(repos):
    content = README.read_text(encoding="utf-8")

    if (
        content.count(START) != 1
        or content.count(END) != 1
        or content.index(START) >= content.index(END)
    ):
        raise RuntimeError(
            "O README.md precisa conter exatamente "
            "um par de marcadores PROJECTS:START "
            "e PROJECTS:END."
        )

    CARDS_DIR.mkdir(parents=True, exist_ok=True)

    card_links = []
    keep = set()

    for repo in repos:
        filename = repo["name"] + ".svg"
        keep.add(filename)

        (CARDS_DIR / filename).write_text(
            svg_card(repo), encoding="utf-8"
        )

        image_path = (
            "assets/recent-projects/"
            + quote(filename)
        )

        card_links.append(
            f"[![{repo['name']}]({image_path})]"
            f"({repo['html_url']})"
        )

    for old in CARDS_DIR.glob("*.svg"):
        if old.name not in keep:
            old.unlink()

    replacement = (
        START + "\n\n"
        + "\n\n".join(card_links)
        + "\n\n" + END
    )

    revised = re.sub(
        re.escape(START) + r".*?" + re.escape(END),
        lambda _: replacement,
        content,
        count=1,
        flags=re.DOTALL
    )

    if revised != content:
        README.write_text(
            revised, encoding="utf-8"
        )

    return len(repos)


if __name__ == "__main__":
    count = update_readme(fetch_projects())
    print(f"Cards atualizados: {count}")
