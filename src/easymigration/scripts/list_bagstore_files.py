# given a doi, retrieve the uuid and subsequently the files from the bag-store

import argparse
import csv
import logging
import sys

import requests
from xml.dom import minidom
from easymigration.batch_processing import batch_process
from easymigration.config import init
from easymigration.pids_handling import non_empty_lines


def find_files(uuid, dark_archive, csv_writer):
    logging.debug(uuid)
    store_url = dark_archive["store_url"]
    metadata_url = f"{store_url}/bags/{uuid}/metadata"
    files_xml = get_file(f"{metadata_url}/files.xml")
    if files_xml:
        ddm = get_file(f"{metadata_url}/dataset.xml")
        if ddm:
            doi = find_doi(ddm)
            if doi:
                parse_files_xml(uuid, doi, files_xml, csv_writer)
            else:
                logging.error(f"No DOI found for {uuid}")


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


def find_doi(ddm):
    identifier_items = minidom.parseString(ddm).getElementsByTagNameNS("http://purl.org/dc/terms/", "identifier")
    for elem in identifier_items:
        id_type = elem.getAttributeNS("http://www.w3.org/2001/XMLSchema-instance", "type")
        logging.debug(f"type = {id_type}")
        if id_type == "id-type:DOI":
            return elem.firstChild.nodeValue
    return ""


def parse_files_xml(uuid, doi, files_xml, csv_writer):
    file_items = minidom.parseString(files_xml).getElementsByTagName("file")
    for elem in file_items:
        access = elem.getElementsByTagName("accessibleToRights")
        access_text = ""
        if access is not None and len(access) == 1:
            access_text = access[0].firstChild.nodeValue
        row = {"uuid": uuid, "doi": doi, "path": elem.attributes["filepath"].value, "accessCategory": access_text}
        csv_writer.writerow(row)


def main():
    config = init()
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="For each doi, list the files in the bag-store"
    )
    parser.add_argument("-p", dest="pid",
                        help="UUID of a bag for which to find the files. "
                             "When omitted, UUIDs are read from stdin.")
    args = parser.parse_args()

    dark_archive = config["dark_archive"]

    fieldnames = {"uuid", "doi", "path", "accessCategory"}
    csv_writer = csv.DictWriter(sys.stdout, delimiter=",", fieldnames=fieldnames)
    csv_writer.writeheader()

    if args.pid is not None:
        find_files(args.pid, dark_archive, csv_writer)
    else:
        pids = non_empty_lines(sys.stdin.read())
        batch_process(pids,
                      lambda pid: find_files(pid, dark_archive, csv_writer))


if __name__ == "__main__":
    main()
