import inspect
import logging
from pathlib import Path
class Logger:
    def __init__(self):
        self.logger = logging.getLogger("app")

        if not self.logger.handlers:
            self.logger.setLevel(logging.DEBUG)

            handler = logging.StreamHandler()

            formatter = logging.Formatter(
                "%(asctime)s | %(levelname)s | %(layer)s | %(component)s | %(message)s",
                "%Y-%m-%d %H:%M:%S",
            )

            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def _extra(self):
        path = Path(inspect.stack()[2].filename)

        return {
            "layer": path.parent.name,      # db
            "component": path.stem,         # engine
        }

    def debug(self, message):
        self.logger.debug(message, extra=self._extra(), stacklevel=2)

    def info(self, message):
        self.logger.info(message, extra=self._extra(), stacklevel=2)

    def warning(self, message):
        self.logger.warning(message, extra=self._extra(), stacklevel=2)

    def error(self, message):
        self.logger.error(message, extra=self._extra(), stacklevel=2)

    def critical(self, message):
        self.logger.critical(message, extra=self._extra(), stacklevel=2)


logger = Logger()