# noinspection PyUnresolvedReferences
"""Initiates a custom logger to be accessed across modules.

>>> CustomLogger

Disables loggers from imported modules, while using the root logger without having to load an external file.

"""

import importlib
import logging
import os
import time
from datetime import datetime
from logging.config import dictConfig
from multiprocessing import current_process
from typing import Union

from pytz import timezone, utc

from modules.models import models

api_logs = os.path.join('logs', 'api')
if not os.path.isdir(api_logs):
    os.makedirs(api_logs)  # Recursively creates both logs and api directories if unavailable

log_format = logging.Formatter(fmt='%(asctime)s - %(levelname)s - [%(module)s:%(lineno)d] - %(funcName)s - %(message)s',
                               datefmt='%b-%d-%Y %I:%M:%S %p')


def log_file() -> str:
    """Creates a log file and writes the headers into it.

    Returns:
        str:
        Log filename.
    """
    filename = datetime.now().strftime(os.path.join('logs', 'jarvis_%d-%m-%Y.log'))
    write = ''.join(['*' for _ in range(120)])
    if current_process().name == 'MainProcess':
        with open(filename, 'a+') as file:
            file.seek(0)
            if not file.read():
                file.write(f"{write}\n")
            else:
                file.write(f"\n{write}\n")
    return filename


def custom_handler() -> logging.FileHandler:
    """Creates a FileHandler, sets the log format and returns it.

    Returns:
        logging.FileHandler:
        Returns file handler.
    """
    handler = logging.FileHandler(filename=log_file(), mode='a')
    handler.setFormatter(fmt=log_format)
    return handler


importlib.reload(module=logging)
dictConfig({
    'version': 1,
    'disable_existing_loggers': True,
})
if not models.settings.macos:
    logging.getLogger("_code_cache").propagate = False

logger = logging.getLogger('jarvis')
logger.addHandler(hdlr=custom_handler())
logger.setLevel(level=logging.INFO)


class TestLogger:
    """This is a class to test logger to verify logging using module references and different logging levels.

    Logging works the same way regardless of callable method, static method, function or class.

    >>> TestLogger

    """

    def __init__(self):
        """Instantiates logger to self.logger which is used by the function methods."""
        self.logger = logger

    # noinspection PyUnresolvedReferences,PyProtectedMember
    def test_log(self) -> None:
        """Logs the caller function with a custom time."""
        logging.Formatter.converter = self.custom_time
        self.logger.error(sys._getframe(0).f_code.co_name)
        called_func = sys._getframe(1).f_code.co_name.replace("<module>", __name__)
        parent_func = sys._getframe(2).f_code.co_name.replace("<module>", __name__) if not called_func == '__main__' \
            else None
        self.logger.critical(f'I was called by {called_func} which was called by {parent_func}')
        self.logger.critical("I'm a special function as I use custom timezone, overriding logging.formatTime() method.")

    # noinspection PyUnusedLocal
    @staticmethod
    def custom_time(*args: Union[logging.Formatter, time.time]) -> time.struct_time:
        """Creates custom timezone for ``logging`` which gets used only when invoked by ``Docker``.

        This is used only when triggered within a ``docker container`` as it uses UTC timezone.

        Args:
            *args: Takes ``Formatter`` object and current epoch as arguments passed by ``formatTime`` from ``logging``.

        Returns:
            struct_time:
            A struct_time object which is a tuple of:
            **current year, month, day, hour, minute, second, weekday, year day and dst** *(Daylight Saving Time)*
        """
        utc_dt = utc.localize(datetime.utcnow())
        my_tz = timezone("US/Eastern")
        converted = utc_dt.astimezone(my_tz)
        return converted.timetuple()


if __name__ == '__main__':
    import sys

    test_logger = TestLogger()
    test_logger.test_log()
    for method_name, return_value in TestLogger.__dict__.items():
        if callable(return_value):
            print(method_name)
