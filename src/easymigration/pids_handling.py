from sys import stdin

from easymigration.batch_processing import batch_process


def non_empty_lines(file_content):
    # Note that readlines() would miss the last 'line' if it has no newline character
    # trim whitespace and remove empty lines...
    return list(filter(lambda item: item.strip(), file_content.splitlines()))


def load_pids(file_path):
    # should read from a text file, with each line contains a pid
    if file_path == "-":
        pids = stdin.read()
    else:
        pids = open(file_path).read()
    return non_empty_lines(pids)


def add_pid_args(parser):
    pids = parser.add_mutually_exclusive_group(required=True)
    pids.add_argument('-p', '--pid', dest='pid',
                      help='The ID of a single dataset')
    pids.add_argument('-d', '--datasets', dest='pid_file',
                      help='Newline separated file with dataset IDs, "-" is stdin')


def process_pids(args, process_action_func, delay=0.1, fail_on_first_error=True):
    if args.pid is not None:
        process_action_func(args.pid)
    elif args.pid_file is not None:
        batch_process(load_pids(args.pid_file),
                      lambda pid: process_action_func(pid),
                      delay,
                      fail_on_first_error)
    else:
        raise Exception("Programming error: ArgumentParser did not require exactly one of the 'dest'-s  "
                        "'pid' or 'pid_file', please call add_pid_args or an equivalent")
