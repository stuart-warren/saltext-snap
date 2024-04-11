from unittest.mock import Mock
from unittest.mock import patch

import pytest
import saltext.snap.modules.snap_mod as snap_module
import saltext.snap.states.snap_mod as snap
from salt.defaults import NOT_SET
from salt.exceptions import CommandExecutionError


@pytest.fixture
def global_state(snap_list):
    return {
        "disabled": [snp for snp, data in snap_list.items() if not data["enabled"]],
        "removed": [],
        "held": [snp for snp, data in snap_list.items() if data["held"]],
        "snap_list": snap_list,
    }


@pytest.fixture
def snap_list_mock(snap_list, request, global_state):
    ret = getattr(request, "param", snap_list)
    global_state["snap_list"] = ret

    def _list(name=None, **kwargs):
        base = {snp: data for snp, data in ret.items() if snp not in global_state["removed"]}
        if name:
            if name not in base:
                return {}
            return {name: base[name]}
        return base

    return Mock(spec=snap_module.list_, side_effect=_list)


@pytest.fixture
def snap_list_upgrades_mock(snap_refresh_list, global_state):
    def _list_upgrades():
        return {
            serv: data
            for serv, data in snap_refresh_list.items()
            if global_state["snap_list"][serv]["revision"] != data["revision"]
        }

    return Mock(spec=snap_module.list_upgrades, side_effect=_list_upgrades)


@pytest.fixture
def snap_install_mock(global_state):
    def _install(name, channel=None, revision=None, classic=False, refresh=False):
        if name in global_state["snap_list"]:
            if not refresh:
                raise CommandExecutionError("Already installed")
            if channel:
                global_state["snap_list"][name]["channel"] = channel
            if revision:
                global_state["snap_list"][name]["revision"] = str(revision)
        else:
            global_state["snap_list"][name] = {
                "name": name,
                "version": "1",
                "revision": str(revision or 1),
                "channel": channel or "latest/stable",
                "publisher": "foobar",
                "notes": [],
            }

    return Mock(spec=snap_module.install, side_effect=_install)


@pytest.fixture
def snap_is_enabled_mock(global_state):
    def _is_enabled(name):
        return name not in global_state["disabled"]

    return Mock(spec=snap_module.is_enabled, side_effect=_is_enabled)


@pytest.fixture
def snap_is_held_mock(global_state):
    def _is_held(name):
        return name in global_state["held"]

    return Mock(spec=snap_module.is_held, side_effect=_is_held)


@pytest.fixture
def snap_hold_mock(global_state, snap_list):
    def _hold(name):
        if name not in global_state["held"]:
            global_state["held"].append(name)
        snap_list[name]["held"] = True

    return Mock(spec=snap_module.hold, side_effect=_hold)


@pytest.fixture
def snap_unhold_mock(global_state, snap_list):
    def _unhold(name):
        if name in global_state["held"]:
            global_state["held"].remove(name)
        snap_list[name]["held"] = False

    return Mock(spec=snap_module.unhold, side_effect=_unhold)


@pytest.fixture
def snap_enable_mock(global_state):
    def _enable(name):
        if name in global_state["disabled"]:
            global_state["disabled"].remove(name)

    return Mock(spec=snap_module.enable, side_effect=_enable)


@pytest.fixture
def snap_disable_mock(global_state):
    def _disable(name):
        if name not in global_state["disabled"]:
            global_state["disabled"].append(name)

    return Mock(spec=snap_module.enable, side_effect=_disable)


@pytest.fixture
def snap_remove_mock(global_state):
    def _remove(name, **kwargs):
        if name not in global_state["removed"]:
            global_state["removed"].append(name)

    return Mock(spec=snap_module.remove, side_effect=_remove)


@pytest.fixture
def snap_services_mock(snap_services):
    def _srv(name=None, snap=None):
        if name:
            return {name: snap_services[name]}
        if snap:
            return {snp: data for snp, data in snap_services.items() if snp.startswith(f"{snap}.")}
        return snap_services

    return Mock(spec=snap_module.remove, side_effect=_srv)


@pytest.fixture
def snap_service_enabled_mock(snap_services):
    def _enabled(name):
        return snap_services[name]["enabled"]

    return Mock(spec=snap_module.service_enabled, side_effect=_enabled)


@pytest.fixture
def snap_service_running_mock(snap_services):
    def _running(name):
        return snap_services[name]["running"]

    return Mock(spec=snap_module.service_running, side_effect=_running)


