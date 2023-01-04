from fastapi import Depends
import logging
from config import Settings, get_settings


class Logger:
    PADDING = '\t'

    def __init__(self, settings: Settings = Depends(get_settings)):
        self.settings = settings
        self.logger = logging.getLogger('uvicorn')
        self.set_level(settings.log_level.value.upper())
        self.source = __name__

    def set_level(self, level):
        self.logger.setLevel(level)

    # TODO: It seems that the logger instance is shared across all the services
    # so the source is always the same.
    def set_source(self, source):
        self.source = source

    def debug(self, message):
        self.logger.debug(f'[{self.source}]:{self.PADDING}{message}')

    def info(self, message):
        self.logger.info(f'[{self.source}]:{self.PADDING}{message}')

    def warning(self, message):
        self.logger.warning(f'[{self.source}]:{self.PADDING}{message}')

    def error(self, message):
        self.logger.error(f'[{self.source}]:{self.PADDING}{message}')

    def critical(self, message):
        self.logger.critical(f'[{self.source}]:{self.PADDING}{message}')