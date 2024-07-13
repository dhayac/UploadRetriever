# import logging
# import os
# log_dir = "logs"

# if not os.path.exists(log_dir):
#     os.makedirs(log_dir)
# # disable pdfplumber log
# logging.getLogger("pdfplumber").setLevel(logging.WARNING)
# # disable pdfdocument log
# logging.getLogger("pdfdocument").setLevel(logging.WARNING)

# logger = logging.getLogger()
# logger.setLevel(logging.DEBUG)

# formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

# filehandler = logging.FileHandler(os.path.join(log_dir, "app.log"))
# filehandler.setLevel(logging.INFO)
# filehandler.setFormatter(formatter)

# streamhandler = logging.StreamHandler()
# streamhandler.setLevel(logging.DEBUG)
# streamhandler.setFormatter(formatter)
# logger.addHandler(filehandler)
# logger.addHandler(streamhandler)

# def get_logger():
#     return logger

from logging import getLogger, INFO, Formatter, LoggerAdapter, StreamHandler, FileHandler
# from logging.handlers import TimedRotatingFileHandler
import os
import sys

def get_logger(name, level=INFO, file_name=r"D:\fastapi\logs\app.log"):

    if not os.path.exists(file_name):
        os.makedirs(os.path.dirname(file_name), exist_ok=True)
    
    handler = StreamHandler(sys.stdout)
    log_format = " %(levelname)s : %(asctime)-5s %(filename)s:%(lineno)d %(funcName)-5s --> %(message)s"
    formatter = Formatter(log_format)
    handler.setFormatter(formatter)
    filehandler = FileHandler(file_name)
    filehandler.setFormatter(formatter)
    logger = getLogger(name)
    logger.addHandler(handler)
    logger.addHandler(filehandler)
    logger.setLevel(level)
    return logger

class LoggerAdap(LoggerAdapter):
    def process(self,msg,kwargs):
        return '%s' % (msg), kwargs