"""Checks for registry integrity; uses temporary files, never project data."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import research


class RegistryChecks(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        overview = self.root / 'overview'; overview.mkdir()
        data = self.root / 'datasets' / 'active'; data.mkdir(parents=True)
        (data / 'manifest.json').write_text('{}')
        (overview / 'PROJECT.json').write_text(json.dumps({'dataset': {'id': 'data-v1', 'directory': 'datasets/active'}, 'benchmark': {'id': 'bench-v1'}}))
        (overview / 'research_catalog.json').write_text(json.dumps([{'id': 'prior', 'candidate_id': 'old-model', 'title': 'Old method', 'status': 'stopped', 'finding': 'No gain', 'evidence': []}]))
        self.patches = [patch.object(research, 'ROOT', self.root), patch.object(research, 'OVERVIEW', overview), patch.object(research, 'RECORDS', self.root / 'experiments')]
        for p in self.patches: p.start()
        self.spec = dict(id='new-run', hypothesis='Test a changed mechanism', change='New mechanism', related_work=['prior'],
            dataset_id='data-v1', input_hashes={'datasets/active/manifest.json': research.sha(data / 'manifest.json')},
            clock='clock-v1', features='extended', candidate_id='new-model', model_parameters={'depth': 2},
            decision_policy={'horizon': 3}, benchmark_id='bench-v1', seasons=['2023-24', '2022-23'],
            resources={'threads': 1}, success_criterion='positive paired result', stop_rule='stop on failed gate', maximum_runs=2)

    def tearDown(self):
        for p in reversed(self.patches): p.stop()
        self.tmp.cleanup()

    def test_changed_input_is_rejected(self):
        research.validate(self.spec)
        (self.root / 'datasets/active/manifest.json').write_text('{"changed": true}')
        with self.assertRaisesRegex(ValueError, 'Input changed'): research.validate(self.spec)

    def test_exact_repeat_is_rejected_even_with_new_id(self):
        spec = dict(self.spec, fingerprint=research.validate(self.spec))
        research.exclusive(research.RECORDS / 'first.proposal.json', spec)
        repeat = dict(self.spec, id='renamed-run')
        with self.assertRaisesRegex(ValueError, 'Identical registered'): research.validate(repeat)

    def test_known_candidate_and_unknown_related_work_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Candidate already explored'):
            research.validate(dict(self.spec, candidate_id='old-model'))
        with self.assertRaisesRegex(ValueError, 'unknown catalog ID'):
            research.validate(dict(self.spec, related_work=['invented']))

    def test_season_order_does_not_change_identity(self):
        other = dict(self.spec, seasons=list(reversed(self.spec['seasons'])))
        self.assertEqual(research.fingerprint(self.spec), research.fingerprint(other))

    def test_evidence_path_cannot_escape_project(self):
        with self.assertRaisesRegex(ValueError, 'outside project'):
            research.local('../outside.json')

    def test_existing_record_cannot_be_overwritten(self):
        path = research.RECORDS / 'record.json'
        research.exclusive(path, {'original': True})
        with self.assertRaises(FileExistsError): research.exclusive(path, {'original': False})
        self.assertEqual(research.read(path), {'original': True})


if __name__ == '__main__':
    unittest.main()
