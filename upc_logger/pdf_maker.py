import barcode
import io
import json
import logging
import os
import requests
import time
from PIL import Image, ImageOps, ImageChops
from textwrap import wrap
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader



##
LOG_FILE_PATH = os.path.join( os.path.dirname(__file__), 'upc_logger.log' )

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('\n%(asctime)s - [MODULE] %(module)s - [LINE] %(lineno)d - [MSG] %(message)s')
file_handler = logging.FileHandler(LOG_FILE_PATH)
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)
##


PDF_TITLE_STRF = '{client_name} order sheet - Crossmark.pdf'
PRODUCT_IMAGES_BASE_DIR = 'upc_logger/data - product images'

UPC_LOOKUP_DATA_FILENAME = '_upc_lookup_data.json'
PRODUCT_NAMES_DATA_FILENAME = 'product_names.json'

ITEM_INFO_GET_URL = 'https://api.upcitemdb.com/prod/trial/lookup?upc={upc_number}'
IMAGE_URL_PREFERENCES = ['target.com', 'target.scene', 'quill.com', 'walmartimages.com', 'unbeatablesale.com', 'officedepot.com', 'neweggimages.com', 'newegg.com']


def create_pdf_with_upcs(full_upcs: list, product_names: list, pdf_path: str, client_name: str):
    pdf_canvas = canvas.Canvas(pdf_path)
    pdf_canvas.setFont("Helvetica", 11)
    # pdf_canvas.setTitle( PDF_TITLE_STRF.format(client_name=client_name.upper()) )
    pdf_canvas.setTitle( f'{client_name.upper()} sheet ({len(full_upcs)}) Crossmark' )

    start_x, start_y = 0, 660
    curr_x, curr_y = start_x, start_y

    max_image_width = 4*cm
    max_image_height = 3*cm
    product_max_width = 3*cm
    product_max_height = 4.5*cm

    product_names_split_list = get_product_names_split_list(product_names)

    writer_options = {
        'module_height': 20,
        'font_size': 10,
        'text_distance': 4.0,
        'write_text': False
    }

    client_logo = get_client_logo(client_name)
    pdf_canvas.drawImage(client_logo, 156, 770, width=10*cm, height=2.1*cm, preserveAspectRatio=True, anchor='c', mask='auto')

    for i, full_upc in enumerate(full_upcs):
        text_height = get_this_rows_text_height(i, product_names_split_list)
        # print(f'Max height: {text_height} ; idx: {i}')

        product_image = get_product_image_bytes(full_upc, client_name)
        if product_image is None:
            logger.info(f'Product image is None for UPC {full_upc}')
            continue

        upc_obj = barcode.get('upc', full_upc, writer=barcode.writer.ImageWriter())
        barcode_image = ImageReader( upc_obj.render(writer_options=writer_options) )

        temp_y = curr_y - 15
        product_name_split: list = product_names_split_list[i]

        # draw string: full_upc
        pdf_canvas.drawString(curr_x + 19, curr_y + 2, full_upc)
        for product_name_line in product_name_split:
            pdf_canvas.drawCentredString(curr_x + 100, temp_y, product_name_line)
            temp_y -= 13
        pdf_canvas.drawImage(barcode_image, curr_x, curr_y + 13, width=max_image_width, height=max_image_height, preserveAspectRatio=True, anchor='sw')
        pdf_canvas.drawImage(product_image, curr_x + 105, curr_y, width=product_max_width, height=product_max_height - 1*cm, preserveAspectRatio=True, anchor='s')

        # curr_x += 280
        curr_x += max_image_width + product_max_width
        if curr_x >= 500:
            curr_x = start_x
            # curr_y -= 160
            # print(f'Max image height: {max_image_height}')
            curr_y -= text_height + 35 + max_image_height
        if curr_y < 40:
            curr_x = start_x
            curr_y = start_y + 50
            pdf_canvas.showPage()

    pdf_canvas.save()


