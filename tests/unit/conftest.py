import os
from datetime import datetime
from datetime import timezone

import pytest
import salt.config


@pytest.fixture
def minion_opts(tmp_path):
    """
    Default minion configuration with relative temporary paths to not
    require root permissions.
    """
    root_dir = tmp_path / "minion"
    opts = salt.config.DEFAULT_MINION_OPTS.copy()
    opts["__role"] = "minion"
    opts["root_dir"] = str(root_dir)
    for name in ("cachedir", "pki_dir", "sock_dir", "conf_dir"):
        dirpath = root_dir / name
        dirpath.mkdir(parents=True)
        opts[name] = str(dirpath)
    opts["log_file"] = "logs/minion.log"
    opts["conf_file"] = os.path.join(opts["conf_dir"], "minion")
    return opts


@pytest.fixture
def master_opts(tmp_path):
    """
    Default master configuration with relative temporary paths to not
    require root permissions.
    """
    root_dir = tmp_path / "master"
    opts = salt.config.master_config(None)
    opts["__role"] = "master"
    opts["root_dir"] = str(root_dir)
    for name in ("cachedir", "pki_dir", "sock_dir", "conf_dir"):
        dirpath = root_dir / name
        dirpath.mkdir(parents=True)
        opts[name] = str(dirpath)
    opts["log_file"] = "logs/master.log"
    opts["conf_file"] = os.path.join(opts["conf_dir"], "master")
    return opts


@pytest.fixture
def syndic_opts(tmp_path):
    """
    Default master configuration with relative temporary paths to not
    require root permissions.
    """
    root_dir = tmp_path / "syndic"
    opts = salt.config.DEFAULT_MINION_OPTS.copy()
    opts["syndic_master"] = "127.0.0.1"
    opts["__role"] = "minion"
    opts["root_dir"] = str(root_dir)
    for name in ("cachedir", "pki_dir", "sock_dir", "conf_dir"):
        dirpath = root_dir / name
        dirpath.mkdir(parents=True)
        opts[name] = str(dirpath)
    opts["log_file"] = "logs/syndic.log"
    opts["conf_file"] = os.path.join(opts["conf_dir"], "syndic")
    return opts


@pytest.fixture
def snap_list():
    return {
        "bare": {
            "name": "bare",
            "version": "1.0",
            "revision": "5",
            "channel": "latest/stable",
            "publisher": "canonical**",
            "notes": ["base"],
            "classic": False,
            "devmode": False,
            "enabled": True,
            "held": False,
        },
        "core": {
            "name": "core",
            "version": "16-2.61.2",
            "revision": "16928",
            "channel": "latest/stable",
            "publisher": "canonical**",
            "notes": ["core"],
            "classic": False,
            "devmode": False,
            "enabled": True,
            "held": False,
        },
        "core18": {
            "name": "core18",
            "version": "20231027",
            "revision": "2812",
            "channel": "latest/stable",
            "publisher": "canonical**",
            "notes": ["base", "disabled"],
            "classic": False,
            "devmode": False,
            "enabled": False,
            "held": False,
        },
        "gnome-3-28-1804": {
            "name": "gnome-3-28-1804",
            "version": "3.28.0-19-g98f9e67.98f9e67",
            "revision": "198",
            "channel": "latest/stable",
            "publisher": "canonical**",
            "notes": [],
            "classic": False,
            "devmode": False,
            "enabled": True,
            "held": False,
        },
        "gtk-common-themes": {
            "name": "gtk-common-themes",
            "version": "0.1-81-g442e511",
            "revision": "1535",
            "channel": "latest/stable",
            "publisher": "canonical**",
            "notes": ["disabled"],
            "classic": False,
            "devmode": False,
            "enabled": False,
            "held": False,
        },
        "hello-world": {
            "name": "hello-world",
            "version": "6.3",
            "revision": "28",
            "channel": "latest/stable",
            "publisher": "canonical**",
            "notes": ["held"],
            "classic": False,
            "devmode": False,
            "enabled": True,
            "held": True,
        },
        "yubioath-desktop": {
            "name": "yubioath-desktop",
            "version": "5.0.5",
            "revision": "12",
            "channel": "latest/stable",
            "publisher": "yubico-snap-store",
            "notes": [],
            "classic": False,
            "devmode": False,
            "enabled": True,
            "held": False,
        },
        "bw": {
            "name": "bw",
            "version": "2024.3.1",
            "revision": "60",
            "channel": None,
            "publisher": "bitwarden**",
            "notes": [],
            "classic": False,
            "devmode": False,
            "enabled": True,
            "held": False,
        },
    }


