import logging
from rich.logging import RichHandler
from rich.console import Console
from rich.text import Text
from resources._config import Config


SUCCESS_LEVEL_NUM = 25
logging.addLevelName(SUCCESS_LEVEL_NUM, "SUCCESS")

def success(self, message, *args, **kwargs):
    if self.isEnabledFor(SUCCESS_LEVEL_NUM):
        self._log(SUCCESS_LEVEL_NUM, message, args, **kwargs)


logging.Logger.success = success

class CustomRichHandler(RichHandler):
    def render_message(self, record: logging.LogRecord, message: str) -> Text:
        if record.levelno == SUCCESS_LEVEL_NUM:
            message = f"[bold green]{message}[/bold green]"
        return super().render_message(record, message)

class LoggingHandler:
    def __init__(self):

        config = Config()
        logging_settings = config.get_logging_settings()

        self.log_file_database = logging_settings['log_file_database']
        self.log_file_main = logging_settings['log_file_main']
        self.log_file_functions = logging_settings['log_file_functions']
        self.log_file_client = logging_settings['log_file_client']
        self.log_level = logging_settings['log_level']

        self.console = Console()

        self.logger_database = self.setup_logger('database_logger', self.log_file_database)
        self.logger_main = self.setup_logger('main_logger', self.log_file_main)
        self.logger_functions = self.setup_logger('functions_logger', self.log_file_functions)
        self.logger_client = self.setup_logger('client_logger', self.log_file_client)

    def setup_logger(self, name, log_file, level=None):
        logger = logging.getLogger(name)
        level = level or self.log_level
        logger.setLevel(level)

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)

        file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(file_formatter)

        console_handler = CustomRichHandler(console=self.console, show_time=True, show_level=True, show_path=False, markup=True)
        console_handler.setLevel(level)

        if not logger.handlers:
            logger.addHandler(file_handler)
            logger.addHandler(console_handler)

        return logger

    def get_logger_database(self):
        return self.logger_database

    def get_logger_main(self):
        return self.logger_main

    def get_logger_functions(self):
        return self.logger_functions

    def get_logger_client(self):
        return self.logger_client
    


loggers = LoggingHandler()
main_logger = loggers.get_logger_main()
database_logger = loggers.get_logger_database()
functions_logger = loggers.get_logger_functions()
client_logger = loggers.get_logger_client()