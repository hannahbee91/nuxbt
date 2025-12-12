import logging
from datetime import datetime


def create_logger(debug=False, log_file_path=None, disable_logging=False):

    logger = logging.getLogger('nuxbt')

    if disable_logging:
        null_handler = logging.NullHandler()
        logger.addHandler(null_handler)
        return logger

    if debug:
        logger.setLevel(logging.DEBUG)

    if log_file_path:
        if log_file_path is True:
             # Default log file path
            log_file_path = f'./nuxbt-{datetime.now().strftime("%Y-%m-%d-%H-%M-%S")}.log'
            
        file_handler = logging.FileHandler(log_file_path)
        file_handler.setFormatter(
            logging.Formatter("[%(asctime)s] %(levelname)s in %(module)s: %(message)s")
        )
        logger.addHandler(file_handler)
    else:
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(
            logging.Formatter("[%(asctime)s] %(levelname)s in %(module)s: %(message)s")
        )
        logger.addHandler(stream_handler)

    return logger