@pytest.fixture
def snap_refresh_list():
    return {
        "hello-world": {
            "name": "hello-world",
            "version": "6.4",
            "revision": "29",
            "publisher": "canonical**",
            "notes": [],
            "size": "20kB",
        },
        "yubioath-desktop": {
            "name": "yubioath-desktop",
            "version": "5.1.0",
            "revision": "13",
            "publisher": "yubico-snap-store",
            "notes": [],
            "size": "238MB",
        },
    }


@pytest.fixture
def snap_options():
    return {
        "cloud.name": "unknown",
        "refresh": {},
        "seed.loaded": True,
        "system.hostname": "foobar",
        "system.network": {},
        "system.timezone": "UTC",
    }


@pytest.fixture
def snap_services():
    return {
        "yubioath-desktop.ea": {"enabled": True, "running": True, "notes": []},
        "yubioath-desktop.ei": {"enabled": True, "running": False, "notes": []},
        "yubioath-desktop.da": {"enabled": False, "running": True, "notes": []},
        "yubioath-desktop.di": {"enabled": False, "running": False, "notes": []},
        "hello-world.foo": {"enabled": True, "running": True, "notes": []},
    }


@pytest.fixture
def snap_info():
    return {
        "contact": "snaps@canonical.com",
        "commands": ["hello-world.env", "hello-world.evil", "hello-world", "hello-world.sh"],
        "snap-id": "buPKUD3TKqCOgLEjjHx5kSiCpIs5cMuQ",
        "license": "unset",
        "installed": "6.3            (28) 20kB -",
        "name": "hello-world",
        "store-url": "https://snapcraft.io/hello-world",
        "summary": "The 'hello-world' of snaps",
        "publisher": "Canonical**",
        "channels": {
            "latest/candidate": "6.4 2024-02-27 (29) 20kB -",
            "latest/beta": "6.4 2024-02-27 (29) 20kB -",
            "latest/edge": "6.4 2024-02-27 (29) 20kB -",
            "latest/stable": "6.4 2024-02-27 (29) 20kB -",
        },
        "tracking": "latest/stable",
        "refresh-date": "today at 12:15 UTC",
        "description": "This is a simple hello world example.\n",
    }


@pytest.fixture
def snap_info_verbose():
    return {
        "contact": "snaps@canonical.com",
        "commands": ["hello-world.env", "hello-world.evil", "hello-world", "hello-world.sh"],
        "license": "unset",
        "name": "hello-world",
        "store-url": "https://snapcraft.io/hello-world",
        "description": "This is a simple hello world example.\n",
        "snap-id": "buPKUD3TKqCOgLEjjHx5kSiCpIs5cMuQ",
        "links": {"contact": ["mailto:snaps@canonical.com"]},
        "health": {"status": "unknown", "message": "health has not been set"},
        "installed": "6.3            (28) 20kB -",
        "notes": {
            "trymode": False,
            "devmode": False,
            "enabled": True,
            "broken": False,
            "confinement": "strict",
            "private": False,
            "jailmode": False,
            "ignore-validation": False,
        },
        "summary": "The 'hello-world' of snaps",
        "publisher": "Canonical**",
        "channels": {
            "latest/candidate": "6.4 2024-02-27 (29) 20kB -",
            "latest/beta": "6.4 2024-02-27 (29) 20kB -",
            "latest/edge": "6.4 2024-02-27 (29) 20kB -",
            "latest/stable": "6.4 2024-02-27 (29) 20kB -",
        },
        "tracking": "latest/stable",
        "refresh-date": "today at 12:15 UTC",
    }


