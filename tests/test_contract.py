import json
import unittest
from pathlib import Path
from importlib.util import module_from_spec, spec_from_file_location

ROOT = Path(__file__).resolve().parent.parent
spec = spec_from_file_location('runner', ROOT / 'examples/run.py')
runner = module_from_spec(spec)
spec.loader.exec_module(runner)

class ContractTests(unittest.TestCase):
    def test_manifests_have_project_report_capabilities(self):
        manifests = list((ROOT / 'extensions').glob('*/extension.json'))
        self.assertEqual(len(manifests), 2)
        for path in manifests:
            value = json.loads(path.read_text())
            self.assertEqual(value['protocol'], 'observer-extension/v1')
            self.assertEqual(value['id'], path.parent.name)
            self.assertEqual(value['network'], [])
            self.assertEqual(set(value['permissions']), {'project:read', 'reports:write'})
            self.assertTrue(value['checks'])
    def test_query_pins_scope(self):
        value = runner.query({'where': '?entity a ?type.'}, 'https://example.org/project/snapshot')
        self.assertIn('GRAPH <https://example.org/project/snapshot>', value)
        self.assertIn('COUNT(DISTINCT ?entity)', value)
        self.assertIn('LIMIT 201', value)
    def test_scope_injection_rejected(self):
        for revision in ['https://example.org/> } SERVICE <https://bad.example', 'not a graph', 'https://example.org/\nother']:
            with self.assertRaises(ValueError):
                runner.query({'where': '?entity a ?type.'}, revision)

if __name__ == '__main__':
    unittest.main()
