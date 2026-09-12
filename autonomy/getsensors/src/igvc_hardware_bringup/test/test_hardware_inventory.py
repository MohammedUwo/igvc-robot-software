from pathlib import Path


def workspace_root() -> Path:
    return Path(__file__).resolve().parents[3]


def test_hardware_inventory_documents_detected_devices():
    text = (workspace_root() / 'docs' / 'hardware_inventory.md').read_text()

    assert 'Intel RealSense D435' in text
    assert '939622074571' in text
    assert 'OAK-D' in text
    assert '1844301051345D0E00' in text
    assert '/dev/ttyUSB0' in text
    assert '/dev/ttyUSB1' in text
    assert '/dev/ttyACM0' in text
