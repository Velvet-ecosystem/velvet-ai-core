# velvet/core/logger.py
"""
Simple logging wrapper for Velvet Core.

Provides a standard logger instance that modules can import.
Uses Python's stdlib logging module.
"""

import logging

# Create the main Velvet logger
logger = logging.getLogger("velvet")

# Set default level (can be overridden by runtime or config)
logger.setLevel(logging.INFO)

# Add a default handler if none exists (prevents "No handlers" warnings)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
