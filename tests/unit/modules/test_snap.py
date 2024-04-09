import contextlib
import json
from textwrap import dedent
from unittest.mock import Mock
from unittest.mock import patch

import pytest
import salt.modules.cmdmod
import saltext.snap.modules.snap_mod as snap
from salt.exceptions import CommandExecutionError
from salt.exceptions import SaltInvocationError


@pytest.fixture
def configure_loader_modules(cmd_run):
    module_globals = {
        "__salt__": {"cmd.run_all": cmd_run},
    }
    # It seems the dunder functions are not called by the test suite, need
    # to initialize globals
    snap.__init__(None)
    return {
        snap: module_globals,
    }


@pytest.fixture
def cmd_run():
    run = Mock(spec=salt.modules.cmdmod.run_all)

    def _run(*args, **kwargs):
        if isinstance(run.return_value, dict):
            return run.return_value
        return {
            "stdout": run.return_value or "potentially gar?bled output",
            "stderr": "",
            "retcode": 0,
        }

    run.side_effect = _run
    return run


@pytest.fixture
def snap_list_out():
    return dedent(
        """
            Name               Version                     Rev    Tracking       Publisher          Notes
            bare               1.0                         5      latest/stable  canonical**        base
            core               16-2.61.2                   16928  latest/stable  canonical**        core
            core18             20231027                    2812   latest/stable  canonical**        base,disabled
            gnome-3-28-1804    3.28.0-19-g98f9e67.98f9e67  198    latest/stable  canonical**        -
            gtk-common-themes  0.1-81-g442e511             1535   latest/stable  canonical**        disabled
            hello-world        6.4                         28     latest/stable  canonical**        -
            yubioath-desktop   5.1.0                       12     latest/stable  yubico-snap-store  -
        """
    ).strip()


@pytest.fixture
def snap_refresh_list_out():
    return dedent(
        """
            Name              Version  Rev  Size   Publisher          Notes
            hello-world       6.4      29   20kB   canonical**        -
            yubioath-desktop  5.1.0    13   238MB  yubico-snap-store  -
        """
    ).strip()


@pytest.fixture
def snap_get_out():
    return dedent(
        """
        {
            "cloud": {
                "name": "unknown"
            },
            "refresh": {},
            "seed": {
                "loaded": true
            },
            "system": {
                "hostname": "foobar",
                "network": {},
                "timezone": "UTC"
            }
        }
        """
    ).strip()


@pytest.fixture
def snap_services_out():
    return dedent(
        """
        Service              Startup   Current   Notes
        yubioath-desktop.ea  enabled   active    -
        yubioath-desktop.ei  enabled   inactive  -
        yubioath-desktop.da  disabled  active    -
        yubioath-desktop.di  disabled  inactive  -
        hello-world.foo      enabled   active    -
    """
    ).strip()


@pytest.fixture
def snap_info_out():
    return dedent(
        """
            name:      hello-world
            summary:   The 'hello-world' of snaps
            publisher: Canonical**
            store-url: https://snapcraft.io/hello-world
            contact:   snaps@canonical.com
            license:   unset
            description: |
              This is a simple hello world example.
            commands:
              - hello-world.env
              - hello-world.evil
              - hello-world
              - hello-world.sh
            snap-id:      buPKUD3TKqCOgLEjjHx5kSiCpIs5cMuQ
            tracking:     latest/stable
            refresh-date: yesterday at 20:29 CEST
            channels:
              latest/stable:    6.4 2024-02-27 (29) 20kB -
              latest/candidate: 6.4 2024-02-27 (29) 20kB -
              latest/beta:      6.4 2024-02-27 (29) 20kB -
              latest/edge:      6.4 2024-02-27 (29) 20kB -
            installed:          6.4            (29) 20kB -
        """
    ).strip()


@pytest.fixture
def run_mock():
    def _run(*args, **kwargs):
        if kwargs.get("full"):
            if isinstance(run.return_value, dict):
                return run.return_value
            return {
                "stdout": run.return_value or "potentially gar?bled output",
                "stderr": "",
                "retcode": 0,
            }
        return run.return_value or ""

    with patch("saltext.snap.modules.snap_mod._run", autospec=True, side_effect=_run) as run:
        yield run


@pytest.fixture
def list_mock(snap_list):
    with patch("saltext.snap.modules.snap_mod.list_", autospec=True, return_value=snap_list) as lst:
        yield lst


@pytest.fixture
def cmd_run_services(cmd_run, snap_services_out):
    cmd_run.return_value = snap_services_out
    return cmd_run


@pytest.fixture
def cmd_run_list_err(cmd_run):
    cmd_run.return_value = {
        "stdout": "",
        "stderr": "error: no matching snaps installed",
        "retcode": 1,
    }


@pytest.fixture
def list_upgrades_mock(snap_refresh_list):
    with patch(
        "saltext.snap.modules.snap_mod.list_upgrades", autospec=True, return_value=snap_refresh_list
    ) as lst:
        yield lst


