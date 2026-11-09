"""Atualiza a seção de repositórios recentes do README de perfil GitHub."""

import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path

USERNAME = "vilhegas"
LIMIT = 5
README_PATH = Path(__file__).resolve().parents[1] / "README.md"
START = "<!-- PROJECTS:START -->"
END = "<!-- PROJECTS:END -->"


def fetch_recent_repositories():
    """Busca repositórios públicos, do mais novo para o mais antigo."""
    url = (
        f"https://api.github.com/users/{USERNAME}/repos"
        "?sort=created&direction=desc&per_page=100"
    )
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "vilhegas-profile-updater",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        repositories = json.load(response)

    return [
        repo
        for repo in repositories
        if not repo.get("fork", False)
        and not repo.get("archived", False)
        and repo["name"].lower() != USERNAME.lower()
    ][:LIMIT]


def clean_markdown(text):
    """Impede que descrições quebrem linhas ou formatação Markdown."""
    text = " ".join(str(text).split())
    return text.replace("\\", "\\\\").replace("|", "\\|").replace("[", "\\[").replace("]", "\\]")


def update_readme(repositories):
    content = README_PATH.read_text(encoding="utf-8")
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.DOTALL)
    if len(pattern.findall(content)) != 1:
        raise ValueError("O README deve conter um único par de marcadores PROJECTS.")

    if repositories:
        lines = [
            f"- **[{clean_markdown(repo['name'])}]({repo['html_url']})** — "
            f"{clean_markdown(repo.get('description') or 'Projeto disponível no GitHub.')}"
            for repo in repositories
        ]
        body = "\n".join(lines)
    else:
        body = "*Nenhum repositório público encontrado.*"

    section = f"{START}\n{body}\n{END}"
    result = pattern.sub(lambda _: section, content)
    if result != content:
        README_PATH.write_text(result, encoding="utf-8")
        print(f"README atualizado com {len(repositories)} projeto(s).")
    else:
        print("README já está atualizado.")


if __name__ == "__main__":
    try:
        update_readme(fetch_recent_repositories())
    except (urllib.error.URLError, json.JSONDecodeError, OSError, ValueError) as exc:
        raise SystemExit(f"Erro ao atualizar projetos: {exc}") from exc
