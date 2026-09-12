from igvc_odrive_interface.safety import SafetyGate


def test_safety_gate_rejects_commands_when_estop_active():
    gate = SafetyGate(command_enabled=True, stale=False, estop_active=True)

    allowed, reason = gate.command_allowed()

    assert allowed is False
    assert reason == "estop_active"


def test_safety_gate_rejects_commands_when_telemetry_stale():
    gate = SafetyGate(command_enabled=True, stale=True, estop_active=False)

    allowed, reason = gate.command_allowed()

    assert allowed is False
    assert reason == "stale_safety_state"


def test_safety_gate_rejects_commands_until_explicitly_enabled():
    gate = SafetyGate(command_enabled=False, stale=False, estop_active=False)

    allowed, reason = gate.command_allowed()

    assert allowed is False
    assert reason == "commands_disabled"


def test_safety_gate_allows_commands_only_when_enabled_fresh_and_not_estopped():
    gate = SafetyGate(command_enabled=True, stale=False, estop_active=False)

    allowed, reason = gate.command_allowed()

    assert allowed is True
    assert reason == "ok"
