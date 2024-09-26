"""
Manage snaps, plugs and snap services statefully.
"""

import json
import logging
import time
from pathlib import Path

from salt.defaults import NOT_SET
from salt.exceptions import CommandExecutionError
from salt.exceptions import SaltInvocationError

log = logging.getLogger(__name__)


__virtualname__ = "snap"


class NoServices(CommandExecutionError):
    """
    Raised when no services to manage can be found
    """


def __virtual__():
    try:
        __salt__["snap.list"]  # pylint: disable=pointless-statement
        return __virtualname__
    except KeyError:
        return False, "Did not find `snap` execution module"


def connected(name, connector, target=None):
    """
    Ensure a snap's plug is connected.

    name
        The name of the snap to connect.

    connector
        The name of the snap's plug to connect.

    target
        A specification for the slot to connect to. Optional.
        Full spec: ``<snap_name>:<slot_name>``.
        If left unspecified, connects the plug to a slot of the
        core snap with a name matching ``plug``.
        If specified as a snap name only, connects the plug to
        the only slot in the provided snap that matches the connection
        interface, but fails if multiple potential slots exist.
    """
    ret = {
        "name": name,
        "result": True,
        "comment": "The connection is already established",
        "changes": {},
    }
    try:
        if target is None:
            target = f"core:{connector}"
        elif ":" not in target:
            try:
                interface = __salt__["snap.plugs"](name)[connector]["interface"]
            except KeyError as err:
                raise SaltInvocationError(
                    f"The snap '{name}' does not have a plug named '{connector}'"
                ) from err
            try:
                possible_slots = __salt__["snap.slots"](target, interface=interface)
            except CommandExecutionError as err:
                if "is not installed" not in str(err) or not __opts__["test"]:
                    raise
                ret["result"] = None
                ret["comment"] = str(err) + " - if we weren't testing, this would be an error"
                return ret
            if len(possible_slots) != 1:
                raise SaltInvocationError(
                    f"The target snap '{target}' does not expose exactly one slot with interface type '{interface}', but {len(possible_slots)}"
                )
            target = f"{target}:{next(iter(possible_slots))}"
        try:
            curr = __salt__["snap.connections"](name)
        except CommandExecutionError as err:
            if "is not installed" not in str(err) or not __opts__["test"]:
                raise
            ret["result"] = None
            ret["comment"] = str(err) + " - if we weren't testing, this would be an error"
            return ret
        target_snap, target_slot = target.split(":", maxsplit=1)
        for conn in curr["established"]:
            if (
                conn["plug"]["plug"] == connector
                and conn["slot"]["snap"] == target_snap
                and conn["slot"]["slot"] == target_slot
            ):
                return ret
        if __opts__["test"]:
            ret["result"] = None
            ret["comment"] = (
                f"Would have connected plug {name}:{connector} to slot "
                f"{target_snap}:{target_slot}"
            )
            ret["changes"]["connected"] = f"{target_snap}:{target_slot}"
            return ret
        __salt__["snap.connect"](name, connector, target=target)
        curr_new = __salt__["snap.connections"](name)
        for conn in curr_new["established"]:
            if (
                conn["plug"]["plug"] == connector
                and conn["slot"]["snap"] == target_snap
                and conn["slot"]["slot"] == target_slot
            ):
                ret["comment"] = (
                    f"Connected plug {name}:{connector} to slot {target_snap}:{target_slot}"
                )
                ret["changes"]["connected"] = f"{target_snap}:{target_slot}"
                return ret
        raise CommandExecutionError("Tried to connect the plug, but the connection is not reported")
    except (CommandExecutionError, SaltInvocationError) as err:
        ret["result"] = False
        ret["comment"] = str(err)
        ret["changes"] = {}
    return ret


