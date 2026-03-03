# velvet/core/__main__.py
from __future__ import annotations

import logging
from velvet.core.runtime import VelvetRuntime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

print("Velvet Core diagnostic mode starting...")

VelvetRuntime().run_forever()
