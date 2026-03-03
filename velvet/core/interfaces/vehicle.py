# velvet/core/interfaces/vehicle.py
from __future__ import annotations
from abc import ABC, abstractmethod


class VehicleInterface(ABC):
    """
    Abstract interface for vehicle control.
    CAN bus, Speeduino, OEM ECU, simulator — all implement this.
    """

    @abstractmethod
    def get_speed(self) -> float:
        """Return vehicle speed in km/h"""
        raise NotImplementedError

    @abstractmethod
    def get_rpm(self) -> float:
        """Return engine RPM"""
        raise NotImplementedError

    @abstractmethod
    def set_throttle(self, percent: float) -> None:
        """Set throttle 0.0 – 100.0"""
        raise NotImplementedError

    @abstractmethod
    def brake(self, force: float) -> None:
        """Apply braking force 0.0 – 100.0"""
        raise NotImplementedError