def disconnected(name, connector, target=None):
    """
    Ensure a snap's plug(s)/slot(s) is/are connected.

    name
        The name of the snap.

    connector
        The name of the snap's plug/slot to disconnect.

    target
        A specification for the slot/plug to disconnect from in the format
        `<snap_name>:<slot_or_plug_name>``. Optional.
        If left unspecified, disconnects all connections of the plug/slot.
    """
    ret = {"name": name, "result": True, "comment": "The connection is already cut", "changes": {}}
    try:
        try:
            if __salt__["snap.plugs"](name, connector):
                typ = "slot"
                this = "plug"
            elif __salt__["snap.slots"](name, connector):
                typ = "plug"
                this = "slot"
            else:
                raise SaltInvocationError(
                    "The snap carries neither a slot nor a plug with this name"
                )
        except CommandExecutionError as err:
            if "is not installed" not in str(err) or not __opts__["test"]:
                raise
            ret["result"] = None
            ret["comment"] = str(err) + " - if we weren't testing, this would be an error"
            return ret
        curr = __salt__["snap.connections"](name)
        disconnect = []
        target_snap = target_entity = None
        if target:
            target_snap, target_entity = target.split(":", maxsplit=1)
        for conn in curr["established"]:
            if conn[this]["snap"] != name or conn[this][this] != connector:
                continue
            if target and (conn[typ]["snap"] != target_snap or conn[typ][typ] != target_entity):
                continue
            disconnect.append((conn[typ]["snap"], conn[typ][typ]))
        if not disconnect:
            return ret
        if __opts__["test"]:
            ret["result"] = None
            ret["comment"] = f"Would have disconnected some {typ}s"
            ret["changes"]["disconnected"] = {
                f"{typ}s": [f"{tgt}:{ent}" for tgt, ent in disconnect]
            }
            return ret
        __salt__["snap.disconnect"](name, connector, target=target)
        curr_new = __salt__["snap.connections"](name)
        still_present = []
        for conn in curr_new["established"]:
            if conn[this]["snap"] != name or conn[this][this] != connector:
                continue
            if target and (conn[typ]["snap"] != target_snap or conn[typ][typ] != target_entity):
                continue
            still_present.append((conn[typ]["snap"], conn[typ][typ]))
        actually_disconnected = [
            f"{tgt}:{ent}" for tgt, ent in set(disconnect).difference(still_present)
        ]
        if actually_disconnected:
            ret["changes"]["disconnected"] = {
                f"{typ}s": [
                    f"{tgt}:{ent}" for tgt, ent in set(disconnect).difference(still_present)
                ]
            }
        if still_present:
            ret["result"] = False
            ret["comment"] = f"Tried to disconnect some {typ}s, but some connections remained"
            return ret
        ret["comment"] = f"Disconnected some {typ}s"
    except (CommandExecutionError, SaltInvocationError) as err:
        ret["result"] = False
        ret["comment"] = str(err)
        ret["changes"] = {}
    return ret


def enabled(name):
    """
    Ensure a snap is enabled.

    name
        The name of the snap.
    """
    ret = {"name": name, "result": True, "comment": "The snap is already enabled", "changes": {}}
    try:
        try:
            if __salt__["snap.is_enabled"](name):
                return ret
        except CommandExecutionError as err:
            if "is not installed" not in str(err) or not __opts__["test"]:
                raise
            ret["result"] = None
            ret["comment"] = str(err) + " - if we weren't testing, this would be an error"
            return ret
        ret["changes"]["enabled"] = name
        if __opts__["test"]:
            ret["result"] = None
            ret["comment"] = "Would have enabled the snap"
            return ret
        __salt__["snap.enable"](name)
        if not __salt__["snap.is_enabled"](name):
            raise CommandExecutionError("Tried to enable the snap, but it is still disabled")
        ret["comment"] = "Enabled the snap"
    except (CommandExecutionError, SaltInvocationError) as err:
        ret["result"] = False
        ret["comment"] = str(err)
        ret["changes"] = {}
    return ret


def disabled(name):
    """
    Ensure a snap is disabled.

    name
        The name of the snap.
    """
    ret = {"name": name, "result": True, "comment": "The snap is already disabled", "changes": {}}
    try:
        try:
            if not __salt__["snap.is_enabled"](name):
                return ret
        except CommandExecutionError as err:
            if "is not installed" not in str(err) or not __opts__["test"]:
                raise
            ret["result"] = None
            ret["comment"] = str(err) + " - if we weren't testing, this would be an error"
            return ret
        ret["changes"]["disabled"] = name
        if __opts__["test"]:
            ret["result"] = None
            ret["comment"] = "Would have disabled the snap"
            return ret
        __salt__["snap.disable"](name)
        if __salt__["snap.is_enabled"](name):
            raise CommandExecutionError("Tried to disable the snap, but it is still enabled")
        ret["comment"] = "Disabled the snap"
    except (CommandExecutionError, SaltInvocationError) as err:
        ret["result"] = False
        ret["comment"] = str(err)
        ret["changes"] = {}
    return ret


