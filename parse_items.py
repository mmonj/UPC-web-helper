#!python3

import json
import os
import re

DUMP_FORMAT_RE = r'item dump_(T\d+)\.\w+'
ITEM_ATTRIBUTES_RE = r'(.+) (\d{12})(?: \d)? ([a-z]\d+)'

OUTPUT_FILE = 'items.json'


def main():
    dump_files = (f for f in os.listdir('./') if f.startswith('item dump_'))
    
    all_store_items = {}
    for file in dump_files:
        store_number = re.search(DUMP_FORMAT_RE, file).group(1)

        items = _parse_items(file)
        all_store_items[store_number] = {}
        all_store_items[store_number].update(items)


    with open(OUTPUT_FILE, 'w', encoding='utf8') as fd:
        json.dump(all_store_items, fd, indent=4)




def _parse_items(file):
    with open(file, 'r', encoding='utf8') as fd:
        contents = fd.read()

    items = {}

    matches = re.finditer(ITEM_ATTRIBUTES_RE, contents, re.MULTILINE|re.IGNORECASE)

    for match in matches:
        name = match.group(1)
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