def get_product_image_bytes(upc: str, client_name: str) -> object:
    upc_image_file_path = os.path.join(PRODUCT_IMAGES_BASE_DIR, client_name.upper(), upc + '.jpg')
    if os.path.isfile(upc_image_file_path):
        with open(upc_image_file_path, 'rb') as fd:
            return ImageReader(io.BytesIO( fd.read() ))

    product_image_url = get_product_image_url(upc)
    if product_image_url is None:
        return get_image_not_available_image()

    logger.info(f'Downloading "{upc}" product image "{product_image_url}"')
    try:
        resp = requests.get(product_image_url)
        # product_image = ImageReader(io.BytesIO(resp.content))
        product_image = Image.open(io.BytesIO(resp.content))
        product_image = resize_and_trim_image(product_image)
        if product_image is None:
            return get_image_not_available_image()
        product_image.save(upc_image_file_path, 'JPEG')

        product_image = ImageReader(product_image)

        logger.info(f'Resized {upc} product image from url: {product_image_url}')

    except Exception as e:
        logger.exception(f'  >! Exception occurred: {e}')
        return get_image_not_available_image()

    # with open(upc_image_file_path, 'wb') as fd:
    #     fd.write(resp.content)

    return product_image


def get_product_image_url(upc: str) -> str:
    '''
    Get image url from json lookup data
    :param upc str: 12-digit UPC number
    :rtype str: return url for image obtained from json lookup data
    '''
    upc_lookup_data_file_path = os.path.join(PRODUCT_IMAGES_BASE_DIR, UPC_LOOKUP_DATA_FILENAME)

    with open(upc_lookup_data_file_path, 'r', encoding='utf8') as fd:
        upc_lookup_data = json.load(fd)

    upc_data = upc_lookup_data.get(upc)
    if upc_data is None:
        return None

    items: list = upc_data.get('items')
    if not items:
        logger.info(f'No "items" data for {upc}')
        return None

    image_urls: list = items[0].get('images')
    if not image_urls:
        logger.info(f'No image URLs found for {upc}')
        return None

    for preference_url in IMAGE_URL_PREFERENCES:
        for image_url in image_urls:
            if preference_url in image_url:
                return image_url

    return image_urls[0]


def lookup_upc_data(full_upcs: list, client_name: str):
    '''
    GETs and saves response json data to file; does not download or process any further data
    :param full_upcs list<str>: list of 12-digit UPC numbers
    :param client_name str: name of client
    '''
    upc_lookup_data_file_path = os.path.join(PRODUCT_IMAGES_BASE_DIR, UPC_LOOKUP_DATA_FILENAME)
    product_images_dir = os.path.join(PRODUCT_IMAGES_BASE_DIR, client_name.upper())

    filenames_in_images_dir = set()
    [filenames_in_images_dir.add( os.path.splitext(f)[0] ) for f in os.listdir(product_images_dir)]

    with open(upc_lookup_data_file_path, 'r', encoding='utf8') as fd:
        upc_lookup_data = json.load(fd)

    upcs_not_existing = [f for f in full_upcs if f not in filenames_in_images_dir and f not in upc_lookup_data]
    n = 2
    pairs_list = [upcs_not_existing[i:i+n] for i in range(0, len(upcs_not_existing), n)]

    for upc_pair in pairs_list:
        upc_lookup_str = ','.join(upc_pair)
        resp = requests.get( ITEM_INFO_GET_URL.format(upc_number=upc_lookup_str) )
        logger.info(f'GETting UPC pair {upc_pair} product info...')

        if resp.ok:
            items = resp.json().get('items')
            if not items:
                logger.info(f'Response json did not have "items" list for {upc_pair}')
                continue
            for upc in upc_pair:
                data = get_upc_data(upc, items)
                if data is None:
                    logger.info(f'get_upc_data returned None for {upc} in {upc_pair}')
                    continue
                upc_lookup_data[upc] = data
        else:
            logger.info(f'Resp not OK for UPC pair {upc_pair}. Resp: {resp.text}')
            break
            # time.sleep(0.5)


    # for full_upc in full_upcs:
    #     if full_upc not in upc_lookup_data and full_upc not in filenames_in_images_dir:
    #         resp = requests.get( ITEM_INFO_GET_URL.format(upc_number=full_upc) )
    #         logger.info(f'GETting {full_upc} product info...')

    #         if resp.ok:
    #             logger.info('OK')
    #             time.sleep(0.2)
    #             data = resp.json()
    #             upc_lookup_data[full_upc] = data
    #         else:
    #             logger.info(f'Resp not OK for UPC {full_upc}. Resp: {resp.text}')
    #             break
    #             # time.sleep(0.5)

    with open(upc_lookup_data_file_path, 'w', encoding='utf8') as fd:
        json.dump(upc_lookup_data, fd, indent=4)