@pytest.fixture
def snap_service_start_mock(snap_services):
    def _start(name, enable=None):
        snap_services[name]["running"] = True
        if enable:
            snap_services[name]["enabled"] = True

    return Mock(spec=snap_module.service_start, side_effect=_start)


@pytest.fixture
def snap_service_restart_mock(snap_services):
    def _restart(name, **kwargs):
        snap_services[name]["running"] = True

    return Mock(spec=snap_module.service_restart, side_effect=_restart)


@pytest.fixture
def snap_service_stop_mock(snap_services):
    def _stop(name, disable=None):
        snap_services[name]["running"] = False
        if disable:
            snap_services[name]["enabled"] = False

    return Mock(spec=snap_module.service_stop, side_effect=_stop)


@pytest.fixture
def snap_options_mock(snap_options):
    return Mock(spec=snap_module.options, return_value=snap_options)


@pytest.fixture
def snap_option_set_mock(snap_options):
    def _set(name, option, value):
        snap_options[option] = value
        return True

    return Mock(spec=snap_module.option_set, side_effect=_set)


@pytest.fixture
def snap_option_unset_mock(snap_options):
    def _unset(name, option):
        snap_options.pop(option)
        return True

    return Mock(spec=snap_module.option_unset, side_effect=_unset)


@pytest.fixture
def configure_loader_modules(
    testmode,
    snap_list_mock,
    snap_is_enabled_mock,
    snap_enable_mock,
    snap_disable_mock,
    snap_is_held_mock,
    snap_hold_mock,
    snap_unhold_mock,
    snap_remove_mock,
    snap_services_mock,
    snap_service_enabled_mock,
    snap_service_running_mock,
    snap_service_start_mock,
    snap_service_stop_mock,
    snap_service_restart_mock,
    snap_install_mock,
    snap_list_upgrades_mock,
    snap_options_mock,
    snap_option_set_mock,
    snap_option_unset_mock,
):
    return {
        snap: {
            "__salt__": {
                "snap.list": snap_list_mock,
                "snap.is_enabled": snap_is_enabled_mock,
                "snap.enable": snap_enable_mock,
                "snap.disable": snap_disable_mock,
                "snap.is_held": snap_is_held_mock,
                "snap.hold": snap_hold_mock,
                "snap.unhold": snap_unhold_mock,
                "snap.remove": snap_remove_mock,
                "snap.services": snap_services_mock,
                "snap.service_enabled": snap_service_enabled_mock,
                "snap.service_running": snap_service_running_mock,
                "snap.service_start": snap_service_start_mock,
                "snap.service_stop": snap_service_stop_mock,
                "snap.service_restart": snap_service_restart_mock,
                "snap.install": snap_install_mock,
                "snap.list_upgrades": snap_list_upgrades_mock,
                "snap.options": snap_options_mock,
                "snap.option_set": snap_option_set_mock,
                "snap.option_unset": snap_option_unset_mock,
            },
            "__opts__": {
                "test": testmode,
            },
        },
    }


@pytest.fixture(params=(False, True))
def testmode(request):
    return request.param


@pytest.mark.parametrize("name,changes", (("hello-world", False), ("core18", True)))
def test_enabled(name, changes, testmode):
    ret = snap.enabled(name)
    assert ret["result"] is not False
    if changes:
        assert (ret["result"] is None) is testmode
        assert name in ret["changes"]["enabled"]
        assert "nabled the snap" in ret["comment"]
        assert ("Would have" in ret["comment"]) is testmode
    else:
        assert ret["result"] is True
        assert not ret["changes"]


@pytest.mark.parametrize("name,changes", (("hello-world", True), ("core18", False)))
def test_disabled(name, changes, testmode):
    ret = snap.disabled(name)
    assert ret["result"] is not False
    if changes:
        assert (ret["result"] is None) is testmode
        assert name in ret["changes"]["disabled"]
        assert "isabled the snap" in ret["comment"]
        assert ("Would have" in ret["comment"]) is testmode
    else:
        assert ret["result"] is True
        assert not ret["changes"]


@pytest.mark.parametrize("name,changes", (("hello-world", True), ("foobar", False)))
def test_removed(name, changes, testmode):
    ret = snap.removed(name)
    assert ret["result"] is not False
    if changes:
        assert (ret["result"] is None) is testmode
        assert name in ret["changes"]["removed"]
        assert "emoved the snap" in ret["comment"]
        assert ("Would have" in ret["comment"]) is testmode
    else:
        assert ret["result"] is True
        assert not ret["changes"]


