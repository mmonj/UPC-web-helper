import json
import re

ITEM_DUMP = 'item dump.txt'
RESULT_JSON = 'items.json'

ITEM_ATTRIBUTES_RE = r'^(.+?) (\d+) (\d) ([a-z]\d+$)$'

def main():
	with open(ITEM_DUMP, 'r', encoding='utf8') as fd:
		item_dump = fd.read()


	final_dict = {}
	matches = re.finditer(ITEM_ATTRIBUTES_RE, item_dump, flags=re.MULTILINE|re.IGNORECASE)
	for match in matches:
		upc = match.group(2)
		final_dict[upc] = {
			'name': match.group(1), 
			'section': match.group(3), 
			'location': match.group(4)
		}

	with open(RESULT_JSON, 'w', encoding='utf8') as fd:
		json.dump(final_dict, fd, indent=4)

	print('Done!')
	

if __name__ == '__main__':
	main()