def get_upc_data(upc: str, items: list) -> dict:
    ret = { 'items': [] }
    for item in items:
        if item['upc'] == upc:
            ret['items'].append(item)
            return ret
    return None


def log_product_names(full_upcs: list, product_names: list, client_name: str):
    product_names_file_path = os.path.join(PRODUCT_IMAGES_BASE_DIR, PRODUCT_NAMES_DATA_FILENAME)

    products = {}
    with open(product_names_file_path, 'r', encoding='utf8') as fd:
        products = json.load(fd)

    if client_name.upper() not in products:
        products[client_name.upper()] = {}

    for i, upc in enumerate(full_upcs):
        if upc not in products[client_name.upper()]:
            products[client_name.upper()][upc] = {}
            products[client_name.upper()][upc]['fs_name'] = product_names[i]

    with open(product_names_file_path, 'w', encoding='utf8') as fd:
        json.dump(products, fd, indent=4)


def resize_and_trim_image(img: object) -> object:
    def trim_whitespace(img):
        bg = Image.new(img.mode, img.size, img.getpixel((0,0)))
        diff = ImageChops.difference(img, bg)
        diff = ImageChops.add(diff, diff, 2.0, -100)
        bbox = diff.getbbox()
        if bbox:
            return img.crop(bbox)

        return None

    def make_rgb_and_thumbnail(img):
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        img.thumbnail(size, Image.ANTIALIAS)
        return img

    size = 600, 600
    img = trim_whitespace(img)

    if img is None:
        return None

    img = ImageOps.expand(img, border=10, fill=(255,255,255))
    img = make_rgb_and_thumbnail(img)
    return img


def get_image_not_available_image() -> object:
    image_not_available_path = os.path.join(PRODUCT_IMAGES_BASE_DIR, '_image_not_available.jpg')
    with open(image_not_available_path, 'rb') as fd:
        return ImageReader(io.BytesIO( fd.read() ))


def get_client_logo(client_name: str) -> object:
    client_logo_image_path = os.path.join(PRODUCT_IMAGES_BASE_DIR, client_name + '.png')
    with open(client_logo_image_path, 'rb') as fd:
        return ImageReader(io.BytesIO( fd.read() ))


def get_this_rows_text_height(test_idx: int, product_names_split_list: str) -> int:
    num_rows = 3
    max_nth_relative_idx = num_rows - 1
    nth_relative_idx = test_idx % num_rows

    zeroth_idx = test_idx - nth_relative_idx
    secondth_idx = test_idx + ( max_nth_relative_idx - nth_relative_idx)
    if nth_relative_idx == 0:
        secondth_idx = test_idx + max_nth_relative_idx

    # print('')
    # print(zeroth_idx);print(secondth_idx); print(nth_relative_idx)
    # print('')

    max_length = 1
    for i, name_split in enumerate(product_names_split_list):
        if zeroth_idx <= i and i <= secondth_idx:
            if len(name_split) > max_length:
                max_length = len(name_split)
    return max_length * 13


def get_product_names_split_list(product_names: list) -> list:
    '''
    :param product_names list<str>: list<str> of product names
    :rtype list<list<str>>: list of name splits after wrapping names to fit each line under n number of characters
    '''

    name_split_list = []
    max_length = 32
    for name in product_names:
        product_name_split: list = wrap(name, max_length)[:3]
        name_split_list.append(product_name_split)

    return name_split_list

