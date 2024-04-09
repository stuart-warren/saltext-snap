import json
import logging
import re
import shlex

import salt.utils.path
import salt.utils.yaml
from salt.exceptions import CommandExecutionError
from salt.exceptions import SaltInvocationError

log = logging.getLogger(__name__)

__virtualname__ = "snap"
__func_alias__ = {
    "list_": "list",
}

LIST_RE = None
SERVICE_RE = None

RISK_LEVELS = ("stable", "candidate", "beta", "edge")


def __virtual__():
    if salt.utils.path.which("snap"):
        return __virtualname__
    return False, "Missing `snap` command in PATH"


def __init__(_):
    global LIST_RE
    global SERVICE_RE
    LIST_RE = re.compile(
        r"^(?P<name>\S+)\s+(?P<version>\S+)\s+(?P<revision>\S+)\s+(?P<channel>\S+)\s+(?P<publisher>\S+)\s+(?P<notes>\S+)"
    )
    SERVICE_RE = re.compile(r"^(?P<name>\S+)\s+(?P<startup>\S+)\s+(?P<status>\S+)\s+(?P<notes>\S+)")


def disable(name):
    """
    Disable a snap.

    CLI Example:

    .. code-block:: bash

        salt '*' snap.disable hello-world

    name
        The name of the snap.
    """
    cmd = ["snap", "disable", name]
    _run(cmd)
    return True


def enable(name):
    """
    Enable a snap.

    CLI Example:

    .. code-block:: bash

        salt '*' snap.en able hello-world

    name
        The name of the snap.
    """
    cmd = ["snap", "enable", name]
    _run(cmd)
    return True


def info(name, verbose=False):
    """
    Show information about a snap. It does not have to be installed.

    CLI Example:

    .. code-block:: bash

        salt '*' snap.info hello-world

    name
        The name of the snap.

    verbose
        Include more details on the snap.
    """
    cmd = ["snap", "info", "--unicode=never", "--color=never"]
    if verbose:
        cmd.append("--verbose")
    cmd.append(name)
    return salt.utils.yaml.load(_run(cmd))


def install(name, channel=None, revision=None, classic=False, refresh=False):
    """
    Install a snap.

    CLI Example:

    .. code-block:: bash

        salt '*' snap.install hello-world

    name
        The name of the snap.

    channel
        Follow this channel instead of stable.

    revision
        Install this revision instead of the latest one available
        in the channel.

    classic
        Enable classic mode and disable security confinement.
        Defaults to false.

    refresh
        Update an already installed snap instead of installing a new one.
        This can also be used to modify installation parameters like the channel.
        Defaults to false.
    """
    cmd = ["snap", "refresh" if refresh else "install", "--unicode=never", "--color=never"]
    if channel:
        chan = channel.split("/")
        if len(chan) > 3:
            raise SaltInvocationError(
                f"Invalid channel name '{channel}', must follow <track>/<risk_level>[/<branch>]"
            )
        if len(chan) == 1:
            if chan[0] in RISK_LEVELS:
                risk_level = chan[0]
            else:
                risk_level = "stable"
        else:
            risk_level = chan[1]
        if risk_level not in RISK_LEVELS:
            raise SaltInvocationError(
                f"Invalid channel risk level '{risk_level}', valid: {', '.join(RISK_LEVELS)}"
            )
        cmd.extend(["--channel", channel])
    if revision is not None:
        cmd.extend(["--revision", str(revision)])
    if classic:
        cmd.append("--classic")
    cmd.append(name)
    res = _run(cmd, full=True)
    if not refresh and "is already installed" in res["stderr"]:
        raise CommandExecutionError(res["stderr"])
    return True


def is_enabled(name):
    """
    Check whether a snap is enabled.

    CLI Example:

    .. code-block:: bash

        salt '*' snap.is_enabled hello-world

    name
        The name of the snap.
    """
    snapinfo = list_(name)
    if not snapinfo:
        raise CommandExecutionError(f'snap "{name}" is not installed')
    return "disabled" not in snapinfo[name]["notes"]


def is_installed(name):
    """
    Check whether a snap is installed.

    CLI Example:

    .. code-block:: bash

        salt '*' snap.is_installed hello-world

    name
        The name of the snap.
    """
    return bool(list_(name, revisions=True))


