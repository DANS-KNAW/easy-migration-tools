def load_pids(file_path):
    # should read from a text file, with each line contains a pid
    pids = []
    with open(file_path) as f:
        pids = f.read().splitlines()
        # Note that f.readlines() would miss the last 'line' if it has no newline character
    # trim whitespace and remove empty lines...
    return list(filter(lambda item: item.strip(), pids))