def installed(
    name, channel="latest/stable", revision=None, classic=False, held=None, assertions=None
):
    """
    Ensure a snap is installed.

    name
        The name of the snap or a path to a local ``.snap`` file.
        In the latter case, ensure you also possess the accompanying
        assertions and specify the ``assertions`` parameter or import
        them in some other way before this state runs.

    channel
        Follow this channel instead of ``latest/stable``.

    revision
        Install this revision instead of the latest one available
        in the channel. Optional. If unset, will not upgrade after
        installation. Set this to ``latest`` to ensure this snap
        is kept up to date.

    classic
        Enable classic mode and disable security confinement.
        Defaults to false.

    held
        Whether the snap should be excluded from general refreshes.
        Optional. If unset, leaves the setting unmanaged.

    assertions
        When installing a snap from a file, import accompanying assertions
        from this file. Optional (if the assertions are imported otherwise).
    """

    def _check_changes(curr, isfile):
        nonlocal revision
        changes = {}
        if not isfile:
            if channel and curr["channel"] != channel:
                changes["channel"] = {"old": curr["channel"], "new": channel}
            if revision == "latest":
                upgrades = __salt__["snap.list_upgrades"]()
                if name in upgrades:
                    revision = upgrades[name]["revision"]
                else:
                    revision = None
            if held is not None and curr["held"] is not held:
                changes["held"] = {"old": curr["held"], "new": held}
        if revision is not None and curr["revision"] != str(revision):
            changes["revision"] = {"old": curr["revision"], "new": str(revision)}
        return changes

    ret = {
        "name": name,
        "result": True,
        "comment": "The snap is already installed as specified",
        "changes": {},
    }

    try:
        snap_name = name
        isfile = name.endswith(".snap")  # this suffix is required by snap
        if isfile:
            path = Path(name)
            if not path.is_absolute():
                raise SaltInvocationError(f"Specified path '{name}' is not absolute")
            if not path.exists():
                msg = f"Specified path '{name}' does not exist"
                if __opts__["test"]:
                    ret["result"] = None
                    ret["comment"] = f"{msg}. If we weren't testing, ths would be an error"
                    return ret
                raise SaltInvocationError(msg)
            snapinfo = __salt__["snap.info"](name, verbose=True)
            snap_name = snapinfo["name"]
            match = {"snap-sha3-384": snapinfo["sha3-384"]}
            curr_assrts = __salt__["snap.known"]("snap-revision", **match)
            if not curr_assrts:
                if __opts__["test"]:
                    if assertions:
                        msg = "Would have imported assertions and installed the snap"
                        ret["changes"]["installed"] = name
                    else:
                        msg = "Missing assertions. If we weren't testing, this would be an error"
                    ret["result"] = None
                    ret["comment"] = msg
                    return ret
                if not assertions:
                    raise CommandExecutionError(
                        "Missing assertions, either import them or pass the assertions file in `assertions`"
                    )
                __salt__["snap.ack"](assertions)
                curr_assrts = __salt__["snap.known"]("snap-revision", **match)
                if not curr_assrts:
                    raise CommandExecutionError(
                        "Imported assertions, but still could not find snap-revision"
                    )
            revision = curr_assrts[0]["snap-revision"]
        curr = __salt__["snap.list"](snap_name)
        if curr:
            changes = _check_changes(curr[snap_name], isfile)
            verb = "modified"
        else:
            changes = {"installed": name}
            verb = "installed"
        if not changes:
            return ret
        if __opts__["test"]:
            ret["result"] = None
            ret["comment"] = f"Would have {verb} the snap"
            ret["changes"] = changes
            return ret
        held_change = changes.pop("held", None)
        if changes:
            __salt__["snap.install"](
                name,
                channel=channel,
                revision=revision if not isfile else None,
                classic=classic,
                refresh=bool(curr) and not isfile,
            )
            ret["changes"].update(changes)
        if held_change:
            func = "hold" if held else "unhold"
            __salt__[f"snap.{func}"](name)
            ret["changes"].update({"held": held_change})
        new = __salt__["snap.list"](snap_name)
        if not new:
            raise CommandExecutionError(
                f"{verb.capitalize()} the snap, but it could not be found afterwards"
            )
        new_changes = _check_changes(new[snap_name], isfile)
        if new_changes:
            ret["result"] = False
            ret["comment"] = (
                f"{verb.capitalize()} the snap, but there are still "
                f"pending changes: {json.dumps(new_changes)}"
            )
            for change in new_changes:
                ret["changes"].pop(change, None)
            return ret
        ret["comment"] = f"{verb.capitalize()} the snap"
    except (CommandExecutionError, SaltInvocationError) as err:
        ret["result"] = False
        ret["comment"] = str(err)
        ret["changes"] = {}
    return ret