def is_uptodate(name=None):
    """
    Check whether a snap/all installed snaps are up to date.

    CLI Example:

    .. code-block:: bash

        salt '*' snap.is_uptodate
        salt '*' snap.is_uptodate hello-world

    name
        The name of the snap. Optional. If missing, will check all snaps.
    """
    if name and not is_installed(name):
        raise CommandExecutionError(f'snap "{name}" is not installed')
    if name is None:
        return not bool(list_upgrades())
    return name not in list_upgrades()


def list_(name=None, revisions=False):
    """
    List all installed snaps.

    CLI Example:

    .. code-block:: bash

        salt '*' snap.list
        salt '*' snap.list hello-world

    name
        Filter for the name of this snap. Optional.

    revisions
        List all revisions. Defaults to false.
    """
    cmd = ["snap", "list", "--unicode=never", "--color=never"]
    if revisions:
        # Not sure if the data structure as it is currently works here
        cmd.append("--all")
    if name:
        cmd.append(name)
    try:
        return _parse_list(_run(cmd, ignore_retcode=bool(name)))
    except CommandExecutionError as err:
        if name and "no matching snaps installed" in str(err):
            return {}
        raise


def list_upgrades():
    """
    List available upgrades.

    CLI Example:

    .. code-block:: bash

        salt '*' snap.list_upgrades
    """
    cmd = ["snap", "refresh", "--unicode=never", "--color=never", "--list"]
    ret = _parse_list(_run(cmd))
    for data in ret.values():
        data["size"] = data.pop("channel")
    return ret


def options(name, option=None):
    """
    Get a snap's configuration option(s).
    If a value has not been set, returns None.

    CLI Example:

    .. code-block:: bash

        salt '*' snap.option core
        salt '*' snap.option core system.timezone

    name
        The name of the snap.

    option
        The name of the option. Nested keys are concatenated with a dot.
        Optional. If omitted, lists all configuration options.
    """
    if not is_installed(name):
        # it happily returns an empty dict in this case
        raise CommandExecutionError(f'snap "{name}" is not installed')
    cmd = ["snap", "get", "-d", name]
    if option:
        cmd.append(option)
    try:
        return _flatten_dict(json.loads(_run(cmd)))
    except CommandExecutionError as err:
        if option and f'has no "{option}" configuration option' in str(err):
            return None
        raise


def option_set(name, option, value):
    """
    Set a snap configuration option.

    CLI Example:

    .. code-block:: bash

        salt '*' snap.option_set system experimental.parallel-instances false

    name
        The name of the snap.

    option
        The name of the option. Nested keys are concatenated with a dot.

    value
        The value to set.
    """
    cmd = ["snap", "set", "-t", name, f"{option}={json.dumps(value)}"]
    _run(cmd)
    return True


def option_unset(name, option):
    """
    Get a snap's configuration option(s).

    CLI Example:

    .. code-block:: bash

        salt '*' snap.option_unset system experimental.parallel-instances

    name
        The name of the snap.

    option
        The name of the option. Nested keys are concatenated with a dot.

    value
        The value to set.
    """
    cmd = ["snap", "unset", name, option]
    _run(cmd)
    return True


def purge(name, revision=None):
    """
    Remove a snap without saving a snapshot of its data.

    CLI Example:

    .. code-block:: bash

        salt '*' snap.purge hello-world

    name
        The name of the snap.

    revision
        Remove this revision only. Optional.
    """
    return remove(name, revision=revision, purge=True)


def refresh(name, channel=None, revision=None, classic=False):
    """
    Upgrade an installed snap or change some installation parameters.

    CLI Example:

    .. code-block:: bash

        salt '*' snap.info hello-world

    name
        The name of the snap.

    channel
        Follow this channel instead of stable.

    revision
        Install this revision instead of the latest one available
        in the channel.

    classic
        Enable classic mode and disable security confinement.
        Defaults to false.
    """
    return install(name, channel=channel, revision=revision, classic=classic, refresh=True)


def remove(name, revision=None, purge=False):
    """
    Remove a snap.

    CLI Example:

    .. code-block:: bash

        salt '*' snap.remove hello-world

    name
        The name of the snap.

    revision
        Remove this revision only. Optional.

    purge
        Don't save a snapshot of its data. Defaults to false.
    """
    cmd = ["snap", "remove"]
    if purge:
        cmd.append("--purge")
    if revision is not None:
        cmd.extend(("--revision", str(revision)))
    cmd.append(name)
    _run(cmd)
    return True


