from sys import stdin

from easymigration.batch_processing import batch_process

def non_empty_lines(file_content):
    # Note that f.readlines() would miss the last 'line' if it has no newline character
    # trim whitespace and remove empty lines...
    return list(filter(lambda item: item.strip(), file_content.splitlines()))


def load_pids(file_path):
    # should read from a text file, with each line contains a pid
    # Note that readlines() would miss the last 'line' if it has no newline character
    pids = []
    if file_path == "-":
        pids = stdin.read()
    else:
        pids = open(file_path).read()
    return non_empty_lines(pids)


def add_pid_args(parser):
    pid_or_file = parser.add_mutually_exclusive_group()
    pid_or_file.add_argument('-p', '--pid', dest='pid',
                             help='The pid of a dataset.')
    pid_or_file.add_argument('-d', '--datasets', dest='pid_file',
                             help='The input file with the dataset pids (UUIDs)')