def option_managed(name, option=None, value=NOT_SET, options=None):
    """
    Ensure a snap's options are set as specified.

    name
        The name of the snap.

    option
        The name of the option. Either this and ``value`` or ``options`` is required.

    value
        The value to set.. Either this and ``option`` or ``options`` is required.
        If the value is specified as None/``null`` (YAML), the value will be unset.

    options
        A mapping of option names to their values to set. If an option's value
        is None, it will be unset.
    """

    def _check_changes(data):
        changes = {}
        to_set = []
        to_unset = []
        for opt, val in options.items():
            if val is None:
                if opt in data:
                    changes[opt] = {"old": data[opt], "new": val, "unset": True}
                    to_unset.append(opt)
            elif opt not in data:
                changes[opt] = {"old": None, "new": val, "set": True}
                to_set.append(opt)
            elif data[opt] != val:
                changes[opt] = {"old": data[opt], "new": val}
                to_set.append(opt)
        return changes, to_set, to_unset

    ret = {
        "name": name,
        "result": True,
        "comment": "All options are in the correct state",
        "changes": {},
    }

    try:
        single = option and value is not NOT_SET
        if not (single or options):
            raise SaltInvocationError("Either option and value or options are required")
        if single and options:
            raise SaltInvocationError(
                "Either specify option and value or options, not both variants"
            )
        options = options or {option: value}
        try:
            curr = __salt__["snap.options"](name)
        except CommandExecutionError as err:
            if "is not installed" not in str(err) or not __opts__["test"]:
                raise
            ret["result"] = None
            ret["comment"] = str(err) + " - if we weren't testing, this would be an error"
            return ret
        changes, to_set, to_unset = _check_changes(curr)
        if not changes:
            return ret
        if __opts__["test"]:
            ret["result"] = None
            ret["comment"] = "Would have modified some options"
            ret["changes"] = changes
            return ret
        errs = {}
        for opt in to_unset:
            try:
                __salt__["snap.option_unset"](name, opt)
                ret["changes"][opt] = changes[opt]
            except CommandExecutionError as err:
                errs[opt] = str(err)
        for opt in to_set:
            try:
                __salt__["snap.option_set"](name, opt, changes[opt]["new"])
                ret["changes"][opt] = changes[opt]
            except CommandExecutionError as err:
                errs[opt] = str(err)
        if errs:
            msg = "\n".join(f"{opt}: {err}" for opt, err in errs.items())
            raise CommandExecutionError(f"Encountered some errors:\n{msg}")
        new_changes, _, _ = _check_changes(__salt__["snap.options"](name))
        if new_changes:
            ret["result"] = False
            ret["comment"] = (
                f"Modified some snap options, but there are still "
                f"pending changes: {json.dumps(new_changes)}"
            )
            for change in new_changes:
                ret["changes"].pop(change, None)
            return ret
        ret["comment"] = "Modified some options"
    except (CommandExecutionError, SaltInvocationError) as err:
        ret["result"] = False
        ret["comment"] = str(err)
    return ret


def removed(name, purge=False):
    """
    Ensure a snap is removed.

    name
        The name of the snap.

    purge
        Don't save a snapshot of its data. Defaults to false.
    """
    ret = {"name": name, "result": True, "comment": "The snap is already absent", "changes": {}}

    try:
        curr = __salt__["snap.list"](name)
        if not curr:
            return ret
        ret["changes"]["removed"] = name
        if __opts__["test"]:
            ret["result"] = None
            ret["comment"] = "Would have removed the snap"
            return ret
        __salt__["snap.remove"](name, purge=purge)
        new = __salt__["snap.list"](name)
        if new:
            raise CommandExecutionError("Tried to remove the snap, but it is still present")
        ret["comment"] = "Removed the snap"
    except (CommandExecutionError, SaltInvocationError) as err:
        ret["result"] = False
        ret["comment"] = str(err)
        ret["changes"] = {}
    return ret


