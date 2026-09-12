from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class SafetyGate:
    command_enabled: bool
    stale: bool
    estop_active: bool

    def command_allowed(self) -> Tuple[bool, str]:
        if self.estop_active:
            return False, 'estop_active'
        if self.stale:
            return False, 'stale_safety_state'
        if not self.command_enabled:
            return False, 'commands_disabled'
        return True, 'ok'
