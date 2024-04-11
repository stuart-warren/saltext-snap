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
            "classic": False,
            "devmode": False,
            "enabled": True,
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
        },
        "hello-world": {
            "name": "hello-world",
            "version": "6.3",
            "revision": "28",
            "channel": "latest/stable",
            "publisher": "canonical**",
            "notes": [],
            "classic": False,
            "devmode": False,
            "enabled": True,
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
