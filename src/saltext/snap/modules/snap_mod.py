import json
import logging
import re
import shlex
from datetime import datetime

import salt.utils.path
import salt.utils.yamlloader
import yaml
from salt.exceptions import CommandExecutionError
from salt.exceptions import SaltInvocationError

try:
    import requests
    from urllib3.connection import HTTPConnection
    from urllib3.connectionpool import HTTPConnectionPool
    from urllib.parse import urlencode
    from requests.adapters import HTTPAdapter

    HAS_REQUESTS = True
    import socket
except ImportError:
    HAS_REQUESTS = False


log = logging.getLogger(__name__)

__virtualname__ = "snap"
__func_alias__ = {
    "list_": "list",
}

LIST_RE = None
SERVICE_RE = None

RISK_LEVELS = ("stable", "candidate", "beta", "edge")
CKEY = "_snapd_conn"
LIST_VERBOSE_FILTER = ("contact", "description", "icon", "links", "media", "website")


def __virtual__():
    if salt.utils.path.which("snap"):
        return __virtualname__
    return False, "Missing `snap` command in PATH"


def __init__(_):
    global LIST_RE
    global SERVICE_RE
    # This regex is a best effort, but some special rows will not match,
    # usually because of empty fields (in try mode, for example)
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

        salt '*' snap.enable hello-world

    name
        The name of the snap.
    """
    cmd = ["snap", "enable", name]
    _run(cmd)
    return True


def hold(name, duration=None):
    """
    Exclude a snap from general refreshes.

    CLI Example:

    .. code-block:: bash

        salt '*' snap.hold hello-world

    name
        The name of the snap.

    duration
        Optional duration to hold for, specified as a time string
        with a unit. If unspecified, holds forever until the snap
        is manually unheld.
    """
    hold = "--hold"
    if duration:
        hold += f"={duration}"
    cmd = ["snap", "refresh", hold, name]
    _run(cmd)
    return True


def unhold(name):
    """
    Remove a hold on a snap.

    CLI Example:

    .. code-block:: bash

        salt '*' snap.unhold hello-world

    name
        The name of the snap.
    """
    cmd = ["snap", "refresh", "--unhold", name]
    _run(cmd)
    return True


def info(name, verbose=False):
    """
    Show information about a snap. It does not have to be installed.

    CLI Example:

    .. code-block:: bash

        salt '*' snap.info hello-world
        salt '*' snap.info '[hello-world, core]'

    name
        The name(s) of the snap(s).

    verbose
        Include more details on the snap.
    """
    # Using the API here would require heavy modifications and
    # two separate calls ( /find?name={name} and /snaps/{name})
    # to get similar output to the CLI.
    # A benefit would be rich channel and app/service information.
    cmd = ["snap", "info", "--unicode=never", "--color=never"]
    if verbose:
        cmd.append("--verbose")
    if not isinstance(name, list):
        name = [name]
    cmd.extend(name)
    ret = {}
    for nam, snap in zip(
        name, list(yaml.load_all(_run(cmd), Loader=salt.utils.yaml.SaltYamlSafeLoader))
    ):
        if "warning" in snap:
            log.warning(snap["warning"])
            snap = {}

        ret[nam] = snap
    if len(ret) == 1:
        return ret[next(iter(ret))]
    return ret


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
    return snapinfo[name]["enabled"]


def is_held(name):
    """
    Check whether a snap is held.

    CLI Example:

    .. code-block:: bash

        salt '*' snap.is_held hello-world

    name
        The name of the snap.
    """
    snapinfo = list_(name)
    if not snapinfo:
        raise CommandExecutionError(f'snap "{name}" is not installed')
    return snapinfo[name]["held"]


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


def is_uptodate(name=None, exclude_held=False):
    """
    Check whether a snap/all installed snaps are up to date.

    CLI Example:

    .. code-block:: bash

        salt '*' snap.is_uptodate
        salt '*' snap.is_uptodate hello-world

    name
        The name of the snap. Optional. If missing, will check all snaps.

    exclude_held
        Count held snaps as up to date. Defaults to False.
    """
    if name and not is_installed(name):
        raise CommandExecutionError(f'snap "{name}" is not installed')
    if name is None:
        return not bool(list_upgrades(exclude_held=exclude_held))
    return name not in list_upgrades(exclude_held=exclude_held)


def list_(name=None, revisions=False, verbose=False):
    """
    List all installed snaps.

    CLI Example:

    .. code-block:: bash

        salt '*' snap.list
        salt '*' snap.list hello-world
        salt '*' snap.list '[hello-world, core]'

    name
        Filter for the name(s) of specified snap(s). Optional.

    revisions
        List all revisions. Defaults to false.

    verbose
        List more detailed information. This requires being able to query the
        REST API (``requests`` lib). Defaults to false
    """
    if HAS_REQUESTS:
        return _list_api(name, revisions, verbose=verbose)
    if verbose:
        raise CommandExecutionError("Cannot query REST API, missing `requests` library.")
    return _list_cli(name, revisions)


def list_upgrades(exclude_held=False):
    """
    List available upgrades.

    CLI Example:

    .. code-block:: bash

        salt '*' snap.list_upgrades

    exclude_held
        Don't list held snaps as upgradable. Defaults to False.
    """
    cmd = ["snap", "refresh", "--unicode=never", "--color=never", "--list"]
    ret = _parse_list(_run(cmd))
    for data in ret.values():
        data["size"] = data.pop("channel")
    if exclude_held:
        snaps = list_(list(ret))
        ret = {snap: data for snap, data in ret.items() if not snaps[snap]["held"]}
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


def _parse_list(data, regex=None, duplicate=False):
    regex = regex or LIST_RE  # since it's initialized late
    ret = {}
    for line in data.splitlines()[1:]:
        match = regex.match(line)
        if not match:
            continue
        parsed = match.groupdict()
        notes = parsed.pop("notes", "")
        if notes == "-":
            notes = []
        else:
            notes = notes.split(",")
        parsed["notes"] = notes
        if duplicate:
            if parsed["name"] not in ret:
                ret[parsed["name"]] = []
            ret[parsed["name"]].append(parsed)
        else:
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


# https://stackoverflow.com/a/59594889


class SnapdConnection(HTTPConnection):
    def __init__(self):
        super().__init__("localhost")

    def connect(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.connect("/run/snapd.socket")

    def close(self):
        self.sock.close()


class SnapdConnectionPool(HTTPConnectionPool):
    def __init__(self):
        super().__init__("localhost")

    def _new_conn(self):
        return SnapdConnection()


class SnapdAdapter(HTTPAdapter):
    def get_connection(self, url, proxies=None):
        return SnapdConnectionPool()


class SnapdApi:
    def __init__(self, conn):
        self.conn = conn

    def get(self, path, query=None, **kwargs):
        return self._check(self.conn.get(self._uri(path, query), **kwargs))

    def post(self, path, query=None, **kwargs):
        return self._check(self.conn.post(self._uri(path, query), **kwargs))

    def patch(self, path, query=None, **kwargs):
        return self._check(self.conn.patch(self._uri(path, query), **kwargs))

    def delete(self, path, query=None, **kwargs):
        return self._check(self.conn.delete(self._uri(path, query), **kwargs))

    def _check(self, res):
        data = res.json()
        if data["status-code"] >= 400:
            raise CommandExecutionError(f"{data['type']}: {data['result']['message']}")
        return data["result"]

    def _uri(self, path, query):
        path = path.lstrip("/")
        suffix = "?"
        if query:
            for param, val in query.items():
                if isinstance(val, list):
                    query[param] = ",".join(val)
            suffix += urlencode(query)
        return f"http://snapd/v2/{path}{suffix}"


def _conn():
    if CKEY not in __context__:
        session = requests.Session()
        session.mount("http://snapd/", SnapdAdapter())
        __context__[CKEY] = SnapdApi(session)
    return __context__[CKEY]


def _list_api(name=None, revisions=False, verbose=False):
    """
    This is the preferred method of listing installed snaps,
    but requires ``requests``.
    """
    query = {}
    if name:
        if not isinstance(name, list):
            name = [name]
        query["snaps"] = name
    if revisions:
        query["all"] = True
    res = _conn().get("snaps", query)
    ret = {}
    for snap in res:
        name = snap["name"]
        if verbose:
            parsed = {k: v for k, v in snap.items() if k not in LIST_VERBOSE_FILTER}
        else:
            parsed = {
                "channel": snap["tracking-channel"],
                "name": name,
                "notes": [],
                "publisher": snap["publisher"]["username"],
                "revision": snap["revision"],
                "version": snap["version"],
                "devmode": snap["devmode"],
            }
            if snap["type"] == "base":
                parsed["notes"].append("base")
            if snap["confinement"] == "classic":  # ?
                parsed["notes"].append("classic")
            if snap["type"] == "os":
                parsed["notes"].append("core")
            if snap["devmode"]:
                parsed["notes"].append("devmode")
            if snap["status"] == "installed":
                parsed["notes"].append("disabled")
            if snap["publisher"]["validation"] == "verified":
                parsed["publisher"] += "**"
            elif snap["publisher"]["validation"] == "starred":
                parsed["publisher"] += "*"
        parsed["enabled"] = snap["status"] == "active"
        parsed["classic"] = snap["confinement"] == "classic"
        if "hold" in snap:
            held_until = _time(snap["hold"])
            parsed["held"] = datetime.now(tz=held_until.tzinfo) < held_until
            if parsed["held"]:
                parsed["notes"].append("held")
        else:
            parsed["held"] = False
        parsed["notes"].sort()
        if name not in ret and revisions:
            ret[name] = []
        if revisions:
            ret[name].append(parsed)
            continue
        # We don't need to account for multiple revisions being listed
        # since the API has the same parameter as the CLI
        ret[name] = parsed

    return ret


def _time(iso):
    try:
        return datetime.fromisoformat(iso)
    except ValueError:
        # Python < 3.11
        iso = re.sub(r"\.[\d]+", "", iso)
        iso = re.sub(r"Z$", "+00:00", iso)
        return datetime.fromisoformat(iso)


def _list_cli(name=None, revisions=False):
    """
    Fallback for listing snaps via CLI.

    This has some issues since
      * the tracking channel's branch is cropped
      * some rows have empty fields (try mode, for example)
    """
    # It could mostly be fixed by only listing the names and then
    # running those through snap info --verbose though.
    def _amend(data):
        data["enabled"] = "disabled" not in data["notes"]
        data["classic"] = "classic" in data["notes"]
        data["devmode"] = "devmode" in data["notes"]
        data["held"] = "held" in data["notes"]

    cmd = ["snap", "list", "--unicode=never", "--color=never"]
    if revisions:
        cmd.append("--all")
    if name:
        if not isinstance(name, list):
            name = [name]
        cmd.extend(name)
    try:
        ret = _parse_list(_run(cmd, ignore_retcode=bool(name)), duplicate=revisions)
    except CommandExecutionError as err:
        if name and "no matching snaps installed" in str(err):
            return {}
        raise
    for info in ret.values():
        if revisions:
            for rev in info:
                _amend(rev)
        else:
            _amend(info)
    return ret
