import logging
import os
from pathlib import Path


DEFAULT_LOG_LEVEL = os.getenv("LHD_LOG_LEVEL", "INFO").upper()
LOG_FILE = os.getenv("LHD_LOG_FILE", "logs/diagnostic.log")


def get_logger(name: str = "linux_hardware_diagnostic") -> logging.Logger:
	"""Return a configured logger instance shared across the project."""
	logger = logging.getLogger(name)
	if logger.handlers:
		return logger

	logger.setLevel(getattr(logging, DEFAULT_LOG_LEVEL, logging.INFO))

	formatter = logging.Formatter(
		"%(asctime)s | %(levelname)s | %(name)s | %(message)s",
		datefmt="%Y-%m-%d %H:%M:%S",
	)

	stream_handler = logging.StreamHandler()
	stream_handler.setFormatter(formatter)
	logger.addHandler(stream_handler)

	log_path = Path(LOG_FILE)
	log_path.parent.mkdir(parents=True, exist_ok=True)
	file_handler = logging.FileHandler(log_path)
	file_handler.setFormatter(formatter)
	logger.addHandler(file_handler)

	logger.propagate = False
	return logger

