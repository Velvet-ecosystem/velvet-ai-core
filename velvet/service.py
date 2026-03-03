# velvet/service.py
from __future__ import annotations

import logging
import os
from pathlib import Path

from velvet.core.runtime import VelvetRuntime

log = logging.getLogger("velvet.service")


def _setup_logging() -> None:
    # systemd sets WorkingDirectory to the state dir (%S/velvet),
    # so write logs relative to where the service is running.
    log_dir = Path.cwd()
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "velvet.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(str(log_path)),
            logging.StreamHandler(),
        ],
    )

    try:
        os.chmod(log_path, 0o644)
    except Exception:
        pass


def main() -> int:
    _setup_logging()
    log.info("Velvet service booted (systemd entrypoint OK).")

    rt = VelvetRuntime()
    rt.run_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
