"""Validate local integrity and references. Does not evaluate teaching effectiveness."""
import hashlib
import json
import re
from pathlib import Path
from build import ROOT, load_data, generated_files


def validate(root=ROOT):
    errors = []
    data = load_data(root)
    outputs = generated_files(root)
    actual_cards = sorted(p.name for p in (root / 'references/theories').glob('*.md'))
    expected_cards = [f'{i:03d}.md' for i in range(1, 101)]
    if actual_cards != expected_cards:
        errors.append('Missing or extra theory cards')
    for rel, expected in outputs.items():
        path = root / rel
        if not path.is_file() or path.read_text(encoding='utf-8') != expected:
            errors.append('Out of sync: ' + rel)
    sources = (root / 'references/sources.md').read_text(encoding='utf-8')
    source_ids = set(re.findall(r'^## ([KT]\d{2})\s*$', sources, re.M))
    used = set()
    for c in data['cards']:
        used.update(re.findall(r'\bK\d{2}\b', c['body_markdown']))
    if used - source_ids:
        errors.append('Missing source IDs: ' + ', '.join(sorted(used - source_ids)))
    for path in root.rglob('*.md'):
        if '.git' in path.parts:
            continue
        text = path.read_text(encoding='utf-8')
        for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)', text):
            target = target.split('#', 1)[0]
            if not target or re.match(r'^[a-zA-Z]+:', target):
                continue
            if not (path.parent / target).is_file():
                errors.append(f'Broken link: {path.relative_to(root)} -> {target}')
    cases = json.loads((root / 'tests/cases.json').read_text(encoding='utf-8'))['cases']
    coverage = json.loads((root / 'tests/coverage.json').read_text(encoding='utf-8'))['cases']
    if len(cases) != 10 or len(coverage) != 100:
        errors.append('Incorrect model exercise coverage')
    skill = (root / 'SKILL.md').read_text(encoding='utf-8')
    if not re.match(r'\A---\nname: life-dilemma-guide\ndescription: .+\n', skill):
        errors.append('Missing skill identity or description')
    return {'version': data['version'], 'theory_cards': len(data['cards']), 'teaching_entries': sum('teaching' in c for c in data['cards']), 'source_records': len(source_ids), 'model_scenarios': len(cases), 'model_coverage_exercises': len(coverage), 'generated_files': len(outputs), 'errors': errors, 'model_evaluation': 'not_run', 'literature_reverification': 'not_run'}


if __name__ == '__main__':
    result = validate()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(bool(result['errors']))