def service_enabled(name):
    """
    Check if a snap's service is enabled to run at boot.

    CLI Example:

    .. code-block:: bash

        salt '*' snap.service_enabled yubioath-desktop.pcscd

    name
        The name of the snap.
    """
    try:
        return services()[name]["enabled"]
    except KeyError as err:
        raise CommandExecutionError(f"No such service: '{name}'") from err


def service_running(name):
    """
    Check if a snap's service is currently running.

    CLI Example:

    .. code-block:: bash

        salt '*' snap.service_running yubioath-desktop.pcscd

    name
        The name of the snap.
    """
    try:
        return services()[name]["running"]
    except KeyError as err:
        raise CommandExecutionError(f"No such service: '{name}'") from err


def service_start(name, enable=False):
    """
    Start a snap's service(s).

    CLI Example:

    .. code-block:: bash

        salt '*' snap.service_start yubioath-desktop.pcscd
        salt '*' snap.service_start yubioath-desktop

    name
        The name of the snap or one of its services.
    """
    cmd = ["snap", "start"]
    if enable:
        cmd.append("--enable")
    cmd.append(name)
    _run(cmd)
    return True


def service_stop(name, disable=False):
    """
    Stop a snap's service(s).

    CLI Example:

    .. code-block:: bash

        salt '*' snap.service_stop yubioath-desktop.pcscd
        salt '*' snap.service_stop yubioath-desktop

    name
        The name of the snap or one of its services.
    """
    cmd = ["snap", "stop"]
    if disable:
        cmd.append("--disable")
    cmd.append(name)
    _run(cmd)
    return True


def service_restart(name, reload=False):
    """
    Restart a snap's service(s).

    CLI Example:

    .. code-block:: bash

        salt '*' snap.service_restart yubioath-desktop.pcscd
        salt '*' snap.service_restart yubioath-desktop

    name
        The name of the snap or one of its services.
    """
    cmd = ["snap", "restart"]
    if reload:
        cmd.append("--reload")
    cmd.append(name)
    _run(cmd)
    return True


def services(name=None, snap=None):
    """
    List snap services and their status.

    CLI Example:

    .. code-block:: bash

        salt '*' snap.services

    name
        Only return information about this specific service.

    snap
        Only return information about services that belong
        to this snap.
    """
    cmd = ["snap", "services"]
    res = _parse_list(_run(cmd), regex=SERVICE_RE)
    res = {
        name: {
            "enabled": serv["startup"] == "enabled",
            "running": serv["status"] == "active",
            "notes": serv["notes"],
        }
        for name, serv in res.items()
    }
    if name:
        try:
            return {name: res[name]}
        except KeyError as err:
            raise CommandExecutionError(f"No such service: '{name}'") from err
    if snap:
        return {name: status for name, status in res.items() if name.startswith(f"{snap}.")}
    return res


def upgrade_all():
    """
    Upgrade all snaps.

    CLI Example:

    .. code-block:: bash

        salt '*' snap.upgrade_all
    """
    cmd = ["snap", "refresh", "--unicode=never", "--color=never"]
    _run(cmd)
    return True


def _parse_list(data, regex=None):
    regex = regex or LIST_RE  # since it's initialized late
    ret = {}
    for line in data.splitlines()[1:]:
        match = regex.match(line)
        if match:
            parsed = match.groupdict()
            notes = parsed.pop("notes", "")
            if notes == "-":
                notes = []
            else:
                notes = notes.split(",")
            parsed["notes"] = notes
            ret[parsed["name"]] = parsed
    return ret


def _run(cmd, ignore_retcode=False, full=False):
    params = {
        "python_shell": False,
        "ignore_retcode": ignore_retcode,
    }
    res = __salt__["cmd.run_all"](shlex.join(cmd), **params)
    if res["retcode"]:
        raise CommandExecutionError(res["stderr"])
    if full:
        return res
    return res["stdout"]


def _flatten_dict(data, prefix=""):
    ret = {}
    if prefix:
        prefix = f"{prefix}."
    for key, val in data.items():
        if isinstance(val, dict) and val:
            ret.update(_flatten_dict(val, prefix=f"{prefix}{key}"))
            continue
        ret[f"{prefix}{key}"] = val
    return ret
