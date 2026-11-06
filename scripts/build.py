"""Build cards, indexes, coverage exercises and standalone from maintained sources."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEXT_FIELDS = ('learning_goal', 'before', 'after', 'transfer_question', 'common_misuse')


def load_data(root=ROOT):
    data = json.loads((root / 'references/knowledge.json').read_text(encoding='utf-8'))
    cards = data['cards']
    if [c['id'] for c in cards] != list(range(1, 101)):
        raise ValueError('Cards must have ordered unique IDs 1–100')
    for card in cards:
        if hashlib.sha256(card['body_markdown'].encode('utf-8')).hexdigest() != card['body_sha256']:
            raise ValueError(f"Original body changed: {card['id']}")
        teaching = card['teaching']
        for key in TEXT_FIELDS:
            if not isinstance(teaching[key], str) or not teaching[key].strip():
                raise ValueError(f"Missing teaching field {card['id']}: {key}")
        points = teaching['answer_points']
        if not isinstance(points, list) or not 2 <= len(points) <= 4 or any(not isinstance(p, str) or not p.strip() for p in points):
            raise ValueError(f"Invalid answer points: {card['id']}")
        if not 1 <= card['canonical_id'] <= 100:
            raise ValueError('Invalid canonical ID')
    if cards[86]['canonical_id'] != 77 or cards[98]['canonical_id'] != 99:
        raise ValueError('Duplicate entry mapping changed')
    if any(cards[i - 1]['mode'] != 'lookup_only' for i in (76, 94)):
        raise ValueError('Lookup-only boundary changed')
    return data


def render_card(card):
    t = card['teaching']
    return card['body_markdown'].rstrip() + '\n\n## 教学补充（重建版原创设计）\n\n' + '\n\n'.join([
        '**学习目标**：' + t['learning_goal'],
        '**学会前的常见判断（不代表用户实际想法）**：' + t['before'],
        '**学会后的判断**：' + t['after'],
        '**迁移练习**：' + t['transfer_question'],
        '**答案要点（练习后反馈或按需查看）**：\n' + '\n'.join('- ' + p for p in t['answer_points']),
        '**常见误用**：' + t['common_misuse'],
    ]) + '\n'


def generated_files(root=ROOT):
    data = load_data(root)
    cards = data['cards']
    outputs = {f"references/theories/{c['id']:03d}.md": render_card(c) for c in cards}
    index = ['# 100条编号索引', '', '按名称定位后读取完整卡片。模式为原卡标记，不代表本次完成了科学验证。', '', '| 编号 | 名称 | 使用模式 | 标准入口 |', '| --- | --- | --- | --- |']
    learning = ['# 学习地图', '', '这是候选学习需要；不能据此断言提问者存在认知缺陷。', '', '| 编号 | 理论 | 值得补充的判断能力 |', '| --- | --- | --- |']
    coverage = []
    for c in cards:
        ident = f"{c['id']:03d}"
        index.append(f"| {ident} | [{c['title']}](theories/{ident}.md) | {c['mode']} | {c['canonical_id']:03d} |")
        learning.append(f"| {ident} | [{c['title']}](theories/{ident}.md) | {c['teaching']['learning_goal'].replace('|', '／')} |")
        coverage.append({'id': c['id'], 'theory': c['title'], 'mode': c['mode'], 'prompt': c['teaching']['transfer_question'], 'expected_points': c['teaching']['answer_points'], 'misuse': c['teaching']['common_misuse'], 'status': 'not_run'})
    outputs['references/INDEX.md'] = '\n'.join(index) + '\n'
    outputs['references/learning-map.md'] = '\n'.join(learning) + '\n'
    outputs['tests/coverage.json'] = json.dumps({'description': '100条迁移题，未执行目标模型测评；不是已通过的成绩。', 'cases': coverage}, ensure_ascii=False, indent=2) + '\n'
    skill = (root / 'SKILL.md').read_text(encoding='utf-8').split('---', 2)[-1].strip()
    pieces = [f"# 人生困境 · 认知补全｜普通聊天单文件版\n\n版本：{data['version']}\n\n本文件由v3知识正文重建并补充教学内容，不是原对话v4压缩包。路径指模块版位置；普通聊天中直接定位下文对应标题。无法读取相关内容时明确说明。", skill]
    modules = ['references/teaching.md', 'references/voice.md', 'references/routing.md', 'references/reasoning-and-action.md', 'references/boundaries.md', 'references/corrections.md']
    pieces.extend((root / p).read_text(encoding='utf-8').strip() for p in modules)
    pieces.append(outputs['references/INDEX.md'].strip())
    pieces.append(outputs['references/learning-map.md'].strip())
    pieces.extend(outputs[f"references/theories/{c['id']:03d}.md"].strip() for c in cards)
    pieces.extend((root / p).read_text(encoding='utf-8').strip() for p in ['examples/answers.md', 'references/sources.md'])
    outputs['standalone.txt'] = '\n\n========================================\n\n'.join(pieces) + '\n'
    return outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Check synchronization without writing files')
    args = parser.parse_args()
    outputs = generated_files()
    stale = []
    for rel, content in outputs.items():
        target = ROOT / rel
        actual = target.read_text(encoding='utf-8') if target.is_file() else None
        if actual != content:
            stale.append(rel)
            if not args.check:
                target.parent.mkdir(parents=True, exist_ok=True)
                with target.open('w', encoding='utf-8', newline='\n') as stream:
                    stream.write(content)
    if args.check and stale:
        print('Out of sync:\n' + '\n'.join(stale))
        return 1
    print(f"{'Checked' if args.check else 'Built'} {len(outputs)} generated files; changed: {len(stale)}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
