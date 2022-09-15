def non_empty_lines(file_content):
    # Note that f.readlines() would miss the last 'line' if it has no newline character
    # trim whitespace and remove empty lines...
    return list(filter(lambda item: item.strip(), file_content.splitlines()))