@pytest.mark.parametrize(
    "name,service,enable,changes",
    (
        ("hello-world", "foo", None, False),
        ("hello-world", "foo", True, False),
        ("yubioath-desktop", "ei", True, ("started",)),
        ("yubioath-desktop", "di", None, ("started",)),
        ("yubioath-desktop", "di", True, ("started", "enabled")),
        ("yubioath-desktop", "da", None, False),
        ("yubioath-desktop", "da", True, ("enabled",)),
    ),
)
def test_service_running(name, service, enable, changes, testmode):
    ret = snap.service_running(name, service=service, enabled=enable)
    assert ret["result"] is not False
    if changes:
        assert (ret["result"] is None) is testmode
        for change in changes:
            assert f"{name}.{service}" in ret["changes"][change]
        assert "tarted/enabled some services" in ret["comment"]
        assert ("Would have" in ret["comment"]) is testmode
    else:
        assert ret["result"] is True
        assert not ret["changes"]


@pytest.mark.parametrize("enable", (None, False, True))
def test_service_running_multi(enable, testmode):
    ret = snap.service_running("yubioath-desktop", enabled=enable)
    assert ret["result"] is not False
    assert (ret["result"] is None) is testmode
    changes = {"di", "ei"}
    if enable:
        changes.add("da")
    unchanged = {"di", "ei", "da", "ea"}.difference(changes)
    for serv in changes:
        assert (f"yubioath-desktop.{serv}" in ret["changes"]["started"]) is serv.endswith("i")
        assert (f"yubioath-desktop.{serv}" in ret["changes"].get("enabled", [])) is bool(
            enable and serv.startswith("d")
        )
    for serv in unchanged:
        assert all(serv not in changed for changed in ret["changes"].values())
    assert "tarted/enabled some services" in ret["comment"]
    assert ("Would have" in ret["comment"]) is testmode


@pytest.mark.parametrize(
    "name,service,disable,changes",
    (
        ("yubioath-desktop", "di", None, False),
        ("yubioath-desktop", "di", True, False),
        ("yubioath-desktop", "da", True, ("stopped",)),
        ("yubioath-desktop", "ea", None, ("stopped",)),
        ("yubioath-desktop", "ea", True, ("stopped", "disabled")),
        ("yubioath-desktop", "ei", None, False),
        ("yubioath-desktop", "ei", True, ("disabled",)),
    ),
)
def test_service_dead(name, service, disable, changes, testmode):
    ret = snap.service_dead(name, service=service, disabled=disable)
    assert ret["result"] is not False
    if changes:
        assert (ret["result"] is None) is testmode
        for change in changes:
            assert f"{name}.{service}" in ret["changes"][change]
        assert "topped/disabled some services" in ret["comment"]
        assert ("Would have" in ret["comment"]) is testmode
    else:
        assert ret["result"] is True
        assert not ret["changes"]


@pytest.mark.parametrize("disable", (None, False, True))
def test_service_dead_multi(disable, testmode):
    ret = snap.service_dead("yubioath-desktop", disabled=disable)
    assert ret["result"] is not False
    assert (ret["result"] is None) is testmode
    changes = {"da", "ea"}
    if disable:
        changes.add("di")
    unchanged = {"di", "ei", "da", "ea"}.difference(changes)
    for serv in changes:
        assert (f"yubioath-desktop.{serv}" in ret["changes"]["stopped"]) is serv.endswith("a")
        assert (f"yubioath-desktop.{serv}" in ret["changes"].get("disabled", [])) is bool(
            disable and serv.startswith("e")
        )
    for serv in unchanged:
        assert all(serv not in changed for changed in ret["changes"].values())
    assert "topped/disabled some services" in ret["comment"]
    assert ("Would have" in ret["comment"]) is testmode


@pytest.mark.parametrize(
    "name,service,reload,change",
    (
        ("hello-world", "foo", False, "restarted"),
        ("hello-world", "foo", True, "reloaded"),
        ("yubioath-desktop", "ei", False, "started"),
        ("yubioath-desktop", "ei", True, "started"),
    ),
)
def test_service_running_mod_watch(name, service, reload, change, testmode):
    ret = snap.mod_watch(name, "service_running", service=service, reload=reload)
    assert ret["result"] is not False
    assert (ret["result"] is None) is testmode
    assert f"{name}.{service}" in ret["changes"][change]
    assert "(re)started some services" in ret["comment"]
    assert ("Would have" in ret["comment"]) is testmode


