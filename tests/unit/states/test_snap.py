from unittest.mock import Mock
from unittest.mock import patch

import pytest
from salt.defaults import NOT_SET
from salt.exceptions import CommandExecutionError

import saltext.snap.modules.snap_mod as snap_module
import saltext.snap.states.snap_mod as snap


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

    def _list(name=None, **kwargs):  # pylint: disable=unused-argument
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
    def _install(
        name, channel=None, revision=None, classic=False, refresh=False
    ):  # pylint: disable=unused-argument
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
    def _remove(name, **kwargs):  # pylint: disable=unused-argument
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
    def _restart(name, **kwargs):  # pylint: disable=unused-argument
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
    def _set(name, option, value):  # pylint: disable=unused-argument
        snap_options[option] = value
        return True

    return Mock(spec=snap_module.option_set, side_effect=_set)


@pytest.fixture
def snap_option_unset_mock(snap_options):
    def _unset(name, option):  # pylint: disable=unused-argument
        snap_options.pop(option)
        return True

    return Mock(spec=snap_module.option_unset, side_effect=_unset)


@pytest.fixture
def snap_ack_mock():
    return Mock(spec=snap_module.ack, return_value=True)


@pytest.fixture
def snap_known_mock(snap_known):
    return Mock(spec=snap_module.known, return_value=[snap_known[-2]])


@pytest.fixture
def snap_info_mock(snap_info_file):
    return Mock(spec=snap_module.info, return_value=snap_info_file)


@pytest.fixture
def snap_connections_mock(snap_connections_name, snap_connections_core):
    def _connections(name=None, **kwargs):  # pylint: disable=unused-argument
        if name == "core":
            return snap_connections_core
        return snap_connections_name

    return Mock(spec=snap_module.connections, side_effect=_connections)


@pytest.fixture
def snap_plugs_mock(snap_plugs):
    def _plugs(name, plug=None, interface=None, **kwargs):  # pylint: disable=unused-argument
        if name != "bitwarden":
            return {}
        if plug is not None:
            if plug in snap_plugs:
                return {plug: snap_plugs[plug]}
            return {}
        if interface is not None:
            for slot, data in snap_plugs.items():
                if data["interface"] == interface:
                    return {slot: data}
            return {}
        return snap_plugs

    return Mock(spec=snap_module.plugs, side_effect=_plugs)


@pytest.fixture
def snap_slots_mock(snap_slots):
    def _slots(name, slot=None, interface=None, **kwargs):  # pylint: disable=unused-argument
        if name != "core":
            return {}
        ret = snap_slots
        if interface is not None:
            ret = {k: v for k, v in snap_slots.items() if v["interface"] == interface}
        if slot is not None:
            if slot in ret:
                return {slot: ret[slot]}
            return {}
        return ret

    return Mock(spec=snap_module.slots, side_effect=_slots)


@pytest.fixture
def snap_connect_mock(snap_connections_name, snap_plugs, snap_slots):
    def _connect(name, plug, *args, **kwargs):  # pylint: disable=unused-argument
        snap_slots[plug]["connections"].append({"snap": name, "plug": plug})
        snap_plugs[plug]["connections"].append({"snap": "core", "slot": plug})
        snap_connections_name["established"].append(
            {
                "slot": {"snap": "core", "slot": plug},
                "plug": {"snap": name, "plug": plug},
                "interface": plug,
            }
        )
        snap_connections_name["plugs"].append(
            {
                "snap": name,
                "plug": plug,
                "interface": plug,
                "apps": [name],
                "connections": [{"snap": "core", "slot": plug}],
            }
        )
        snap_connections_name["slots"].append(
            {
                "snap": "core",
                "plug": plug,
                "interface": plug,
                "apps": [name],
                "connections": [{"snap": name, "plug": plug}],
            }
        )
        return True

    return Mock(spec=snap_module.connect, side_effect=_connect)


