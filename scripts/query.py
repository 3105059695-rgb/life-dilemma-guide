"""Local keyword candidates or exact card lookup; no network, no model inference."""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def search_cards(cards, query):
    query = query.strip().casefold()
    if not query:
        return []
    return [c for c in cards if c['title'].casefold() in query or query in c['title'].casefold() or any(k.casefold() in query or query in k.casefold() for k in c['keywords'])]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--id', type=int, nargs='+')
    group.add_argument('--search')
    parser.add_argument('--full', action='store_true')
    args = parser.parse_args()
    cards = json.loads((ROOT / 'references/knowledge.json').read_text(encoding='utf-8'))['cards']
    if args.id:
        if any(i < 1 or i > 100 for i in args.id):
            parser.error('IDs must be between 1 and 100')
        results = [cards[i - 1] for i in dict.fromkeys(args.id)]
    else:
        results = search_cards(cards, args.search)
        print('关键词候选，需阅读门槛与反证；不代表语义匹配或认知诊断。')
    if not results:
        print('未找到关键词候选；可查 references/INDEX.md 或 routing.md。')
    for card in results:
        if args.full:
            print((ROOT / f"references/theories/{card['id']:03d}.md").read_text(encoding='utf-8'))
        else:
            print(f"{card['id']:03d} {card['title']} [{card['mode']}; 标准入口 {card['canonical_id']:03d}] — {card['teaching']['learning_goal']}")


if __name__ == '__main__':
    main()
