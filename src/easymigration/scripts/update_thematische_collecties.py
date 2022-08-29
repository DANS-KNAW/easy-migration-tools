import sys
import csv
import requests
import logging
import argparse
import urllib.parse
from easymigration.config import init

EASY_API = "http://deasy.dans.knaw.nl:8080/"
JUMP_OF_ID = EASY_API + "fedora/risearch"
JUMP_OFF_CONTENT = "{}:8080/fedora/objects/{}/datastreams/{}/content"


def update_thematische_collecties(base_url):
    """
     Copies a Thematische-Collecties.csv from stdin to stdout.
     Assumed columns: -,EASY-dataset-id,-,-,members,jumpoff-id
     Empty members columns are filled by crawling jump of pages.
     jumpoff-id is for temporal testing purposes

        Example: update_thematische_collecties.py  < OldThemCol.csv > NewThemCol.csv
    """

    csv_reader = csv.reader(sys.stdin, delimiter=',')
    csv_writer = csv.writer(sys.stdout, delimiter=',')
    for row in csv_reader:
        # columns: name,EASY-dataset-id,type,comment,members
        value = row[4].strip()
        if not ("easy-dataset" in value or "members" in value):
            # TODO replace row[5] by feeding row[1] to fedora risearch:
            #  PREFIX dans: <http://dans.knaw.nl/ontologies/relations#> SELECT ?s WHERE {?s dans:isJumpoffPageFor <info:fedora/easy-dataset:13> . }
            #  https://stackoverflow.com/questions/56727817/how-to-send-form-data-using-python-requests
            logging.debug("{} {}".format(value, row[5]))
            row[4] = get_members(row[5], base_url)
        csv_writer.writerow(row)


def get_members(jumpoff_id, base_url):
    try:
        mu = get_jumpoff(jumpoff_id, "HTML_MU", base_url)
        if mu.status_code == 404:
            mu = get_jumpoff(jumpoff_id, "TXT_MU", base_url)
    except Exception as e:
        logging.error("{}".format(e))
        return ""
    if 200 == mu.status_code:
        return parse_jumpoff(jumpoff_id, mu.text)
    else:
        logging.error("jumpoff not found {} {}".format(jumpoff_id, mu.status_code))
        return ""
    #     https://www.thepythoncode.com/article/extract-all-website-links-python
    # "<body><a href='http://x.y.nl'>blabla</a>blabla</body>"


def get_jumpoff(jumpof_id, format, base_url):
    req = JUMP_OFF_CONTENT.format(base_url, jumpof_id, format)
    response = requests.get(req)
    logging.debug("status code: {} req: {}".format(response.status_code, req))
    return response


def parse_jumpoff(jumpoff_id, jumpoff_page):
    # members: "easy-dataset:34099, easy-dataset:57698"
    logging.debug("whoops, parsing not yet implemented {} {}".format(jumpoff_id, jumpoff_page))
    result_links = ["blabla", jumpoff_id, "rabarbera"]
    return ",".join(result_links).replace("[]", "\"")


def main():
    config = init()
    parser = argparse.ArgumentParser(
        description='Copies a Thematische-Collecties.csv from stdin to stdout. '
                    'Empty member fields will be filled in by collecting links from the jumpoff page of the dataset. ',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('-b', '--base_url', default='http://deasy.dans.knaw.nl', help='The host with the fedora DB')
    args = parser.parse_args()
    update_thematische_collecties(args.base_url)


if __name__ == '__main__':
    main()
