"""Hardware identity spoofing (ported from qoderush)."""

from __future__ import annotations

import hashlib
import json
import random
import uuid

# Apple MAC OUI prefixes
APPLE_OUI = [
    "DC:A6:32", "AC:DE:48", "F8:FF:C2", "3C:22:FB", "A4:83:E7",
    "50:EA:F6", "B4:96:91", "00:03:93", "00:05:02", "00:0A:27",
    "60:FB:42", "70:56:81", "88:66:A5", "98:B8:63", "A8:20:66",
    "CC:08:E0", "E0:B9:BA", "F0:DB:E2",
]

APPLE_FACTORY_CODES = ["C02", "C07", "C17", "C1M", "D25", "DMP", "F5V", "W89", "W80"]
APPLE_BOARD_IDS = [
    "MacBookPro16,1", "MacBookPro16,2", "MacBookPro15,1",
    "MacBookPro15,2", "MacBookPro15,4", "iMac19,1",
    "iMac19,2", "iMac20,1", "iMac20,2", "iMacPro1,1",
]
APPLE_PRODUCT_NAMES = [
    "MacBookPro16,1", "MacBookPro16,2", "MacBookPro15,1",
    "MacBookPro15,2", "MacBookPro15,4", "iMac19,1",
    "iMac20,1", "iMacPro1,1",
]
APPLE_BIOS_VERSIONS = [
    "2069.0.0.0.0", "1968.0.0.0.0", "1856.0.0.0.0",
    "1715.0.0.0.0", "1678.0.0.0.0",
]

INTEL_CPUS = [
    {"name": "Intel(R) Core(TM) i7-9750H CPU @ 2.60GHz", "family": 6, "model": 158, "stepping": 13},
    {"name": "Intel(R) Core(TM) i9-9980HK CPU @ 2.40GHz", "family": 6, "model": 158, "stepping": 13},
    {"name": "Intel(R) Core(TM) i7-8850H CPU @ 2.60GHz", "family": 6, "model": 158, "stepping": 10},
    {"name": "Intel(R) Core(TM) i5-1038NG7 CPU @ 2.00GHz", "family": 6, "model": 126, "stepping": 5},
    {"name": "Intel(R) Core(TM) i7-1068NG7 CPU @ 2.30GHz", "family": 6, "model": 126, "stepping": 5},
]


def _rng_from_seed(seed: str) -> random.Random:
    """Create deterministic RNG from seed."""
    h = hashlib.sha256(seed.encode()).hexdigest()
    return random.Random(int(h[:16], 16))


def _generate_machine_id(rng: random.Random) -> str:
    """Generate 32-char hex machine ID."""
    return "".join(rng.choice("0123456789abcdef") for _ in range(32))


def generate_identity(seed: str, platform: str = "macos") -> dict:
    """Generate deterministic fake hardware identity from seed."""
    rng = _rng_from_seed(seed)

    if platform == "macos":
        return _generate_macos_identity(rng, seed)
    else:
        return _generate_linux_identity(rng, seed)


def _generate_macos_identity(rng: random.Random, seed: str) -> dict:
    """Generate macOS (MacBook Pro) identity."""
    product_name = rng.choice(APPLE_PRODUCT_NAMES)
    board_id = rng.choice(APPLE_BOARD_IDS)
    bios_version = rng.choice(APPLE_BIOS_VERSIONS)
    cpu = rng.choice(INTEL_CPUS)

    # Apple serial: 3-char factory + 2-char year/week + 4 random + 3 check
    factory = rng.choice(APPLE_FACTORY_CODES)
    year_code = rng.choice("CDEFPRSTUVWX")
    week_code = f"{rng.randint(0, 52):02d}"[-1]
    mid = "".join(rng.choices("0123456789ABCDEFGHJKLMNPQRSTUVWXYZ", k=4))
    check = "".join(rng.choices("CFGHJKLMMPQRUVWXY", k=3))
    serial = f"{factory}{year_code}{week_code}{mid}{check}"

    board_serial = serial + "".join(rng.choices("0123456789ABCDEF", k=5))

    oui = rng.choice(APPLE_OUI)
    mac_suffix = ":".join(f"{rng.randint(0, 255):02x}" for _ in range(3))
    mac = f"{oui}:{mac_suffix}"

    hostname_names = ["Rifqi", "Admin", "User", "MacBook", "Pro"]
    hostname = f"{rng.choice(hostname_names)}-MacBook-{rng.randint(1000, 9999)}"

    cpuinfo = (
        f"processor\t: 0\n"
        f"vendor_id\t: GenuineIntel\n"
        f"model name\t: {cpu['name']}\n"
        f"cpu family\t: {cpu['family']}\n"
        f"model\t\t: {cpu['model']}\n"
        f"stepping\t: {cpu['stepping']}\n"
    )

    return {
        "seed": seed,
        "platform": "x86_64_darwin",
        "machine_id": _generate_machine_id(rng),
        "product_uuid": str(uuid.UUID(int=rng.getrandbits(128))),
        "mac": mac,
        "product_serial": serial,
        "board_serial": board_serial,
        "hostname": hostname,
        "product_name": product_name,
        "board_id": board_id,
        "bios_version": bios_version,
        "bios_vendor": "Apple Inc.",
        "sys_vendor": "Apple Inc.",
        "cpu_name": cpu["name"],
        "cpuinfo": cpuinfo,
    }


def _generate_linux_identity(rng: random.Random, seed: str) -> dict:
    """Generate Linux (ASUS desktop) identity."""
    machine_id = _generate_machine_id(rng)
    product_uuid = str(uuid.UUID(int=rng.getrandbits(128)))

    # Locally administered MAC
    mac_first = rng.randint(0, 255) | 0x02  # Set locally administered bit
    mac_first &= 0xFE  # Clear multicast bit
    mac = f"02:{mac_first:02x}:" + ":".join(f"{rng.randint(0, 255):02x}" for _ in range(4))

    serial = "".join(rng.choices("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789", k=12))
    board_serial = "".join(rng.choices("0123456789ABCDEF", k=17))
    cpu_serial = hashlib.sha256(seed.encode()).hexdigest()[:16]

    hostname = f"DESKTOP-{''.join(rng.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=7))}"

    return {
        "seed": seed,
        "platform": "x86_64_linux",
        "machine_id": machine_id,
        "product_uuid": product_uuid,
        "mac": mac,
        "product_serial": serial,
        "board_serial": board_serial,
        "cpu_serial": cpu_serial,
        "hostname": hostname,
        "product_name": "PRIME X570-E",
        "board_name": "PRIME X570-E",
        "bios_vendor": "American Megatrends Inc.",
        "sys_vendor": "ASUSTeK COMPUTER INC.",
    }


if __name__ == "__main__":
    import sys

    seed = sys.argv[1] if len(sys.argv) > 1 else "test-seed"
    platform = sys.argv[2] if len(sys.argv) > 2 else "macos"
    identity = generate_identity(seed, platform)
    print(json.dumps(identity, indent=2))