@pytest.fixture
def snap_disconnect_mock(snap_connections_name, snap_connections_core, snap_plugs, snap_slots):
    def _disconnect_plug(name, plug, **kwargs):  # pylint: disable=unused-argument
        snap_slots[plug]["connections"].remove({"snap": name, "plug": plug})
        snap_plugs[plug]["connections"].remove({"snap": "core", "slot": plug})
        snap_connections_name["established"].remove(
            {
                "slot": {"snap": "core", "slot": plug},
                "plug": {"snap": name, "plug": plug},
                "interface": plug,
            }
        )
        snap_connections_name["plugs"].remove(
            {
                "snap": name,
                "plug": plug,
                "interface": plug,
                "apps": [name],
                "connections": [{"snap": "core", "slot": plug}],
            }
        )
        snap_connections_name["slots"].remove(
            {
                "snap": "core",
                "slot": plug,
                "interface": plug,
                "connections": [{"snap": name, "plug": plug}],
            }
        )
        return True

    def _find_slot(slot):
        return next(iter(x for x in snap_connections_core["slots"] if x["slot"] == slot))

    def _disconnect_slot(name, slot, target=None, **kwargs):  # pylint: disable=unused-argument
        if target is None:
            targets = ["bitwarden", "bw"]
        else:
            targets = [target.split(":")[0]]
        if "bitwarden" in targets:
            snap_slots[slot]["connections"].remove({"snap": "bitwarden", "plug": slot})
            snap_plugs[slot]["connections"].remove({"snap": "core", "slot": slot})
            snap_connections_name["established"].remove(
                {
                    "slot": {"snap": "core", "slot": slot},
                    "plug": {"snap": "bitwarden", "plug": slot},
                    "interface": slot,
                }
            )
            snap_connections_name["plugs"].remove(
                {
                    "snap": "bitwarden",
                    "plug": slot,
                    "interface": slot,
                    "apps": ["bitwarden"],
                    "connections": [{"snap": "core", "slot": slot}],
                }
            )
            snap_connections_name["slots"].remove(
                {
                    "snap": "core",
                    "slot": slot,
                    "interface": slot,
                    "connections": [{"snap": "bitwarden", "plug": slot}],
                }
            )
        slot_inst = _find_slot(slot)
        for tgt in targets:
            snap_connections_core["established"].remove(
                {
                    "slot": {"snap": "core", "slot": slot},
                    "plug": {"snap": tgt, "plug": slot},
                    "interface": slot,
                }
            )
            slot_inst["connections"].remove({"snap": tgt, "plug": slot})
            snap_connections_core["plugs"].remove(
                {
                    "snap": tgt,
                    "apps": [tgt],
                    "plug": slot,
                    "interface": slot,
                    "connections": [{"snap": "core", "slot": slot}],
                }
            )
        return True

    def _disconnect(name, connector, **kwargs):
        if name == "core":
            return _disconnect_slot(name, connector, **kwargs)
        if name == "bitwarden":
            return _disconnect_plug(name, connector, **kwargs)
        raise RuntimeError("Undefined test behavior")

    return Mock(spec=snap_module.disconnect, side_effect=_disconnect)


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
    snap_known_mock,
    snap_ack_mock,
    snap_info_mock,
    snap_connections_mock,
    snap_plugs_mock,
    snap_slots_mock,
    snap_connect_mock,
    snap_disconnect_mock,
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
                "snap.known": snap_known_mock,
                "snap.ack": snap_ack_mock,
                "snap.info": snap_info_mock,
                "snap.connections": snap_connections_mock,
                "snap.plugs": snap_plugs_mock,
                "snap.slots": snap_slots_mock,
                "snap.connect": snap_connect_mock,
                "snap.disconnect": snap_disconnect_mock,
            },
            "__opts__": {
                "test": testmode,
            },
        },
    }


@pytest.fixture(params=(False, True))
def testmode(request):
    return request.param


@pytest.mark.parametrize(
    "plug,target,changes",
    (
        ("network", None, False),
        ("password-manager-service", None, "core:password-manager-service"),
        ("password-manager-service", "core", "core:password-manager-service"),
        (
            "password-manager-service",
            "core:password-manager-service",
            "core:password-manager-service",
        ),
    ),
)
def test_connected(plug, target, changes, testmode):
    ret = snap.connected("bitwarden", plug, target)
    assert ret["result"] is not False
    if changes:
        assert (ret["result"] is None) is testmode
        assert ret["changes"]["connected"] == changes
        assert f"onnected plug bitwarden:{plug}" in ret["comment"]
        assert ("Would have" in ret["comment"]) is testmode
    else:
        assert ret["result"] is True
        assert not ret["changes"]