@pytest.mark.parametrize("reload", (False, True))
def test_service_running_mod_watch_multi(reload, testmode):
    ret = snap.mod_watch("yubioath-desktop", "service_running", reload=reload)
    assert ret["result"] is not False
    assert (ret["result"] is None) is testmode
    started = {"di", "ei"}
    restarted = {"da", "ea"}
    assert set(ret["changes"]["started"]) == {f"yubioath-desktop.{serv}" for serv in started}
    assert set(ret["changes"]["reloaded" if reload else "restarted"]) == {
        f"yubioath-desktop.{serv}" for serv in restarted
    }
    assert "(re)started some services" in ret["comment"]
    assert ("Would have" in ret["comment"]) is testmode


@pytest.mark.parametrize(
    "name,service,change",
    (
        ("hello-world", "foo", "stopped"),
        ("yubioath-desktop", "di", False),
    ),
)
def test_service_dead_mod_watch(name, service, change, testmode):
    ret = snap.mod_watch(name, "service_dead", service=service)
    assert ret["result"] is not False
    if change:
        assert (ret["result"] is None) is testmode
        assert f"{name}.{service}" in ret["changes"][change]
        assert "topped some services" in ret["comment"]
        assert ("Would have" in ret["comment"]) is testmode
    else:
        assert ret["result"] is True
        assert not ret["changes"]


def test_service_dead_mod_watch_multi(testmode):
    ret = snap.mod_watch("yubioath-desktop", "service_dead")
    assert ret["result"] is not False
    assert (ret["result"] is None) is testmode
    stopped = {"da", "ea"}
    assert set(ret["changes"]["stopped"]) == {f"yubioath-desktop.{serv}" for serv in stopped}
    assert "topped some services" in ret["comment"]
    assert ("Would have" in ret["comment"]) is testmode


@pytest.mark.parametrize("func", ("enabled", "disabled"))
@pytest.mark.parametrize("err", ("is not installed", "something else went wrong"))
def test_en_dis_abled_error_handling(err, func, snap_is_enabled_mock, testmode):
    snap_is_enabled_mock.side_effect = CommandExecutionError(err)
    ret = getattr(snap, func)("hello-world")
    if err == "is not installed":
        assert (ret["result"] is None) is testmode
    else:
        assert ret["result"] is False
    assert err in ret["comment"]
    assert not ret["changes"]


@pytest.mark.usefixtures("testmode")
@pytest.mark.parametrize("testmode", (False,))
@pytest.mark.parametrize("func,tgt", (("enabled", "core18"), ("disabled", "hello-world")))
def test_en_dis_abled_validation(func, tgt, snap_enable_mock, snap_disable_mock):
    snap_enable_mock.side_effect = snap_disable_mock.side_effect = None
    ret = getattr(snap, func)(tgt)
    assert ret["result"] is False
    assert "but it is still" in ret["comment"]
    assert not ret["changes"]


@pytest.mark.parametrize(
    "name,channel,revision,held,changes",
    (
        ("hello-world", None, None, None, False),
        (
            "hello-world",
            "latest/edge",
            None,
            True,
            {"channel": {"old": "latest/stable", "new": "latest/edge"}},
        ),
        (
            "hello-world",
            None,
            29,
            False,
            {"revision": {"old": "28", "new": "29"}, "held": {"old": True, "new": False}},
        ),
        (
            "hello-world",
            None,
            "latest",
            None,
            {"revision": {"old": "28", "new": "29"}},
        ),
        (
            "core",
            None,
            "latest",
            None,
            False,
        ),
        (
            "new-snap",
            None,
            None,
            None,
            {"installed": "new-snap"},
        ),
        (
            "core",
            None,
            "latest",
            True,
            {"held": {"old": False, "new": True}},
        ),
    ),
)
def test_installed(name, channel, revision, held, changes, testmode):
    ret = snap.installed(name, channel=channel, revision=revision, held=held)
    assert ret["result"] is not False
    if changes:
        assert (ret["result"] is None) is testmode
        assert ret["changes"] == changes
        if "installed" in changes:
            assert "nstalled the snap" in ret["comment"]
        else:
            assert "odified the snap" in ret["comment"]
        assert ("Would have" in ret["comment"]) is testmode
    else:
        assert ret["result"] is True
        assert not ret["changes"]


