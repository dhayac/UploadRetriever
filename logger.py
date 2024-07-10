import logging
import os
log_dir = "logs"

if not os.path.exists(log_dir):
    os.makedirs(log_dir)

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

filehandler = logging.FileHandler(os.path.join(log_dir, "app.log"))
filehandler.setLevel(logging.INFO)
filehandler.setFormatter(formatter)

streamhandler = logging.StreamHandler()
streamhandler.setLevel(logging.DEBUG)
streamhandler.setFormatter(formatter)
logger.addHandler(filehandler)
logger.addHandler(streamhandler)

def get_logger():
    return logger