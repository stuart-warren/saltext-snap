import os

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
        },
        "core": {
            "name": "core",
            "version": "16-2.61.2",
            "revision": "16928",
            "channel": "latest/stable",
            "publisher": "canonical**",
            "notes": ["core"],
        },
        "core18": {
            "name": "core18",
            "version": "20231027",
            "revision": "2812",
            "channel": "latest/stable",
            "publisher": "canonical**",
            "notes": ["base", "disabled"],
        },
        "gnome-3-28-1804": {
            "name": "gnome-3-28-1804",
            "version": "3.28.0-19-g98f9e67.98f9e67",
            "revision": "198",
            "channel": "latest/stable",
            "publisher": "canonical**",
            "notes": [],
        },
        "gtk-common-themes": {
            "name": "gtk-common-themes",
            "version": "0.1-81-g442e511",
            "revision": "1535",
            "channel": "latest/stable",
            "publisher": "canonical**",
            "notes": ["disabled"],
        },
        "hello-world": {
            "name": "hello-world",
            "version": "6.4",
            "revision": "28",
            "channel": "latest/stable",
            "publisher": "canonical**",
            "notes": [],
        },
        "yubioath-desktop": {
            "name": "yubioath-desktop",
            "version": "5.1.0",
            "revision": "12",
            "channel": "latest/stable",
            "publisher": "yubico-snap-store",
            "notes": [],
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
        "name": "hello-world",
        "summary": "The 'hello-world' of snaps",
        "publisher": "Canonical**",
        "store-url": "https://snapcraft.io/hello-world",
        "contact": "snaps@canonical.com",
        "license": "unset",
        "description": "This is a simple hello world example.\n",
        "commands": ["hello-world.env", "hello-world.evil", "hello-world", "hello-world.sh"],
        "snap-id": "buPKUD3TKqCOgLEjjHx5kSiCpIs5cMuQ",
        "tracking": "latest/stable",
        "refresh-date": "yesterday at 20:29 CEST",
        "channels": {
            "latest/stable": "6.4 2024-02-27 (29) 20kB -",
            "latest/candidate": "6.4 2024-02-27 (29) 20kB -",
            "latest/beta": "6.4 2024-02-27 (29) 20kB -",
            "latest/edge": "6.4 2024-02-27 (29) 20kB -",
        },
        "installed": "6.4            (29) 20kB -",
    }
