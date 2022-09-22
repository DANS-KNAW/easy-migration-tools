import time
import logging


def batch_process(pids, process_action_func, delay=0.1, fail_on_first_error=True):

    num_pids = len(pids)
    logging.info("Start batch processing on {} datasets".format(num_pids))
    num = 0
    for pid in pids:
        num += 1
        logging.info("[{} of {}] Processing dataset with pid: {}".format(num, num_pids, pid))
        try:
            process_action_func(pid)
        except Exception as e:
            logging.exception("Exception occurred", exc_info=True)
            if fail_on_first_error:
                logging.error("Stop processing because of an exception:  {}".format(e))
                break
            logging.debug("fail_on_first_error is False, continuing...")
        if delay > 0 and num < num_pids:
            logging.debug("Sleeping for {} seconds...".format(delay))
            time.sleep(delay)
    logging.info("Done processing {} out of {} datasets".format(num, num_pids))
