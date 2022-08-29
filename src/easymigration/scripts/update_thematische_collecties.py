import sys
import csv
import requests
import logging
import urllib.parse
from easymigration.config import init

EASY_API = "http://deasy.dans.knaw.nl:8080/"
JUMP_OF_ID = EASY_API + "fedora/risearch"
JUMP_OFF_CONTENT = EASY_API + "fedora/objects/{}/datastreams/{}/content"


def update_thematische_collecties():
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
            # TODO replace row[5] by using row[1] in fedora risearch:
            #  PREFIX dans: <http://dans.knaw.nl/ontologies/relations#> SELECT ?s WHERE {?s dans:isJumpoffPageFor <info:fedora/easy-dataset:13> . }
            #  https://stackoverflow.com/questions/56727817/how-to-send-form-data-using-python-requests
            logging.debug("{} {}".format(value, row[5]))
            row[4] = add_members(row[5])
        csv_writer.writerow(row)


def add_members(jumpoff_id):

    mu = get_jumpoff(jumpoff_id, "HTML_MU")
    if mu.status_code == 404:
        mu = get_jumpoff(jumpoff_id, "TXT_MU")
    if 200 == mu.status_code:
        return parse_jumpoff(jumpoff_id, mu.text)
    else:
        logging.error("jumpoff not found {} {}".format(jumpoff_id, mu.status_code))
        return " "
    #     https://www.thepythoncode.com/article/extract-all-website-links-python
    # "<body><a href='http://x.y.nl'>blabla</a>blabla</body>"


def get_jumpoff(id, format):
    req = JUMP_OFF_CONTENT.format(id, format)
    response = requests.get(req)
    logging.debug("status code: {} req: {}".format(response.status_code, req))
    return response


def parse_jumpoff (jumpoff_id, jumpoff_page):
    # members: "easy-dataset:34099, easy-dataset:57698"
    logging.debug("whoops, parsing not yet implemented {} {}".format(jumpoff_id, jumpoff_page))
    result_links = ["blabla", jumpoff_id, "rabarbera"]
    return ",".join(result_links).replace("[]", "\"")


def main():
    config = init()
    update_thematische_collecties()


if __name__ == '__main__':
    main()
