"""The agent index (docs/start-here/for-agents.md) must list every page and skill.

An agent that only reads the index never learns that an unlisted page exists, so a
new page without an index row is invisible to it. Stdlib only, like hooks/tests.
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / 'docs'
INDEX = DOCS / 'start-here' / 'for-agents.md'
NOT_INDEXED = {'start-here/tags.md', 'start-here/for-agents.md'}


class AgentIndexTest(unittest.TestCase):
    def setUp(self):
        self.text = INDEX.read_text()
        self.named = set(re.findall(r'`([a-z0-9/_-]+\.md)`', self.text))

    def test_every_page_is_listed(self):
        pages = {p.relative_to(DOCS).as_posix() for p in DOCS.rglob('*.md')}
        missing = sorted(pages - NOT_INDEXED - self.named)
        self.assertEqual(missing, [], 'add a row to docs/start-here/for-agents.md')

    def test_every_listed_page_exists(self):
        dangling = sorted(p for p in self.named if not (DOCS / p).is_file())
        self.assertEqual(dangling, [])

    def test_every_skill_is_listed(self):
        skills = sorted(p.name for p in (ROOT / 'skills').iterdir()
                        if (p / 'SKILL.md').is_file())
        self.assertTrue(skills)
        missing = [s for s in skills if f'`{s}`' not in self.text]
        self.assertEqual(missing, [], 'add the skill to docs/start-here/for-agents.md')


if __name__ == '__main__':
    unittest.main()
