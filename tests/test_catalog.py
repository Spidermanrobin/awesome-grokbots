"""Regression tests for data loss, attribution, validation and deterministic output."""
import copy
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from common import ROOT, load_catalog, read_yaml
import check_links
from build import outputs
from validate import validate
import yaml


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for folder in ('data', 'schema', 'i18n', 'web'):
            shutil.copytree(ROOT / folder, self.root / folder)

    def snapshot(self):
        return {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob('*') if p.is_file()}

    def write(self, relative, content):
        (self.root / relative).write_text(yaml.safe_dump(content, allow_unicode=True, sort_keys=False))

    def test_only_404_and_410_are_gone(self):
        cases = {200:'alive', 204:'alive', 301:'alive', 399:'alive', 400:'error', 401:'blocked', 403:'blocked', 404:'gone', 405:'error', 410:'gone', 429:'blocked', 500:'error', 503:'error', 999:'error', None:'error'}
        for status, expected in cases.items():
            self.assertEqual(check_links.classify(status), expected, status)

    def test_breaker_boundary_and_no_writes_even_with_gone(self):
        data = load_catalog(self.root)
        entries = data['bots'][:4]
        results = [{'id':e['id'], 'bucket':b} for e,b in zip(entries, ['gone','blocked','error','alive'])]
        before = self.snapshot()
        self.assertFalse(check_links.apply_results(self.root, data, results, '2026-10-21'))
        self.assertEqual(self.snapshot(), before)
        self.assertFalse(check_links.tripped([{'bucket':b} for b in ['blocked','alive','alive','gone']]))
        self.assertTrue(check_links.tripped([{'bucket':b} for b in ['error','alive','alive']]))
        self.assertFalse(check_links.tripped([]))

    def test_retirement_cleans_picks_and_preserves_uncertain_rows(self):
        data = load_catalog(self.root)
        entries = data['bots'][:4]
        self.write('data/picks.yaml', [{'week':'2026-10-19', 'entries':[entries[0]['id']]}])
        results = [{'id':e['id'],'bucket':b} for e,b in zip(entries,['gone','alive','blocked','alive'])]
        self.assertTrue(check_links.apply_results(self.root, data, results, '2026-10-21'))
        retired = read_yaml(self.root / 'data/retired.yaml')
        self.assertEqual(retired[0]['id'], entries[0]['id'])
        self.assertEqual(retired[0]['status'], 'retired')
        remaining = load_catalog(self.root)['bots']
        self.assertNotIn(entries[0]['id'], [e['id'] for e in remaining])
        self.assertEqual(next(e for e in remaining if e['id'] == entries[2]['id']), entries[2])
        self.assertEqual(read_yaml(self.root / 'data/picks.yaml'), [])
        validate(self.root)

    def test_dry_run_and_trip_do_not_create_report(self):
        import validate as validation
        for write, buckets in [(False,['gone','alive','alive','alive']), (True,['gone','blocked','error','alive'])]:
            data = {'bots':load_catalog(self.root)['bots'][:4], 'skills':[], 'guides':[]}
            values = [{'id':e['id'],'url':e['url'],'status':404 if b=='gone' else None,'bucket':b} for e,b in zip(data['bots'], buckets)]
            args=['check_links.py', '--report', str(self.root / 'report.json'), '--write' if write else '--dry-run']
            before=self.snapshot()
            with patch.object(check_links, 'ROOT', self.root), patch.object(check_links, 'load_catalog', return_value=data), patch.object(check_links, 'probe', side_effect=values), patch.object(validation, 'validate'), patch.object(sys,'argv',args):
                self.assertEqual(check_links.main(), 2 if write else 1)
            self.assertEqual(before, self.snapshot())

    def test_rejects_duplicate_and_unknown_pick(self):
        data = load_catalog(self.root)
        self.write('data/bots.yaml', data['bots'] + [data['bots'][0]])
        with self.assertRaisesRegex(ValueError,'duplicate'):
            validate(self.root)
        self.write('data/bots.yaml',data['bots'])
        self.write('data/picks.yaml',[{'week':'2026-10-19','entries':['missing-id']}])
        with self.assertRaisesRegex(ValueError,'IDs must be unique active'):
            validate(self.root)

    def test_rejects_missing_attribution_and_invalid_date(self):
        data=load_catalog(self.root)
        row=next(e for e in data['skills'] if e['source']['license']=='CC-BY-4.0')
        del row['source']['attribution']
        self.write('data/skills.yaml',data['skills'])
        with self.assertRaisesRegex(ValueError,'attribution'):
            validate(self.root)
        shutil.copy(ROOT/'data/skills.yaml',self.root/'data/skills.yaml')
        data['bots'][0]['added']='2026-02-30'
        self.write('data/bots.yaml',data['bots'])
        with self.assertRaisesRegex(ValueError,'date'):
            validate(self.root)

    def test_duplicate_yaml_keys_are_errors(self):
        (self.root/'data/picks.yaml').write_text('- week: "2026-10-19"\n  week: "2026-10-26"\n  entries: []\n')
        with self.assertRaisesRegex(ValueError,'Duplicate YAML key'):
            validate(self.root)

    def test_outputs_deterministic_and_attributed(self):
        first=outputs(self.root)
        self.assertEqual(first,outputs(self.root))
        self.assertEqual(first['dist/catalog.json'],first['site/data/catalog.json'])
        for name in ['README.md','README.zh-CN.md','README.ja.md','llms.txt']:
            self.assertIn('ZeroPointRepo/awesome-grok-bot contributors',first[name])
            self.assertIn('Metadata normalized; reviews rewritten and translated.',first[name])
            self.assertIn('https://creativecommons.org/licenses/by/4.0/',first[name])

    def test_new_locale_needs_only_one_yaml_file(self):
        ui=read_yaml(self.root/'i18n/en.yaml');ui['language_name']='Français'
        self.write('i18n/fr.yaml',ui)
        result=outputs(self.root)
        self.assertIn('README.fr.md',result)
        self.assertIn('fr',json.loads(result['site/data/ui.json']))
        self.assertIn(load_catalog(self.root)['bots'][0]['review'],result['README.fr.md'])

    def test_seed_audit_records_successful_accepted_urls(self):
        # The historical audit must not prevent new entries or future tier reviews.
        audit=json.loads((ROOT/'docs/seed-link-audit.json').read_text())
        accepted=[r for r in audit['results'] if r['accepted']]
        self.assertEqual(len({r['url'] for r in accepted}),len(accepted))
        for record in accepted:
            self.assertGreaterEqual(record['status'],200)
            self.assertLess(record['status'],400)



if __name__ == '__main__':
    unittest.main()
