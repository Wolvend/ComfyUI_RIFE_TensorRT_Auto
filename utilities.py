import requests
from tqdm import tqdm
import logging
import os
import sys
import tempfile
import time

class ColoredLogger:
    COLORS = {
        'RED': '\033[91m',
        'GREEN': '\033[92m',
        'YELLOW': '\033[93m',
        'BLUE': '\033[94m',
        'MAGENTA': '\033[95m',
        'RESET': '\033[0m'
    }

    LEVEL_COLORS = {
        'DEBUG': COLORS['BLUE'],
        'INFO': COLORS['GREEN'],
        'WARNING': COLORS['YELLOW'],
        'ERROR': COLORS['RED'],
        'CRITICAL': COLORS['MAGENTA']
    }

    def __init__(self, name="MY-APP"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        self.app_name = name

        # Prevent message propagation to parent loggers
        self.logger.propagate = False

        # Clear existing handlers
        self.logger.handlers = []

        # Create console handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)

        # Custom formatter class to handle colored components
        class ColoredFormatter(logging.Formatter):
            def format(self, record):
                # Color the level name according to severity
                level_color = ColoredLogger.LEVEL_COLORS.get(record.levelname, '')
                colored_levelname = f"{level_color}{record.levelname}{ColoredLogger.COLORS['RESET']}"

                # Color the logger name in blue
                colored_name = f"{ColoredLogger.COLORS['BLUE']}{record.name}{ColoredLogger.COLORS['RESET']}"

                # Set the colored components
                record.levelname = colored_levelname
                record.name = colored_name

                return super().format(record)

        # Create formatter with the new format
        formatter = ColoredFormatter('[%(name)s|%(levelname)s] - %(message)s')
        handler.setFormatter(formatter)

        self.logger.addHandler(handler)


    def debug(self, message):
        self.logger.debug(f"{self.COLORS['BLUE']}{message}{self.COLORS['RESET']}")

    def info(self, message):
        self.logger.info(f"{self.COLORS['GREEN']}{message}{self.COLORS['RESET']}")

    def warning(self, message):
        self.logger.warning(f"{self.COLORS['YELLOW']}{message}{self.COLORS['RESET']}")

    def error(self, message):
        self.logger.error(f"{self.COLORS['RED']}{message}{self.COLORS['RESET']}")

    def critical(self, message):
        self.logger.critical(f"{self.COLORS['MAGENTA']}{message}{self.COLORS['RESET']}")

def download_file(
    url,
    save_path,
    *,
    timeout=30,
    max_size_bytes=2 * 1024 * 1024 * 1024,
    retries=3,
    backoff_seconds=1.0,
):
    """
    Download a file from URL with progress bar

    Args:
        url (str): URL of the file to download
        save_path (str): Path to save the file as
    """
    GREEN = '\033[92m'
    RESET = '\033[0m'
    attempt = 0
    while True:
        try:
            response = requests.get(url, stream=True, timeout=timeout)
            response.raise_for_status()
            total_size = int(response.headers.get('content-length', 0))

            # If the server tells us the size and it's too big, bail early.
            if total_size and total_size > max_size_bytes:
                raise ValueError(f"Download too large ({total_size} bytes) for {url}")

            os.makedirs(os.path.dirname(save_path) or '.', exist_ok=True)
            with tempfile.NamedTemporaryFile(delete=False, dir=os.path.dirname(save_path) or '.') as tmp_file, tqdm(
                desc=save_path,
                total=total_size if total_size else None,
                unit='iB',
                unit_scale=True,
                unit_divisor=1024,
                colour='green',
                bar_format=f'{GREEN}{{l_bar}}{{bar}}{RESET}{GREEN}{{r_bar}}{RESET}'
            ) as progress_bar:
                bytes_written = 0
                for data in response.iter_content(chunk_size=1024 * 1024):
                    if not data:
                        continue
                    bytes_written += len(data)
                    if bytes_written > max_size_bytes:
                        tmp_path = tmp_file.name
                        tmp_file.close()
                        os.remove(tmp_path)
                        raise ValueError(f"Download exceeded max size ({max_size_bytes} bytes) for {url}")
                    tmp_file.write(data)
                    progress_bar.update(len(data))

            os.replace(tmp_file.name, save_path)
            return save_path
        except Exception as exc:  # noqa: BLE001
            attempt += 1
            if attempt > retries:
                raise
            # lightweight backoff
            time.sleep(backoff_seconds * attempt)
