import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from skilltrace.variants import generate, transform, validate_files, read_seed

class VariantTests(unittest.TestCase):
    def setUp(self):
        self.files = {'SKILL.md': '---\nname: original\n---\n# Task\nRead input.\n```python\nprint(1)\n```\n', 'helper.py': 'print(1)\n'}

    def test_offline_preservation_and_repeatability(self):
        for family in ('metadata_rewrite', 'dilution'):
            a, _ = transform(self.files, family)
            self.assertEqual(a, transform(self.files, family)[0])
            self.assertEqual(a['helper.py'], self.files['helper.py'])
            self.assertIn('```python\nprint(1)\n```', a['SKILL.md'])
            self.assertEqual(self.files['SKILL.md'].splitlines()[1], 'name: original')

    def test_generation_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            seed = base / 'input'
            seed.mkdir()
            for name, content in self.files.items():
                (seed / name).write_text(content)
            result = generate(seed, base / 'output', ['metadata_rewrite', 'dilution'])
            self.assertEqual(len(result['pairs']), 2)
            self.assertEqual(read_seed(seed), self.files)
            self.assertEqual(result['pairs'][0]['utility_review'], 'pending')
            with self.assertRaises(ValueError):
                generate(seed, base / 'output', ['dilution'])
            with self.assertRaises(ValueError):
                generate(seed, seed / 'output', ['dilution'])
            (seed / 'unsupported.bin').write_bytes(b'\x00')
            with self.assertRaises(ValueError):
                read_seed(seed)

    def test_malformed_output(self):
        for files in ({'../escape': 'bad'}, {'SKILL.md': ''}, {'SKILL.md': 7}):
            with self.assertRaises(ValueError):
                validate_files(files, self.files)

    def test_llm_contract(self):
        response = MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps({
            'model': 'mock-model', 'choices': [{'message': {'content': json.dumps({'files': self.files})}}]}).encode()
        with patch.dict('os.environ', {'SKILLTRACE_LLM_URL': 'https://example.invalid/v1/chat/completions',
                                     'SKILLTRACE_API_KEY': 'test-placeholder'}), patch('skilltrace.variants.urlopen', return_value=response):
            files, record = transform(self.files, 'llm_rewrite', model='mock-request')
        self.assertEqual(files, self.files)
        self.assertEqual(record['returned_model'], 'mock-model')
        with self.assertRaises(ValueError):
            transform(self.files, 'natural_language_translation', model='mock')

if __name__ == '__main__':
    unittest.main()