# Cannot use snap_module.SnapNotFound here because it is reloaded by the
# execution module tests, making the isinstance test fail.
@pytest.mark.parametrize("err", ("SnapNotFound", "something else went wrong"))
def test_connected_error_handling(err, snap_connections_mock, testmode):
    err = getattr(snap_module, err, err)
    if isinstance(err, str):
        err = CommandExecutionError(err)
    else:
        err = err("hello-world")
    snap_connections_mock.side_effect = err
    ret = snap.connected("bitwardenn", "network")
    if isinstance(err, snap_module.SnapNotFound):
        assert (ret["result"] is None) is testmode
    else:
        assert ret["result"] is False
    assert str(err) in ret["comment"]
    assert not ret["changes"]


@pytest.mark.usefixtures("testmode")
@pytest.mark.parametrize("testmode", (False,), indirect=True)
def test_connected_validation(snap_connect_mock):
    snap_connect_mock.side_effect = None
    ret = snap.connected("bitwarden", "password-manager-service")
    assert ret["result"] is False
    assert "connection is not reported" in ret["comment"]
    assert not ret["changes"]


@pytest.mark.usefixtures("testmode")
def test_connected_target_discovery_no_plug(snap_plugs_mock):
    snap_plugs_mock.side_effect = None
    snap_plugs_mock.return_value = {}
    ret = snap.connected("bitwarden", "password-manager-service", target="core")
    assert ret["result"] is False
    assert "does not have a plug named" in ret["comment"]
    assert not ret["changes"]


@pytest.mark.usefixtures("testmode")
def test_connected_target_discovery_no_slot(snap_slots_mock):
    snap_slots_mock.side_effect = None
    snap_slots_mock.return_value = {}
    ret = snap.connected("bitwarden", "password-manager-service", target="core")
    assert ret["result"] is False
    assert "does not expose exactly one slot with interface type" in ret["comment"]
    assert not ret["changes"]


@pytest.mark.usefixtures("testmode")
def test_connected_target_discovery_multiple_slots(snap_slots_mock):
    snap_slots_mock.side_effect = None
    snap_slots_mock.return_value = {
        "slot-a": {"interface": "password-manager-service"},
        "slot-b": {},
    }
    ret = snap.connected("bitwarden", "password-manager-service", target="core")
    assert ret["result"] is False
    assert "does not expose exactly one slot with interface type" in ret["comment"]
    assert not ret["changes"]


# Cannot use snap_module.SnapNotFound here because it is reloaded by the
# execution module tests, making the isinstance test fail.
@pytest.mark.parametrize("err", ("SnapNotFound", "something else went wrong"))
def test_connected_target_discovery_error_handling(err, snap_slots_mock, testmode):
    err = getattr(snap_module, err, err)
    if isinstance(err, str):
        err = CommandExecutionError(err)
    else:
        err = err("hello-world")
    snap_slots_mock.side_effect = err
    ret = snap.connected("bitwarden", "network", target="core")
    if isinstance(err, snap_module.SnapNotFound):
        assert (ret["result"] is None) is testmode
    else:
        assert ret["result"] is False
    assert str(err) in ret["comment"]
    assert not ret["changes"]


@pytest.mark.parametrize(
    "name,connector,target,changes",
    (
        ("bitwarden", "password-manager-service", None, False),
        ("bitwarden", "password-manager-service", "core:password-manager-service", False),
        ("bitwarden", "network", None, {"slots": ["core:network"]}),
        ("bitwarden", "network", "core:network", {"slots": ["core:network"]}),
        ("bitwarden", "network", "foo:network", False),
        ("core", "network", "bitwarden:network", {"plugs": ["bitwarden:network"]}),
        ("core", "network", "foo:network", False),
        ("core", "network", None, {"plugs": ["bitwarden:network", "bw:network"]}),
    ),
)
def test_disconnected(name, connector, target, changes, testmode):
    ret = snap.disconnected(name, connector, target=target)
    assert ret["result"] is not False
    if changes:
        typ = next(iter(changes))[:-1]
        assert (ret["result"] is None) is testmode
        assert set(ret["changes"]["disconnected"][f"{typ}s"]) == set(changes[f"{typ}s"])
        assert f"isconnected some {typ}s" in ret["comment"]
        assert ("Would have" in ret["comment"]) is testmode
    else:
        assert ret["result"] is True
        assert not ret["changes"]