@pytest.mark.parametrize("func", ("enable", "disable"))
def test_en_dis_able(run_mock, func):
    run_mock.return_value = "possibly garbled text"
    res = getattr(snap, func)("foo")
    assert res is True
    run_mock.assert_called_once_with(["snap", func, "foo"])


@pytest.mark.parametrize("verbose", (False, True))
def test_info(verbose, run_mock, snap_info_out, snap_info):
    run_mock.return_value = snap_info_out
    assert snap.info("hello-world", verbose=verbose) == snap_info
    cmd = run_mock.call_args[0][0]
    assert ("--verbose" in cmd) is verbose
    assert cmd[:4] == ["snap", "info", "--unicode=never", "--color=never"]
    assert cmd[-1] == "hello-world"


@pytest.mark.parametrize("channel", (None, "latest/edge"))
@pytest.mark.parametrize("classic", (False, True))
@pytest.mark.parametrize("refresh", (False, True))
@pytest.mark.parametrize("revision", (None, 10))
def test_install(channel, revision, classic, refresh, cmd_run):
    res = snap.install("foo", channel=channel, revision=revision, classic=classic, refresh=refresh)
    assert res is True
    cmd_str = cmd_run.call_args[0][0]
    assert cmd_str.startswith("snap refresh") is refresh
    assert ("--classic" in cmd_str) is classic
    assert ("--revision" in cmd_str) is bool(revision)
    assert ("--channel" in cmd_str) is bool(channel)
    if revision:
        assert f"--revision {revision}" in cmd_str
    if channel:
        assert f"--channel {channel}" in cmd_str


@pytest.mark.parametrize(
    "channel,err",
    (
        ("trackonly", False),
        ("stable", False),
        ("tracka/stable", False),
        ("trackb/candidate", False),
        ("trackc/beta", False),
        ("trackd/edge", False),
        ("tracke/stable/brancha", False),
        ("trackf/candidate/branchb", False),
        ("trackg/beta/branchc", False),
        ("trackh/edge/branchd", False),
        ("tracki/stabble", "Invalid channel risk level 'stabble'"),
        ("trackj/betta/branche", "Invalid channel risk level 'betta'"),
        ("foo/stable/bar/baz", "Invalid channel name"),
    ),
)
def test_install_channel_validation(channel, err, run_mock):
    if err:
        ctx = pytest.raises(SaltInvocationError, match=err)
    else:
        ctx = contextlib.nullcontext()
    with ctx:
        snap.install("foo", channel=channel)


def test_install_already_installed(cmd_run):
    cmd_run.return_value = {
        "stdout": "",
        "stderr": "snap \"hello-world\" is already installed, see 'snap help refresh'",
        "retcode": 0,
    }
    with pytest.raises(CommandExecutionError, match="is already installed"):
        snap.install("hello-world")


@pytest.mark.usefixtures("list_mock")
@pytest.mark.parametrize("name,expected", (("hello-world", True), ("core18", False)))
def test_is_enabled(name, expected):
    assert snap.is_enabled(name) is expected


@pytest.mark.usefixtures("cmd_run_list_err")
@pytest.mark.parametrize("func", ("is_enabled", "is_uptodate"))
def test_status_checks_not_installed(func):
    with pytest.raises(CommandExecutionError, match="is not installed"):
        getattr(snap, func)("foo")


@pytest.mark.parametrize("name,expected", (("hello-world", True), ("foobar", False)))
def test_is_installed(name, expected, snap_list_out, cmd_run):
    cmd_run.return_value = (
        snap_list_out
        if expected
        else {"stdout": "", "stderr": "error: no matching snaps installed", "retcode": 1}
    )
    assert snap.is_installed(name) is expected


@pytest.mark.usefixtures("list_mock")
@pytest.mark.usefixtures("list_upgrades_mock")
@pytest.mark.parametrize("name,expected", (("core18", True), ("hello-world", False)))
def test_is_uptodate_with_name(name, expected):
    assert snap.is_uptodate(name) is expected


@pytest.mark.parametrize("expected", (True, False))
def test_is_uptodate(list_upgrades_mock, expected):
    if expected:
        list_upgrades_mock.return_value = {}
    assert snap.is_uptodate() is expected


def test_list(cmd_run, snap_list_out, snap_list):
    cmd_run.return_value = snap_list_out
    assert snap.list_() == snap_list


def test_list_upgrades(cmd_run, snap_refresh_list_out, snap_refresh_list):
    cmd_run.return_value = snap_refresh_list_out
    assert snap.list_upgrades() == snap_refresh_list


def test_list_other_error(cmd_run):
    cmd_run.return_value = {"stdout": "", "stderr": "something went wrong", "retcode": 1}
    with pytest.raises(CommandExecutionError, match="something went wrong"):
        snap.list_()