@pytest.mark.usefixtures("testmode")
@pytest.mark.parametrize("testmode", (False,))
def test_installed_validation_install(snap_install_mock):
    snap_install_mock.side_effect = None
    ret = snap.installed("hello-foo")
    assert ret["result"] is False
    assert "could not be found afterwards" in ret["comment"]
    assert not ret["changes"]


@pytest.mark.usefixtures("testmode")
@pytest.mark.parametrize("testmode", (False,))
def test_installed_validation_modify(snap_install_mock):
    snap_install_mock.side_effect = None
    ret = snap.installed("hello-world", channel="stable/edge", revision=29)
    assert ret["result"] is False
    assert "pending changes" in ret["comment"]
    assert not ret["changes"]


@pytest.mark.usefixtures("testmode")
@pytest.mark.parametrize("testmode", (False,))
def test_removed_validation(snap_remove_mock):
    snap_remove_mock.side_effect = None
    ret = snap.removed("hello-world")
    assert ret["result"] is False
    assert "is still present" in ret["comment"]
    assert not ret["changes"]


@pytest.mark.parametrize("mod_watch", (True, False))
@pytest.mark.parametrize("func", ("service_running", "service_dead"))
@pytest.mark.parametrize("err", ("", "something else went wrong"))
def test_service_missing_error_handling(err, func, mod_watch, snap_services_mock, testmode):
    if err:
        snap_services_mock.side_effect = CommandExecutionError(err)
    params = {"name": "nonexistent"}
    if mod_watch:
        params["sfun"] = func
        func = "mod_watch"
    ret = getattr(snap, func)(**params)
    if err:
        assert ret["result"] is False
        assert err in ret["comment"]
    else:
        assert (ret["result"] is None) is testmode
        assert "Did not find any service to manage" in ret["comment"]
        assert ("this would be an error" in ret["comment"]) is testmode
    assert not ret["changes"]


@pytest.mark.usefixtures("testmode")
@pytest.mark.parametrize("testmode", (False,))
@pytest.mark.parametrize("func", ("service_running", "service_dead"))
@pytest.mark.parametrize("mod_watch", (True, False))
def test_service_timer(func, mod_watch, snap_service_running_mock):
    if func == "service_running":
        exp_ret = False
        serv = "ei"
    else:
        exp_ret = True
        serv = "da"
    snap_service_running_mock.side_effect = None
    snap_service_running_mock.return_value = exp_ret
    params = {"name": "yubioath-desktop", "service": serv}
    if mod_watch:
        params["sfun"] = func
        func = "mod_watch"
    with patch("time.sleep"), patch("time.time", side_effect=(0, 0, 5, 11)):
        ret = getattr(snap, func)(**params)
    assert ret["result"] is False
    assert "but it is still" in ret["comment"]
    assert not ret["changes"]


@pytest.mark.usefixtures("testmode")
@pytest.mark.parametrize("testmode", (False,))
@pytest.mark.parametrize("func", ("service_running", "service_dead"))
@pytest.mark.parametrize("mod_watch", (True, False))
def test_multi_service_error_handling(
    func, mod_watch, snap_service_start_mock, snap_service_stop_mock
):
    if func == "service_running":
        _prev_func = snap_service_start_mock.side_effect
        serv = "ei"
    else:
        _prev_func = snap_service_stop_mock.side_effect
        serv = "da"

    def _err(name, **kwargs):
        if name[-2:] == serv:
            raise CommandExecutionError("I like you anyways")
        return _prev_func(name, **kwargs)

    snap_service_start_mock.side_effect = snap_service_stop_mock.side_effect = _err

    params = {"name": "yubioath-desktop"}
    if mod_watch:
        params["sfun"] = func
        func = "mod_watch"
    ret = getattr(snap, func)(**params)
    assert ret["result"] is False
    assert "Encountered some errors" in ret["comment"]
    assert f"yubioath-desktop.{serv}: I like you anyways" in ret["comment"]
    assert ret["changes"]
    assert all(f"yubioath-desktop.{serv}" not in changes for changes in ret["changes"].values())


@pytest.mark.parametrize(
    "name,value,changes",
    (
        ("system.timezone", "UTC", False),
        ("system.timezone", "PST", {"old": "UTC", "new": "PST"}),
        ("system.timezone", None, {"old": "UTC", "new": None, "unset": True}),
        ("experimental.foo", False, {"old": None, "new": False, "set": True}),
    ),
)
def test_option_managed(name, value, changes, testmode):
    ret = snap.option_managed("core", option=name, value=value)
    assert ret["result"] is not False
    if changes:
        assert (ret["result"] is None) is testmode
        assert "odified some options" in ret["comment"]
        assert ("Would have" in ret["comment"]) is testmode
        assert ret["changes"]
        assert ret["changes"] == {name: changes}
    else:
        assert ret["result"] is True
        assert not ret["changes"]
        assert "correct state" in ret["comment"]