@pytest.mark.usefixtures("testmode")
def test_disconnected_no_connector(snap_plugs_mock, snap_slots_mock):
    snap_plugs_mock.side_effect = snap_slots_mock.side_effect = None
    snap_plugs_mock.return_value = snap_slots_mock.return_value = {}
    ret = snap.disconnected("bitwarden", "foo")
    assert ret["result"] is False
    assert "carries neither a slot nor a plug" in ret["comment"]
    assert not ret["changes"]


# Cannot use snap_module.SnapNotFound here because it is reloaded by the
# execution module tests, making the isinstance test fail.
@pytest.mark.parametrize("err", ("SnapNotFound", "something else went wrong"))
def test_disconnected_error_handling(err, snap_plugs_mock, testmode):
    err = getattr(snap_module, err, err)
    if isinstance(err, str):
        err = CommandExecutionError(err)
    else:
        err = err("bitwarden")
    snap_plugs_mock.side_effect = err
    ret = snap.disconnected("bitwarden", "network")
    if isinstance(err, snap_module.SnapNotFound):
        assert (ret["result"] is None) is testmode
    else:
        assert ret["result"] is False
    assert str(err) in ret["comment"]
    assert not ret["changes"]


@pytest.mark.usefixtures("testmode")
@pytest.mark.parametrize("testmode", (False,), indirect=True)
def test_disconnected_validation(snap_disconnect_mock):
    snap_disconnect_mock.side_effect = None
    ret = snap.disconnected("bitwarden", "network")
    assert ret["result"] is False
    assert "some connections remained" in ret["comment"]
    assert not ret["changes"]


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


# Cannot use snap_module.SnapNotFound here because it is reloaded by the
# execution module tests, making the isinstance test fail.
@pytest.mark.parametrize("err", ("SnapNotFound", "something else went wrong"))
@pytest.mark.parametrize("func", ("enabled", "disabled"))
def test_en_dis_abled_error_handling(err, func, snap_is_enabled_mock, testmode):
    err = getattr(snap_module, err, err)
    if isinstance(err, str):
        err = CommandExecutionError(err)
    else:
        err = err("hello-world")
    snap_is_enabled_mock.side_effect = err
    ret = getattr(snap, func)("hello-world")
    if isinstance(err, snap_module.SnapNotFound):
        assert (ret["result"] is None) is testmode
    else:
        assert ret["result"] is False
    assert str(err) in ret["comment"]
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
def test_installed(
    name,
    channel,
    revision,
    held,
    changes,
    snap_install_mock,
    snap_hold_mock,
    snap_unhold_mock,
    testmode,
):
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
        if tuple(changes) != ("held",):
            assert bool(snap_install_mock.call_count) is not (testmode)
        else:
            snap_install_mock.assert_not_called()
        if "held" in changes and not testmode:
            if changes["held"]["new"]:
                snap_hold_mock.assert_called_once_with(name)
            else:
                snap_unhold_mock.assert_called_once_with(name)
        else:
            snap_hold_mock.assert_not_called()
            snap_unhold_mock.assert_not_called()

    else:
        assert ret["result"] is True
        assert not ret["changes"]
        snap_install_mock.assert_not_called()
        snap_hold_mock.assert_not_called()
        snap_unhold_mock.assert_not_called()


