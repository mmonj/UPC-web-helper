#!python3

import json
import os
import re

# DUMP_FORMAT_RE = r'item dump_(T\d+.*)\.\w+'
ITEM_ATTRIBUTES_RE = r'(.+?)[ \t]+(\d{12})(?:[ \t]+\d)?[ \t]+([a-z]\d+)'

DUMP_FOLDER = 'item dumps'
ITEMS_JSON_FILE = 'items.json'


def main():
    dump_files = (os.path.join(DUMP_FOLDER, f) for f in os.listdir(DUMP_FOLDER))

    with open(ITEMS_JSON_FILE, 'r', encoding='utf8') as fd:
        old_all_items = json.load(fd)
    
    all_items = {}
    for file in dump_files:
        basename = os.path.basename(file)
        store_name = os.path.splitext(basename)[0]
        # store_number = re.search(DUMP_FORMAT_RE, file).group(1)

        items = _parse_items(file)
        all_items[store_name] = {}
        all_items[store_name].update(items)

        print(f'{store_name:<20}: {len(items)} items')

    print('')
    compare_items(old_all_items, all_items)

    with open(ITEMS_JSON_FILE, 'w', encoding='utf8') as fd:
        json.dump(all_items, fd, indent=4)


def compare_items(old_all_items: dict, all_items: dict):
    for store in old_all_items:
        print_differences(store, old_all_items, all_items)


def print_differences(store: str, old_all_items: dict, all_items: dict):
    if all_items.get(store) is None:
        return

    counter = 0

    for upc, item_info in all_items[store].items():
        location = item_info['location']

        old_upc = old_all_items[store].get(upc)
        if old_upc is None:
            continue

        old_location = old_all_items[store][upc]['location']

        if location != old_location:
            counter += 1

    print(f'{store:<20}: {counter}/{len(all_items[store])} items have moved locations')


def _parse_items(file: str) -> dict:
    with open(file, 'r', encoding='utf8') as fd:
        contents = fd.read()

    items = {}

    matches = re.finditer(ITEM_ATTRIBUTES_RE, contents, re.MULTILINE|re.IGNORECASE)

    for match in matches:
        name = match.group(1).strip()
        upc = match.group(2)
        location = match.group(3)


        item = {
            upc: {
                'name': name,
                'location': location
            }
        }

        items.update(item)

    return items


if __name__ == '__main__':
    main()