@pytest.mark.usefixtures("list_mock")
@pytest.mark.parametrize("option", (None, "system", "system.timezone"))
def test_options(option, cmd_run, snap_get_out, snap_options):
    ret = json.loads(snap_get_out)
    if option:
        parts = option.split(".")
        while parts:
            ret = ret[parts.pop(0)]
        ret = {option: ret}
        if isinstance(ret[next(iter(ret))], dict):
            prefix = next(iter(ret))
            exp = {f"{prefix}.{opt}": val for opt, val in ret[prefix].items()}
        else:
            exp = ret
    else:
        exp = snap_options
    cmd_run.return_value = json.dumps(ret)
    res = snap.options("core", option=option)
    assert res == exp
    cmd_str = cmd_run.call_args[0][0]
    assert cmd_str.startswith("snap get -d core")
    assert cmd_str.endswith(option or "")


@pytest.mark.usefixtures("list_mock")
def test_options_not_set(cmd_run):
    cmd_run.return_value = {
        "stdout": "",
        "stderr": 'error: snap "core" has no "systemd" configuration option',
        "retcode": 1,
    }
    assert snap.options("core", "systemd") is None


@pytest.mark.usefixtures("cmd_run_list_err")
def test_options_missing_snap():
    with pytest.raises(CommandExecutionError, match="not installed"):
        snap.options("foo")


def test_option_set(cmd_run):
    res = snap.option_set("foo", "bar", False)
    assert res is True
    cmd_str = cmd_run.call_args[0][0]
    assert cmd_str == "snap set -t foo bar=false"


def test_option_unset(cmd_run):
    res = snap.option_unset("foo", "bar")
    assert res is True
    cmd_str = cmd_run.call_args[0][0]
    assert cmd_str == "snap unset foo bar"


def test_purge():
    with patch("saltext.snap.modules.snap_mod.remove", autospec=True, return_value=True) as rem:
        res = snap.purge("foo", revision=10)
        assert res is True
        args, kwargs = rem.call_args
        assert args[0] == "foo"
        assert kwargs["revision"] == 10
        assert kwargs["purge"] is True


def test_refresh():
    with patch("saltext.snap.modules.snap_mod.install", autospec=True, return_value=True) as inst:
        res = snap.refresh("foo", channel="discovery", revision=10, classic=True)
        assert res is True
        args, kwargs = inst.call_args
        assert args[0] == "foo"
        assert kwargs["refresh"] is True
        assert kwargs["channel"] == "discovery"
        assert kwargs["revision"] == 10
        assert kwargs["classic"] is True


@pytest.mark.parametrize("purge", (False, True))
@pytest.mark.parametrize("revision", (None, 10))
def test_remove(revision, purge, cmd_run):
    res = snap.remove("foo", revision=revision, purge=purge)
    assert res is True
    cmd_str = cmd_run.call_args[0][0]
    assert ("--purge" in cmd_str) is purge
    assert ("--revision" in cmd_str) is bool(revision)
    if revision:
        assert f"--revision {revision}" in cmd_str


def test_services(cmd_run, snap_services_out, snap_services):
    cmd_run.return_value = snap_services_out
    assert snap.services() == snap_services


@pytest.mark.parametrize(
    "name,snp,expected",
    (
        (None, "hello-world", ["hello-world.foo"]),
        ("yubioath-desktop.ea", None, ["yubioath-desktop.ea"]),
        (
            None,
            "yubioath-desktop",
            [
                "yubioath-desktop.ea",
                "yubioath-desktop.da",
                "yubioath-desktop.ei",
                "yubioath-desktop.di",
            ],
        ),
    ),
)
def test_services_filtering(name, snp, expected, run_mock, snap_services_out, snap_services):
    run_mock.return_value = snap_services_out
    assert set(snap.services(name, snp)) == set(expected)


@pytest.mark.usefixtures("cmd_run_services")
@pytest.mark.parametrize("func", ("enabled", "running"))
@pytest.mark.parametrize("expected", (True, False))
def test_service_status(func, expected):
    if func == "enabled":
        serv = "ea" if expected else "da"
    else:
        serv = "ea" if expected else "di"
    assert getattr(snap, f"service_{func}")(f"yubioath-desktop.{serv}") is expected


@pytest.mark.usefixtures("cmd_run_services")
@pytest.mark.parametrize("func", ("service_enabled", "service_running", "services"))
def test_service_status_missing_service(func, snap_services_out):
    with pytest.raises(CommandExecutionError, match="No such service"):
        getattr(snap, func)("foo.bar")


@pytest.mark.parametrize(
    "func,param", (("start", "enable"), ("stop", "disable"), ("restart", "reload"))
)
@pytest.mark.parametrize("param_val", (True, False))
def test_service_actions(func, param, param_val, run_mock):
    kwargs = {param: param_val}
    res = getattr(snap, f"service_{func}")("foo.bar", **kwargs)
    assert res is True
    cmd = run_mock.call_args[0][0]
    assert (f"--{param}" in cmd) is param_val
    assert cmd[:2] == ["snap", func]
    assert "foo.bar" in cmd


def test_upgrade_all(cmd_run):
    res = snap.upgrade_all()
    assert res is True
    assert cmd_run.call_args[0][0] == "snap refresh --unicode=never --color=never"
