import logging
import os

def setup_logging():
    level = logging.INFO
    log_dir = os.path.join(os.getcwd(), 'logs')
    log_file = os.path.join(log_dir, 'webapp.log')

    # File handler for logging to a file
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(logging.Formatter(
        '[%(asctime)s][%(levelname)s][%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))

    # Set up root logger with both handlers
    root = logging.getLogger()
    root.setLevel(level)
    root.handlers = [file_handler]

    # Silence invasive log
    logging.getLogger("elasticsearch").setLevel(logging.WARNING)
    logging.getLogger("elastic_transport").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)