@pytest.mark.skip_on_windows
@pytest.mark.parametrize(
    "name,changes,asserts_imported",
    (
        ("/tmp/bw_60.snap", False, True),
        ("/tmp/bw_61.snap", {"revision": {"old": "60", "new": "61"}}, True),
        ("/tmp/bw2_60.snap", {"installed": "/tmp/bw2_60.snap"}, True),
        ("/tmp/bw2_60.snap", {"installed": "/tmp/bw2_60.snap"}, False),
    ),
)
def test_installed_with_file(
    name,
    changes,
    asserts_imported,
    snap_info_mock,
    snap_known_mock,
    snap_install_mock,
    snap_list_mock,
    snap_ack_mock,
    snap_info_file,
    snap_list,
    testmode,
):
    def _reinstall(*args, **kwargs):  # pylint: disable=unused-argument
        snap_list["bw"]["revision"] = "61"

    def _install(*args, **kwargs):  # pylint: disable=unused-argument
        snap_list["bw2"] = snap_list["bw"].copy()

    if changes:
        if "revision" in changes:
            snap_known_mock.return_value[0]["snap-revision"] = 61
            snap_install_mock.side_effect = _reinstall
        elif "installed" in changes:
            snap_info_file["name"] = "bw2"
            snap_install_mock.side_effect = _install
            if not asserts_imported:
                snap_known_mock.side_effect = ([], snap_known_mock.return_value)

    snap_info_mock.return_value = snap_info_file
    with patch("pathlib.Path.exists", return_value=True):
        ret = snap.installed(name, assertions="/tmp/bw2_60.assert")
    assert ret["result"] is not False
    exp_name = "bw2" if changes and "installed" in changes else "bw"
    if changes:
        assert (ret["result"] is None) is testmode
        assert ret["changes"] == changes
        if "installed" in changes:
            assert "nstalled the snap" in ret["comment"]
        else:
            assert "odified the snap" in ret["comment"]
        assert ("Would have" in ret["comment"]) is testmode
        assert bool(snap_install_mock.call_count) is not testmode
    else:
        assert ret["result"] is True
        assert not ret["changes"]
        snap_install_mock.assert_not_called()
    if asserts_imported or testmode:
        snap_known_mock.assert_called_once()
    else:
        assert snap_known_mock.call_count == 2
    if asserts_imported or not testmode:
        snap_list_mock.assert_called_with(
            exp_name
        )  # ensure listing uses the snap name, not the path
    assert snap_known_mock.call_args[0] == ("snap-revision",)
    assert snap_known_mock.call_args[1] == {"snap-sha3-384": snap_info_file["sha3-384"]}
    if asserts_imported or testmode:
        snap_ack_mock.assert_not_called()
    else:
        snap_ack_mock.assert_called_once_with("/tmp/bw2_60.assert")


@pytest.mark.usefixtures("testmode")
def test_installed_with_file_requires_absolute_path():
    ret = snap.installed("tmp/bw_60.snap")
    assert ret["result"] is False
    assert "not absolute" in ret["comment"]


@pytest.mark.skip_on_windows
def test_installed_with_file_checks_path_exists(testmode):
    ret = snap.installed("/tmp/bw_60.snap")
    assert (ret["result"] is False) is not testmode
    assert (ret["result"] is None) is testmode
    assert "does not exist" in ret["comment"]
    assert ("would be an error" in ret["comment"]) is testmode


@pytest.mark.skip_on_windows
@pytest.mark.parametrize(
    "assertions,testmode",
    ((None, False), (None, True), ("/tmp/bw_60.snap", False)),
    indirect=("testmode",),
)
def test_installed_with_file_requires_assertions(
    assertions, snap_known_mock, snap_ack_mock, testmode
):
    snap_known_mock.return_value = []
    with patch("pathlib.Path.exists", return_value=True):
        ret = snap.installed("/tmp/bw_60.snap", assertions=assertions)
    assert (ret["result"] is False) is not testmode
    assert (ret["result"] is None) is testmode
    if not assertions:
        assert "Missing assertions" in ret["comment"]
        assert ("would be an error" in ret["comment"]) is testmode
    else:
        snap_ack_mock.assert_called_once()
        assert "still could not find" in ret["comment"]


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


# Cannot use snap_module.SnapNotFound here because it is reloaded by the
# execution module tests, making the isinstance test fail.
@pytest.mark.parametrize("err", ("SnapNotFound", "something else went wrong"))
def test_option_managed_error_handling(err, snap_options_mock, testmode):
    err = getattr(snap_module, err, err)
    if isinstance(err, str):
        err = CommandExecutionError(err)
    else:
        err = err("hello-world")
    snap_options_mock.side_effect = err
    ret = snap.option_managed("core", option="system.foo", value="bar")
    if isinstance(err, snap_module.SnapNotFound):
        assert (ret["result"] is None) is testmode
    else:
        assert ret["result"] is False
    assert str(err) in ret["comment"]
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


@pytest.mark.usefixtures("testmode")
@pytest.mark.parametrize(
    "name,value,options",
    (
        (None, NOT_SET, None),
        ("foo", NOT_SET, None),
        (None, "foo", None),
        ("foo", "bar", {"baz": "quux"}),
    ),
)
def test_option_managed_requires_either_name_and_value_or_dict(name, value, options):
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
