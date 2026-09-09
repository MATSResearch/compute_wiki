import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / 'skill_hint.py'
spec = importlib.util.spec_from_file_location('skill_hint', SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class HintTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.env = patch.dict(os.environ, {
            'MATS_SKILLS_DIR': str(self.root / 'skills'),
            'MATS_SKILL_HINT_STATE_DIR': str(self.root / 'state'),
            'MATS_SKILL_HINTS': '1', 'MATS_SKILL_HINT_MUTE': '',
        })
        home = patch.object(Path, "home", return_value=self.root)
        home.start()
        self.addCleanup(home.stop)
        self.env.start()
        self.addCleanup(self.env.stop)
        for name in set(module.RULES.values()):
            p = self.root / 'skills' / name / 'SKILL.md'
            p.parent.mkdir(parents=True)
            p.write_text('test skill')

    def event(self, tool='Edit', path='Main.lean', session='one'):
        return dict(hook_event_name='PostToolUse', session_id=session,
                    cwd=str(self.root), tool_name=tool, tool_input={'file_path': path})

    def test_hint_only_context_and_once_per_session(self):
        result = module.hint(self.event())
        self.assertEqual(set(result), {'hookSpecificOutput'})
        self.assertEqual(set(result['hookSpecificOutput']), {'hookEventName', 'additionalContext'})
        self.assertIn('mats-lean-cleanup', result['hookSpecificOutput']['additionalContext'])
        self.assertIsNone(module.hint(self.event(tool='Write', path='Other.lean')))
        self.assertIsNotNone(module.hint(self.event(session='two')))

    def test_cli_delivers_context_and_other_project_is_independent(self):
        p = subprocess.run([sys.executable, str(SCRIPT)], input=json.dumps(self.event()),
                           text=True, capture_output=True)
        self.assertEqual(p.returncode, 0)
        self.assertEqual(p.stderr, '')
        self.assertEqual(json.loads(p.stdout)['hookSpecificOutput']['hookEventName'], 'PostToolUse')
        self.assertIsNone(module.hint(self.event()))
        self.assertIsNotNone(module.hint(self.event() | {'cwd': str(self.root / 'other')}))
        self.assertIsNone(module.hint(self.event(session='failure') |
                                     {'hook_event_name': 'PostToolUseFailure'}))

    def test_read_and_edit_have_distinct_relevance(self):
        self.assertIn('mats-lean-formalization', str(module.hint(self.event(tool='Read'))))
        self.assertIn('mats-lean-cleanup', str(module.hint(self.event())))

    def test_loaded_skill_stays_quiet(self):
        self.assertIsNone(module.hint(self.event(tool='Read', path='skills/mats-lean-cleanup/SKILL.md')))
        self.assertIsNone(module.hint(self.event()))
        e = self.event(tool='Skill')
        e['tool_input'] = {'skill': 'mats-lean-formalization'}
        self.assertIsNone(module.hint(e))
        self.assertIsNone(module.hint(self.event(tool='Read')))

    def test_irrelevant_missing_disabled_and_muted(self):
        self.assertIsNone(module.hint(self.event(path='lean_notes.md')))
        self.assertIsNone(module.hint(self.event(tool='Bash')))
        (self.root / 'skills/mats-lean-cleanup/SKILL.md').unlink()
        self.assertIsNone(module.hint(self.event()))
        with patch.dict(os.environ, {'MATS_SKILL_HINTS': '0'}):
            self.assertIsNone(module.hint(self.event(tool='Read')))
        with patch.dict(os.environ, {'MATS_SKILL_HINT_MUTE': 'mats-lean-formalization'}):
            self.assertIsNone(module.hint(self.event(tool='Read')))

    def test_concurrent_calls_emit_once(self):
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(lambda _: module.hint(self.event()), range(20)))
        self.assertEqual(sum(x is not None for x in results), 1)

    def test_cli_bad_inputs_and_unwritable_state_fail_open(self):
        for raw in ('not json', '[]', '{}', json.dumps(self.event() | {'tool_input': None})):
            p = subprocess.run([sys.executable, str(SCRIPT)], input=raw, text=True, capture_output=True)
            self.assertEqual((p.returncode, p.stdout, p.stderr), (0, '', ''))
        (self.root / 'state').write_text('not a directory')
        p = subprocess.run([sys.executable, str(SCRIPT)], input=json.dumps(self.event()),
                           text=True, capture_output=True)
        self.assertEqual((p.returncode, p.stdout, p.stderr), (0, '', ''))


if __name__ == '__main__':
    unittest.main()
