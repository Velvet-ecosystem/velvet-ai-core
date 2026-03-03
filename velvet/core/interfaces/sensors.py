# velvet/core/interfaces/sensors.py
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict


class SensorInterface(ABC):
    """
    Abstract interface for environmental and body sensors.
    """

    @abstractmethod
    def read_all(self) -> Dict[str, float]:
        """Return a dict of sensor_name -> value"""
        raise NotImplementedError
