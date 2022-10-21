# given a UUID, retrieve the DOI and subsequently the files from the bag-store

import argparse
import csv
import logging
import sys
from xml.dom import minidom

import requests

from easymigration.config import init
from easymigration.pids_handling import add_pid_args, process_pids


def find_files(bag_store_url, uuid, csv_writer):
    logging.debug(uuid)
    metadata_url = f"{bag_store_url}/bags/{uuid}/metadata"
    files_xml = get_file(f"{metadata_url}/files.xml")
    ddm_xml = get_file(f"{metadata_url}/dataset.xml")
    if files_xml and ddm_xml:
        try:
            parse_files_xml(uuid, find_ids(ddm_xml), files_xml, csv_writer, find_rights(ddm_xml))
        except Exception as e:
            logging.error(f"{uuid} FAILED: {e}")


def get_file(url):
    logging.debug(url)
    response = requests.get(url)
    if response.status_code == 410 or response.status_code == 404:
        logging.error(f"Not found {response.status_code} : {url}")
        return ""
    elif response.status_code != 200:
        raise Exception(f"status {response.status_code} : {url}")
    else:
        return response.text


def find_ids(ddm):
    ns = "http://purl.org/dc/terms/"
    items = minidom.parseString(ddm).getElementsByTagNameNS(ns, "identifier")
    id_strings = sorted(map(child_value, filter(is_id, items)))
    if len(id_strings) == 2:
        return id_strings
    else:
        logging.error(f"Expecting [DOI,easy-dataset:NN]. Found {','.join(id_strings)}")
        return ["", ""]


def find_rights(ddm):
    ns = "http://easy.dans.knaw.nl/schemas/md/ddm/"
    items = minidom.parseString(ddm).getElementsByTagNameNS(ns, "accessRights")
    m = {'ANONYMOUS_ACCESS': 'ANONYMOUS',
         'OPEN_ACCESS_FOR_REGISTERED_USERS': 'KNOWN',
         'GROUP_ACCESS': 'RESTRICTED_GROUP',
         'REQUEST_PERMISSION': 'RESTRICTED_REQUEST',
         'OPEN_ACCESS': 'ANONYMOUS',
         'NO_ACCESS': 'RESTRICTED',
         }
    return m[child_value(items[0])]


def child_value(elem):
    return elem.firstChild.nodeValue


def is_id(id_elem):
    ns = "http://www.w3.org/2001/XMLSchema-instance"
    is_dataset_id = child_value(id_elem).startswith('easy-dataset:')
    return is_dataset_id or id_elem.getAttributeNS(ns, "type") == "id-type:DOI"


def parse_files_xml(uuid, ids, files_xml, csv_writer, rights):
    logging.debug(rights)
    file_items = minidom.parseString(files_xml).getElementsByTagName("file")
    for elem in file_items:
        access = elem.getElementsByTagName("accessibleToRights")
        if access is not None and len(access) == 1:
            rights = access[0].firstChild.nodeValue
        row = {"uuid": uuid,
               "doi": ids[0],
               "dataset_id": ids[1],
               "path": elem.attributes["filepath"].value,
               "accessible_to_rights": rights
               }
        csv_writer.writerow(row)


def create_csv():
    fieldnames = ["uuid", "doi", "dataset_id", "path", "accessible_to_rights"]
    csv_writer = csv.DictWriter(sys.stdout, delimiter=",", fieldnames=fieldnames)
    csv_writer.writeheader()
    return csv_writer


def main():
    config = init()
    bag_store_url = config["dark_archive"]["store_url"]

    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="For each dataset (identified with a UUID), list the files in the bag-store"
    )
    add_pid_args(parser)
    args = parser.parse_args()
    csv_writer = create_csv()  # after parsing CLI to avoid output on --help
    process_pids(args, lambda pid: find_files(bag_store_url, pid, csv_writer))


if __name__ == "__main__":
    main()