@pytest.mark.parametrize(
    "options,changes",
    (
        ({"system.timezone": "UTC", "system.hostname": "foobar"}, False),
        (
            {"system.timezone": "PST", "system.hostname": "foobar"},
            {"system.timezone": {"old": "UTC", "new": "PST"}},
        ),
        (
            {"system.timezone": None, "system.hostname": "foobar"},
            {"system.timezone": {"old": "UTC", "new": None, "unset": True}},
        ),
        (
            {"experimental.foo": True, "system.hostname": "foobar"},
            {"experimental.foo": {"old": None, "new": True, "set": True}},
        ),
        (
            {"experimental.foo": "foo", "system.hostname": "bar", "system.timezone": None},
            {
                "experimental.foo": {"old": None, "new": "foo", "set": True},
                "system.timezone": {"old": "UTC", "new": None, "unset": True},
                "system.hostname": {"old": "foobar", "new": "bar"},
            },
        ),
    ),
)
def test_option_managed_multi(options, changes, testmode):
    ret = snap.option_managed("core", options=options)
    assert ret["result"] is not False
    if changes:
        assert (ret["result"] is None) is testmode
        assert "odified some options" in ret["comment"]
        assert ("Would have" in ret["comment"]) is testmode
        assert ret["changes"]
        assert ret["changes"] == changes
    else:
        assert ret["result"] is True
        assert not ret["changes"]
        assert "correct state" in ret["comment"]


@pytest.mark.parametrize("err", ("is not installed", "something else went wrong"))
def test_option_managed_error_handling(err, snap_options_mock, testmode):
    snap_options_mock.side_effect = CommandExecutionError(err)
    ret = snap.option_managed("core", option="system.foo", value="bar")
    if err == "is not installed":
        assert (ret["result"] is None) is testmode
    else:
        assert ret["result"] is False
    assert err in ret["comment"]
    assert not ret["changes"]


@pytest.mark.usefixtures("testmode")
@pytest.mark.parametrize("testmode", (False,))
def test_option_managed_multi_error_handling(snap_option_set_mock, snap_option_unset_mock):
    fail = ("system.hostname", "system.fail", "system.timezone")

    def make_err(prev):
        def _err(name, option, *args, **kwargs):
            if option in fail:
                raise CommandExecutionError("I like you anyways")
            return prev(name, option, *args, **kwargs)

        return _err

    snap_option_set_mock.side_effect = make_err(snap_option_set_mock.side_effect)
    snap_option_unset_mock.side_effect = make_err(snap_option_unset_mock.side_effect)

    options = {
        "system.timezone": None,
        "system.hostname": "foo",
        "system.fail": "wut",
        "seed.loaded": False,
        "cloud.name": "unknown",
    }
    ret = snap.option_managed("core", options=options)
    assert ret["result"] is False
    assert "Encountered some errors" in ret["comment"]
    for opt in fail:
        assert f"{opt}: I like you anyways" in ret["comment"]
    assert ret["changes"]
    assert all(opt not in ret["changes"] for opt in fail)
    assert ret["changes"]["seed.loaded"] == {"old": True, "new": False}


@pytest.mark.usefixtures("testmode")
@pytest.mark.parametrize("testmode", (False,))
def test_option_managed_validation(snap_option_set_mock):
    snap_option_set_mock.side_effect = None
    ret = snap.option_managed("core", "foo.bar", "baz")
    assert ret["result"] is False
    assert "pending changes" in ret["comment"]
    assert not ret["changes"]


@pytest.mark.parametrize(
    "name,value,options",
    (
        (None, NOT_SET, None),
        ("foo", NOT_SET, None),
        (None, "foo", None),
        ("foo", "bar", {"baz": "quux"}),
    ),
)
def test_option_managed_requires_either_name_and_value_or_dict(name, value, options, testmode):
    """
    Check that requirements are fulfilled and that value has to be set explicitly
    (since None is a meaningful value here).
    """
    err = "are required"
    if name and value and options:
        err = "not both"
    ret = snap.option_managed("core", option=name, value=value, options=options)
    assert ret["result"] is False
    assert err in ret["comment"]
    assert not ret["changes"]