def service_running(
    name, service=None, enabled=None, timeout=10
):  # pylint: disable=redefined-outer-name
    """
    Ensure a snap service is running.
    This state supports the ``watch`` requisite.

    name
        The name of the snap.

    service
        Restrict this state to one of its services. Optional.
        If unset, will manage all services of the snap.

    enabled
        Ensure the service is enabled to start at boot time.
        Optional. Can only be set to true.

    timeout
        This state waits for each service. If it is still not at the desired
        state after this amount of seconds, it will fail. Defaults to 10.

    reload
        When the ``watch`` requisite causes a restart, attempt to reload the
        service instead. Defaults to false.
    """
    ret = {
        "name": name,
        "result": True,
        "comment": "All services are in the correct state",
        "changes": {},
    }
    try:
        try:
            start, enable = _check_service_changes(
                name, service, running=True, enabled=enabled or None
            )
        except NoServices as err:
            if not __opts__["test"]:
                raise
            ret["result"] = None
            ret["comment"] = str(err) + " - if we weren't testing, this would be an error"
            return ret
        if not (enable or start):
            return ret
        if __opts__["test"]:
            ret["result"] = None
            ret["comment"] = "Would have started/enabled some services"
            if start:
                ret["changes"]["started"] = start
            if enable:
                ret["changes"]["enabled"] = enable
            return ret
        errs = {}
        ret["changes"] = {"enabled": [], "started": []}
        for serv in set(start + enable):
            try:
                __salt__["snap.service_start"](serv, enable=enabled)
                if serv in start:
                    _timer(
                        __salt__["snap.service_running"],
                        serv,
                        True,
                        timeout,
                        "Tried to start the snap service, but it is still not running",
                    )
                    ret["changes"]["started"].append(serv)
                if serv in enable:
                    _timer(
                        __salt__["snap.service_enabled"],
                        serv,
                        True,
                        timeout if serv not in start else 1,
                        "Tried to enable the snap service, but it is still not enabled",
                    )
                    ret["changes"]["enabled"].append(serv)
            except CommandExecutionError as err:
                errs[serv] = str(err)
        if errs:
            msg = "\n".join(f"{service}: {err}" for service, err in errs.items())
            raise CommandExecutionError(f"Encountered some errors:\n{msg}")
        ret["comment"] = "Started/enabled some services"
    except (CommandExecutionError, SaltInvocationError) as err:
        ret["result"] = False
        ret["comment"] = str(err)
    for typ in ("enabled", "started"):
        if typ in ret["changes"] and not ret["changes"][typ]:
            ret["changes"].pop(typ)
    return ret


def service_dead(
    name, service=None, disabled=None, timeout=10
):  # pylint: disable=redefined-outer-name
    """
    Ensure a snap service is dead.
    This state supports the ``watch`` requisite.

    name
        The name of the snap.

    service
        Restrict this state to one of its services. Optional.
        If unset, will manage all services of the snap.

    disabled
        Ensure the service is disabled (does not start at boot time).
        Optional. Can only be set to true.

    timeout
        This state waits for each service. If it is still not at the desired
        state after this amount of seconds, it will fail. Defaults to 10.
    """
    ret = {
        "name": name,
        "result": True,
        "comment": "All services are in the correct state",
        "changes": {},
    }
    try:
        try:
            stop, disable = _check_service_changes(
                name, service, running=False, enabled=False if disabled else None
            )
        except NoServices as err:
            if not __opts__["test"]:
                raise
            ret["result"] = None
            ret["comment"] = str(err) + " - if we weren't testing, this would be an error"
            return ret
        if not (stop or disable):
            return ret
        if __opts__["test"]:
            ret["result"] = None
            ret["comment"] = "Would have stopped/disabled some services"
            if stop:
                ret["changes"]["stopped"] = stop
            if disable:
                ret["changes"]["disabled"] = disable
            return ret
        errs = {}
        ret["changes"] = {"disabled": [], "stopped": []}
        for serv in set(stop + disable):
            try:
                __salt__["snap.service_stop"](serv, disable=disabled)
                if serv in stop:
                    _timer(
                        __salt__["snap.service_running"],
                        serv,
                        False,
                        timeout,
                        "Tried to stop the snap service, but it is still running",
                    )
                    ret["changes"]["stopped"].append(serv)
                if serv in disable:
                    _timer(
                        __salt__["snap.service_enabled"],
                        serv,
                        False,
                        timeout if serv not in stop else 1,
                        "Tried to disable the snap service, but it is still enabled",
                    )
                    ret["changes"]["disabled"].append(serv)
            except CommandExecutionError as err:
                errs[serv] = str(err)
        if errs:
            msg = "\n".join(f"{service}: {err}" for service, err in errs.items())
            raise CommandExecutionError(f"Encountered some errors:\n{msg}")
        ret["comment"] = "Stopped/disabled some services"
    except (CommandExecutionError, SaltInvocationError) as err:
        ret["result"] = False
        ret["comment"] = str(err)
    for typ in ("disabled", "stopped"):
        if typ in ret["changes"] and not ret["changes"][typ]:
            ret["changes"].pop(typ)
    return ret


