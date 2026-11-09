
import json
import re
import urllib.request
from pathlib import Path

USERNAME = "vilhegas"
README = Path("README.md")

url = (
    f"https://api.github.com/users/{USERNAME}/repos"
    "?sort=created&direction=desc&per_page=100"
)

request = urllib.request.Request(
    url,
    headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "github-profile-updater",
    },
)

with urllib.request.urlopen(request, timeout=20) as response:
    repositories = json.load(response)

projects = [
    repo for repo in repositories
    if not repo["fork"]
    and not repo["archived"]
    and repo["name"].lower() != USERNAME.lower()
][:5]

lines = []

for repo in projects:
    name = repo["name"].replace("|", "\\|")
    description = (
        repo.get("description") or "Projeto disponível no GitHub."
    ).replace("\n", " ").replace("|", "\\|")

    lines.append(
        f"- **[{name}]({repo['html_url']})** — {description}"
    )

content = README.read_text(encoding="utf-8")

pattern = r"<!-- PROJECTS:START -->.*?<!-- PROJECTS:END -->"
replacement = (
    "<!-- PROJECTS:START -->\n"
    + "\n".join(lines)
    + "\n<!-- PROJECTS:END -->"
)

updated, count = re.subn(
    pattern,
    lambda match: replacement,
    content,
    flags=re.DOTALL,
)

if count != 1:
    raise ValueError("Marcadores dos projetos não encontrados.")

if updated != content:
    README.write_text(updated, encoding="utf-8")
