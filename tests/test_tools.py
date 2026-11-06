import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import build
import query


class ToolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = build.load_data()

    def assert_invalid_data(self, modify):
        data = copy.deepcopy(self.data)
        modify(data)
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'references').mkdir()
            (root / 'references/knowledge.json').write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
            with self.assertRaises(ValueError):
                build.load_data(root)

    def test_duplicate_id_rejected(self):
        self.assert_invalid_data(lambda d: d['cards'][1].update(id=1))

    def test_original_body_edit_rejected(self):
        self.assert_invalid_data(lambda d: d['cards'][0].update(body_markdown='Changed original'))

    def test_alias_mapping_loss_rejected(self):
        self.assert_invalid_data(lambda d: d['cards'][86].update(canonical_id=87))

    def test_lookup_only_loss_rejected(self):
        self.assert_invalid_data(lambda d: d['cards'][93].update(mode='conditional'))

    def test_empty_teaching_rejected(self):
        self.assert_invalid_data(lambda d: d['cards'][0]['teaching'].update(learning_goal=''))

    def test_keyword_candidates_and_empty_query(self):
        self.assertIn(6, [c['id'] for c in query.search_cards(self.data['cards'], '不甘心')])
        self.assertEqual(query.search_cards(self.data['cards'], '   '), [])
        self.assertEqual(query.search_cards(self.data['cards'], 'zzzz_unrelated_zzzz'), [])

    def test_invalid_id_fails_without_traceback(self):
        run = subprocess.run([sys.executable, '-B', str(ROOT / 'scripts/query.py'), '--id', '0'], capture_output=True, encoding='utf-8')
        self.assertNotEqual(run.returncode, 0)
        self.assertIn('IDs must be between', run.stderr)
        self.assertNotIn('Traceback', run.stderr)

    def test_check_is_read_only_and_all_generated_files_match(self):
        expected = build.generated_files()
        before = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in expected}
        run = subprocess.run([sys.executable, '-B', str(ROOT / 'scripts/build.py'), '--check'], capture_output=True, encoding='utf-8')
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        after = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in expected}
        self.assertEqual(before, after)
        for path, content in expected.items():
            self.assertEqual((ROOT / path).read_text(encoding='utf-8'), content, path)


if __name__ == '__main__':
    unittest.main()
