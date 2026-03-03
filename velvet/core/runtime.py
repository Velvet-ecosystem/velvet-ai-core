# velvet/core/runtime.py
from __future__ import annotations

import logging
import signal
import time

from velvet.core.context import set_event_bus
from velvet.core.module_loader import ModuleLoader
from velvet.core.modules.config import ConfigModule
from velvet.core.modules.event_bus import EventBusModule
from velvet.core.modules.heartbeat import HeartbeatModule
from velvet.core.modules.health import HealthModule
from velvet.core.modules.memory import MemoryModule
from velvet.core.modules.command_bus import CommandBusModule
from velvet.core.modules.registry_module import RegistryModule
from velvet.core.modules.wallet import WalletModule

log = logging.getLogger("velvet.runtime")


class VelvetRuntime:
    def __init__(self) -> None:
        self._running = False
        self.modules = ModuleLoader()

    def start(self) -> None:
        self._running = True
        log.info("VelvetRuntime started.")

        # Config must be loaded before other modules read it
        cfg = ConfigModule(path="velvet_config.json")
        cfg.start()
        self.modules.register(cfg.name, lambda: None, cfg.stop)

        # Registry early so other modules can provide capabilities
        regmod = RegistryModule()
        self.modules.register(regmod.name, regmod.start, regmod.stop)

        # Event bus early (UI can tail events.jsonl)
        bus = EventBusModule(path="events.jsonl")
        set_event_bus(bus)
        self.modules.register(bus.name, bus.start, bus.stop)

        cmd = CommandBusModule(
            path="commands.jsonl",
            poll_interval_s=float(cfg.get("command_poll_interval_s", 0.5)),
        )
        self.modules.register(cmd.name, cmd.start, cmd.stop)

        hb = HeartbeatModule(interval_s=float(cfg.get("heartbeat_interval_s", 5)))
        self.modules.register(hb.name, hb.start, hb.stop)

        mem = MemoryModule(path="memory_events.jsonl")
        self.modules.register(mem.name, mem.start, mem.stop)

        wallet = WalletModule(path="wallet.json")
        self.modules.register(wallet.name, wallet.start, wallet.stop)
        
        health = HealthModule(path="health.json", interval_s=2.0)
        self.modules.register(health.name, health.start, health.stop)

        self.modules.start_all()

    def stop(self) -> None:
        if not self._running:
            return
        self._running = False
        log.info("VelvetRuntime stopping...")
        self.modules.stop_all()

    def _install_signal_handlers(self) -> None:
        def _handle(sig: int, _frame) -> None:
            log.info("Signal received: %s", sig)
            self.stop()

        signal.signal(signal.SIGTERM, _handle)
        signal.signal(signal.SIGINT, _handle)

    def run_forever(self) -> None:
        self._install_signal_handlers()
        self.start()

        while self._running:
            log.info("VelvetRuntime tick.")
            time.sleep(5)

        log.info("VelvetRuntime stopped.")
