import importlib.util
import json
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("update_projects", ROOT / "scripts" / "update_projects.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class TestCards(unittest.TestCase):
    def test_cards_sections_limits_button_svg_and_repeatability(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)
            original = (
                "## Destaques\n<!-- FEATURED:START -->\nplaceholder\n<!-- FEATURED:END -->\n"
                "## Recentes\n<!-- PROJECTS:START -->\nplaceholder\n<!-- PROJECTS:END -->\n"
                "[![EXPLORAR MEUS REPOSITÓRIOS](badge)](https://example.com)\n"
            )
            (path / "README.md").write_text(original, encoding="utf-8")
            (path / "featured_projects.json").write_text(json.dumps({"projects": ["Payflow-Credit-Risk", "credit-risk-intelligence", "resume-ai-agent-starter"]}))
            repositories = [
                {"name": n, "description": "Descrição de projeto de dados", "html_url": f"https://github.com/vilhegas/{n}", "topics": []}
                for n in ["test-6", "test-5", "test-4", "test-3", "resume-ai-agent-starter", "credit-risk-intelligence", "Payflow-Credit-Risk"]
            ]
            old = (mod.ROOT, mod.README, mod.CONFIG, mod.CARDS)
            try:
                mod.ROOT, mod.README, mod.CONFIG, mod.CARDS = path, path / "README.md", path / "featured_projects.json", path / "assets" / "projects"
                mod.render(repositories)
                output = mod.README.read_text(encoding="utf-8")
                self.assertEqual(output.count('assets/projects/featured-'), 3)
                self.assertEqual(output.count('assets/projects/recent-'), 3)
                self.assertEqual(output.count('EXPLORAR MEUS REPOSITÓRIOS'), 1)
                self.assertNotIn('recent-Payflow-Credit-Risk.svg', output)
                self.assertIn('recent-test-6.svg', output)
                self.assertEqual(len(list(mod.CARDS.glob('*.svg'))), 6)
                for file in mod.CARDS.glob('*.svg'):
                    ET.parse(file)
                mod.render(repositories)
                self.assertEqual(mod.README.read_text(encoding="utf-8"), output)
            finally:
                mod.ROOT, mod.README, mod.CONFIG, mod.CARDS = old

    def test_rejects_more_than_three_featured(self):
        with tempfile.TemporaryDirectory() as folder:
            config = Path(folder) / "featured_projects.json"
            config.write_text(json.dumps({"projects": ["a", "b", "c", "d"]}))
            old = mod.CONFIG
            try:
                mod.CONFIG = config
                with self.assertRaisesRegex(ValueError, "máximo três"):
                    mod.choose_projects([])
            finally:
                mod.CONFIG = old


if __name__ == '__main__':
    unittest.main()