def _check_service_changes(name, service, running, enabled):  # pylint: disable=redefined-outer-name
    if service:
        services = __salt__["snap.services"](f"{name}.{service}")
    else:
        services = __salt__["snap.services"](snap=name)
    if not services:
        raise NoServices("Did not find any service to manage")
    running_state = []
    enable_state = []
    for sname, status in services.items():
        if status["running"] is not running:
            running_state.append(sname)
        if enabled is not None and status["enabled"] is not enabled:
            enable_state.append(sname)
    return running_state, enable_state


def _timer(func, serv, check_exp, timeout, msg):
    start_time = time.time()
    while func(serv) is not check_exp:
        if time.time() - start_time > timeout:
            raise CommandExecutionError(msg)
        time.sleep(0.25)


def mod_watch(name, sfun=None, reload=False, **kwargs):
    """
    Support the ``watch`` requisite for ``snap.service_running`` and ``snap.service_dead``.
    """
    ret = {"name": name, "changes": {}, "result": True, "comment": ""}
    pp_suffix = "ed"
    services = {}
    typ_func = {}
    try:
        # Note that we don't have to worry about enabled/disabled since
        # mod_watch would otherwise not run (the normal state would report changes).
        # https://docs.saltproject.io/en/latest/ref/states/requisites.html#watch
        if sfun in ["service_dead", "service_running"]:
            try:
                running_services, _ = _check_service_changes(
                    name, kwargs.get("service"), running=False, enabled=None
                )
            except NoServices as err:
                if not __opts__["test"]:
                    raise
                ret["result"] = None
                ret["comment"] = str(err) + " - if we weren't testing, this would be an error"
                return ret
            if sfun == "service_dead":
                if not running_services:
                    ret["comment"] = "All snap services are already stopped."
                    return ret
                verb = "stop"
                pp_suffix = "ped"
                typ_func[verb] = __salt__["snap.service_stop"]
                services = {verb: running_services}
                check_exp = False

            # "service_running" == sfun evidently
            else:
                check_exp = True
                dead_services, _ = _check_service_changes(
                    name, kwargs.get("service"), running=True, enabled=None
                )
                typ_func = {
                    "start": __salt__["snap.service_start"],
                    "restart": __salt__["snap.service_restart"],
                }
                services["restart"] = running_services
                services["start"] = dead_services
                verb = "(re)start"

        else:
            ret["comment"] = f"Unable to trigger watch for snap.{sfun}"
            ret["result"] = False
            return ret

        if __opts__["test"]:
            ret["result"] = None
            ret["comment"] = f"Would have {verb}{pp_suffix} some services."
            ret["changes"] = {typ + pp_suffix: lst for typ, lst in services.items() if lst}
            if reload and "restarted" in ret["changes"]:
                ret["changes"]["reloaded"] = ret["changes"].pop("restarted")
            return ret

        errs = {}
        ret["changes"] = {typ + pp_suffix: [] for typ in services}
        for typ, lst in services.items():
            params = {}
            if typ == "restart":
                params["reload"] = reload
            for serv in lst:
                try:
                    typ_func[typ](serv, **params)
                    _timer(
                        __salt__["snap.service_running"],
                        serv,
                        check_exp,
                        kwargs.get("timeout", 10),
                        f"Tried to {typ} the snap service, but it is still not {sfun.split('_')[-1]}.",
                    )
                    ret["changes"][typ + pp_suffix].append(serv)
                except CommandExecutionError as err:
                    errs[serv] = str(err)
        if errs:
            msg = "\n".join(f"{service}: {err}" for service, err in errs.items())
            raise CommandExecutionError(f"Encountered some errors:\n{msg}")
        ret["comment"] = f"{verb}{pp_suffix} some services"

    except (CommandExecutionError, SaltInvocationError) as err:
        ret["result"] = False
        ret["comment"] = str(err)

    for typ in services:
        lookup = typ + pp_suffix
        if lookup in ret["changes"] and not ret["changes"][lookup]:
            ret["changes"].pop(lookup)
    if reload and "restarted" in ret["changes"]:
        ret["changes"]["reloaded"] = ret["changes"].pop("restarted")
    return ret
