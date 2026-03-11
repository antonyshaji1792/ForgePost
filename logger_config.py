from loguru import logger
import sys

# Configure logger
logger.remove()
logger.add(sys.stdout, format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}")
logger.add("app.log", rotation="10 MB", format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}", encoding="utf-8")

def get_logger():
    return logger