@pytest.fixture
def snap_info_file():
    return {
        "path": "/root/tmp/bw_60.snap",
        "name": "bw",
        "summary": "Bitwarden CLI - A secure and free password manager for all of your devices.",
        "version": "2024.3.1 -",
        "build-date": "4 days ago, at 14:01 CEST",
        "license": "unset",
        "description": "Bitwarden, Inc. is the parent company of 8bit Solutions LLC.\n\nNAMED BEST PASSWORD MANAGER BY THE VERGE, U.S. NEWS &amp; WORLD REPORT,\nCNET, AND MORE.\n\nManage, store, secure, and share unlimited passwords across unlimited\ndevices from anywhere. Bitwarden delivers open source password management\nsolutions to everyone, whether at  home, at work, or on the go.\n\nGenerate strong, unique, and random passwords based on security\nrequirements for every website you frequent.\n\nBitwarden Send quickly transmits encrypted information --- files and\nplaintext -- directly to anyone.\n\nBitwarden offers Teams and Enterprise plans for companies so you can\nsecurely share passwords with colleagues.\n\nWhy Choose Bitwarden:\n\nWorld-Class Encryption\nPasswords are protected with advanced end-to-end encryption (AES-256 bit,\nsalted hashing, and PBKDF2 SHA-256) so your data stays secure and private.\n\nBuilt-in Password Generator\nGenerate strong, unique, and random passwords based on security\nrequirements for every website you frequent.\n\nGlobal Translations\nBitwarden translations exist in 40 languages and are growing, thanks to our\nglobal community.\n\nCross-Platform Applications\nSecure and share sensitive data within your Bitwarden Vault from any\nbrowser, mobile device, or desktop OS, and more.\n",
        "commands": ["bw"],
        "notes": {"private": False, "confinement": "strict"},
        "base": "core22",
        "sha3-384": "rCj3QCM0PMpsn4FiyOqBpUBtjbU_PLGrTOcr96Q9jTKjV96NSRDpW9lZIpmrsSJU",
    }


@pytest.fixture
def snap_known():
    return [
        {
            "type": "snap-revision",
            "authority-id": "canonical",
            "snap-sha3-384": "AH7zvZLOXzHcp3gxaWTmGUOrmsXYJmACXFiCBoydL-H1PlC9G43rGAJs3WiyzOb_",
            "developer-id": "GKq9csPRQp1E5kUglZG9QTqDEBLrcszO",
            "provenance": "global-upload",
            "snap-id": "JUJH91Ved74jd4ZgJCpzMBtYbPOzTlsD",
            "snap-revision": 142,
            "snap-size": 123101184,
            "timestamp": datetime(2024, 4, 3, 17, 49, 48, 613165, tzinfo=timezone.utc),
            "sign-key-sha3-384": "BWDEoaqyr25nF5SNCvEv2v7QnM9QsfCc0PBMYD_i2NGSQ32EF2d4D0hqUel3m8ul",
        },
        {
            "type": "snap-revision",
            "authority-id": "canonical",
            "snap-sha3-384": "tZ4sZcgQR8QSIdneZKmUj44OXwnVm_64iWwPmwh_3Jfi5eGCRyDYEnfrAcIsX2D_",
            "developer-id": "canonical",
            "provenance": "global-upload",
            "snap-id": "TIM9dBBJEceEjMpwaB3fiuZ3AdSykgDO",
            "snap-revision": 93,
            "snap-size": 228999168,
            "timestamp": datetime(2023, 4, 24, 16, 34, 37, 479211, tzinfo=timezone.utc),
            "sign-key-sha3-384": "BWDEoaqyr25nF5SNCvEv2v7QnM9QsfCc0PBMYD_i2NGSQ32EF2d4D0hqUel3m8ul",
        },
        {
            "type": "snap-revision",
            "authority-id": "canonical",
            "snap-sha3-384": "rCj3QCM0PMpsn4FiyOqBpUBtjbU_PLGrTOcr96Q9jTKjV96NSRDpW9lZIpmrsSJU",
            "developer-id": "SflUpHyJuL9BkjUnFAgINhCW9QjI5tow",
            "provenance": "global-upload",
            "snap-id": "n0XNnJXxSdYYHRYwtfYV2mBSkzH1Fbkn",
            "snap-revision": 60,
            "snap-size": 28114944,
            "timestamp": datetime(2024, 4, 8, 12, 46, 12, 441719, tzinfo=timezone.utc),
            "sign-key-sha3-384": "BWDEoaqyr25nF5SNCvEv2v7QnM9QsfCc0PBMYD_i2NGSQ32EF2d4D0hqUel3m8ul",
        },
        {
            "type": "snap-revision",
            "authority-id": "canonical",
            "snap-sha3-384": "7uNHCak9aSwcICRfP1YmJNGrRqROw45Ihj1aFx7S74MUfXYedKyZQzbjkJC2CCYd",
            "developer-id": "canonical",
            "provenance": "global-upload",
            "snap-id": "amcUKQILKXHHTlmSa7NMdnXSx02dNeeT",
            "snap-revision": 1122,
            "snap-size": 77819904,
            "timestamp": datetime(2024, 1, 11, 16, 31, 37, 728357, tzinfo=timezone.utc),
            "sign-key-sha3-384": "BWDEoaqyr25nF5SNCvEv2v7QnM9QsfCc0PBMYD_i2NGSQ32EF2d4D0hqUel3m8ul",
        },
    ]
