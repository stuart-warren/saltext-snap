import contextlib
import json
import logging
from importlib import reload
from textwrap import dedent
from unittest.mock import Mock
from unittest.mock import patch

import pytest
import salt.modules.cmdmod
from salt.exceptions import CommandExecutionError
from salt.exceptions import SaltInvocationError

import saltext.snap.modules.snap_mod as snap


@pytest.fixture
def configure_loader_modules(cmd_run):
    module_globals = {
        "__salt__": {"cmd.run_all": cmd_run},
    }
    # It seems the dunder functions are not called by the test suite, need
    # to initialize globals
    snap.__init__(None)  # pylint: disable=unnecessary-dunder-call
    return {
        snap: module_globals,
    }


@pytest.fixture(params=(False,), autouse=True)
def requests_available(request):
    """
    This fixture reloads the execution module to simulate
    a) if True, requests being available
    b) if None, requests being unavailable, but http.client working
    c) if False, requests being unavailable and the REST API requests failing

    This causes issues with references to the module in the global namespace
    of other modules (e.g. state module unit tests).
    Reconsider this if it becomes a problem down the line.
    """
    global snap  # pylint: disable=global-statement
    orig_import = __import__

    def _import_mock(name, *args):
        if name == "requests":
            raise ImportError("No module named requests")
        return orig_import(name, *args)

    req = contextlib.nullcontext()
    conn = contextlib.nullcontext()
    if not request.param:
        req = patch("builtins.__import__", side_effect=_import_mock)
    with req:
        snap = reload(snap)
        snap.__init__(None)  # pylint: disable=unnecessary-dunder-call
        if request.param is False:
            conn = patch("saltext.snap.modules.snap_mod._conn", side_effect=snap.APIConnectionError)
        with conn:
            yield request.param
    snap = reload(snap)
    snap.__init__(None)  # pylint: disable=unnecessary-dunder-call


@pytest.fixture
def cmd_run():
    run = Mock(spec=salt.modules.cmdmod.run_all)

    def _run(*args, **kwargs):  # pylint: disable=unused-argument
        if isinstance(run.return_value, dict):
            return run.return_value
        return {
            "stdout": (
                run.return_value if run.return_value is not None else "potentially gar?bled output"
            ),
            "stderr": "",
            "retcode": 0,
        }

    run.side_effect = _run
    return run


@pytest.fixture
def snap_list_out():
    # the testapp will fail to parse
    return dedent(
        """
            Name               Version                     Rev    Tracking       Publisher          Notes
            bare               1.0                         5      latest/stable  canonical**        base
            bitwarden          2024.4.0                    108    latest/stable  bitwarden**        -
            bw                 2024.3.1                    60     -              bitwarden**        -
            core               16-2.61.2                   16928  latest/stable  canonical**        core
            core18             20231027                    2812   latest/stable  canonical**        base,disabled
            core22             20240111                    1122   latest/stable  canonical**        base
            gnome-3-28-1804    3.28.0-19-g98f9e67.98f9e67  198    latest/stable  canonical**        -
            gnome-3-34-1804    0+git.3556cb3               93     latest/stable  canonical**        -
            gtk-common-themes  0.1-81-g442e511             1535   latest/stable  canonical**        disabled
            hello-world        6.3                         28     latest/stable  canonical**        held
            testapp            1.0                         x2                                       try
            yubioath-desktop   5.0.5                       12     latest/stable  yubico-snap-store  -
        """
    ).strip()


@pytest.fixture
def snap_list_revisions_out():
    return dedent(
        """
            Name               Version                     Rev    Tracking       Publisher          Notes
            bare               1.0                         5      latest/stable  canonical**        base
            bitwarden          2024.4.0                    108    latest/stable  bitwarden**        -
            bw                 2024.3.1                    60     -              bitwarden**        -
            core               16-2.61.2                   16928  latest/stable  canonical**        core
            core18             20231027                    2812   latest/stable  canonical**        base,disabled
            core22             20240111                    1122   latest/stable  canonical**        base
            gnome-3-28-1804    3.28.0-19-g98f9e67.98f9e67  198    latest/stable  canonical**        -
            gnome-3-34-1804    0+git.3556cb3               93     latest/stable  canonical**        -
            gtk-common-themes  0.1-81-g442e511             1535   latest/stable  canonical**        disabled
            hello-world        6.3                         28     latest/stable  canonical**        held
            yubioath-desktop   5.0.5                       12     latest/stable  yubico-snap-store  -
            yubioath-desktop   5.0.4                       11     latest/stable  yubico-snap-store  disabled
            yubioath-desktop   5.0.3                       10     latest/stable  yubico-snap-store  disabled
        """
    ).strip()


@pytest.fixture
def snap_list_api_out():
    return '{"type":"sync","status-code":200,"status":"OK","result":[{"id":"jZLfBRzf1cYlYysIjD2bwSzNtngY0qit","title":"GTK Common Themes","summary":"All the (common) themes","description":"A snap that exports the GTK and icon themes used on various Linux distros.","installed-size":96141312,"name":"gtk-common-themes","publisher":{"id":"canonical","username":"canonical","display-name":"Canonical","validation":"verified"},"developer":"canonical","status":"installed","type":"app","base":"bare","version":"0.1-81-g442e511","channel":"stable","tracking-channel":"latest/stable","ignore-validation":false,"revision":"1535","confinement":"strict","private":false,"devmode":false,"jailmode":false,"mounted-from":"/var/lib/snapd/snaps/gtk-common-themes_1535.snap","links":{"contact":["https://gitlab.gnome.org/Community/Ubuntu/gtk-common-themes/issues"]},"contact":"https://gitlab.gnome.org/Community/Ubuntu/gtk-common-themes/issues"},{"id":"buPKUD3TKqCOgLEjjHx5kSiCpIs5cMuQ","title":"Hello World","summary":"The \'hello-world\' of snaps","description":"This is a simple hello world example.","icon":"/v2/icons/hello-world/icon","installed-size":20480,"install-date":"2024-04-11T12:15:56.850202878+00:00","name":"hello-world","publisher":{"id":"canonical","username":"canonical","display-name":"Canonical","validation":"verified"},"developer":"canonical","status":"active","type":"app","version":"6.3","channel":"","tracking-channel":"latest/stable","ignore-validation":false,"revision":"28","confinement":"strict","private":false,"devmode":false,"jailmode":false,"apps":[{"snap":"hello-world","name":"env"},{"snap":"hello-world","name":"evil"},{"snap":"hello-world","name":"hello-world"},{"snap":"hello-world","name":"sh"}],"mounted-from":"/var/lib/snapd/snaps/hello-world_28.snap","links":{"contact":["mailto:snaps@canonical.com"]},"contact":"mailto:snaps@canonical.com","media":[{"type":"icon","url":"https://dashboard.snapcraft.io/site_media/appmedia/2015/03/hello.svg_NZLfWbh.png","width":256,"height":256},{"type":"screenshot","url":"https://dashboard.snapcraft.io/site_media/appmedia/2018/06/Screenshot_from_2018-06-14_09-33-31.png","width":199,"height":118},{"type":"video","url":"https://vimeo.com/194577403"}],"hold":"2316-07-22T12:19:33.173911003+00:00"},{"id":"osRLU2WSwcWCNSMFOgqpQoE6NPnD7r31","title":"Yubico Authenticator","summary":"2FA with YubiKey","description":"Store your unique credential on a hardware-backed security key and take it wherever you go from mobile to desktop. No more storing sensitive secrets on your mobile phone, leaving your account vulnerable to takeovers. With the Yubico Authenticator you can raise the bar for security.\\n\\nThe Yubico Authenticator generates a one time code used to verify your identity as you’re logging into various services. No connectivity needed! This is based on Open Authentication (OATH) time-based TOTP and event-based HOTP one-time password codes.\\n\\nSetting up the Yubico Authenticator desktop app is easy. Simply download and open the app, insert your YubiKey, and begin adding the accounts you wish to protect by using the QR code provided by each service.\\n\\nExperience security the modern way with the Yubico Authenticator. Visit yubico.com to learn more about the YubiKey and security solutions for mobile.\\n\\nFeatures on desktop include:\\n- Touch Authentication - Touch the YubiKey 5 Series security key to store your credential on the YubiKey\\n- Biometric Authentication - Manage PINs and fingerprints on your FIDO-enabled YubiKeys, as well as add, delete and rename fingerprints on your Yubikey Bio Series keys.\\n- Easy Setup - QR codes available from the services you wish to protect with strong authentication\\n- User Presence - New codes generated with just a touch of the YubiKey\\n- Compatible - Secure all the services currently compatible with other Authenticator apps\\n- Secure - Hardware-backed strong two-factor authentication with secret stored on the YubiKey, not on the desktop\\n- Versatile - Support for multiple work and personal accounts\\n- Portable - Get the same set of codes across our other Yubico Authenticator apps for desktops as well as for all leading mobile platforms\\n- Flexible - Support for time-based and counter-based code generation\\n\\n---\\n\\nThis snap bundles its own version of the pcscd daemon, and is not compatible with running a system-wide version of pcscd.\\n\\nTo stop the system-wide pcscd:\\n\\n   sudo systemctl stop pcscd\\n   sudo systemctl stop pcscd.socket\\n\\nTo restart the bundled pcscd:\\n\\n   sudo snap restart yubioath-desktop.pcscd","icon":"/v2/icons/yubioath-desktop/icon","installed-size":227135488,"install-date":"2024-04-11T12:15:23.66083664+00:00","name":"yubioath-desktop","publisher":{"id":"o2S2GYSCBxilwi1OFNftYfLhm2l3aEzI","username":"yubico-snap-store","display-name":"Yubico","validation":"unproven"},"developer":"yubico-snap-store","status":"active","type":"app","base":"core18","version":"5.0.5","channel":"","tracking-channel":"latest/stable","ignore-validation":false,"revision":"12","confinement":"strict","private":false,"devmode":false,"jailmode":false,"apps":[{"snap":"yubioath-desktop","name":"pcscd","daemon":"simple","daemon-scope":"system","enabled":true,"active":true,"common-id":"com.yubico.pcscd"},{"snap":"yubioath-desktop","name":"yubioath-desktop","desktop-file":"/var/lib/snapd/desktop/applications/yubioath-desktop_yubioath-desktop.desktop","common-id":"com.yubico.yubioath"}],"common-ids":["com.yubico.pcscd","com.yubico.yubioath"],"mounted-from":"/var/lib/snapd/snaps/yubioath-desktop_12.snap","links":{"contact":["https://support.yubico.com/support/tickets/new"],"website":["https://developers.yubico.com/yubioath-desktop"]},"contact":"https://support.yubico.com/support/tickets/new","website":"https://developers.yubico.com/yubioath-desktop","media":[{"type":"icon","url":"https://dashboard.snapcraft.io/site_media/appmedia/2020/05/com.yubico.yubioath.svg.png","width":512,"height":512},{"type":"screenshot","url":"https://dashboard.snapcraft.io/site_media/appmedia/2021/10/Linux-12x-100.jpg","width":2881,"height":1801},{"type":"screenshot","url":"https://dashboard.snapcraft.io/site_media/appmedia/2021/10/Linux-22x-100.jpg","width":2881,"height":1801},{"type":"screenshot","url":"https://dashboard.snapcraft.io/site_media/appmedia/2021/10/Linux-32x-100_1.jpg","width":2881,"height":1801},{"type":"screenshot","url":"https://dashboard.snapcraft.io/site_media/appmedia/2021/10/Linux-42x-100.jpg","width":2881,"height":1801}],"hold":"2024-04-11T12:43:59.00001288+00:00"},{"id":"EISPgh06mRh1vordZY9OZ34QHdd7OrdR","title":"bare","summary":"Empty base snap, useful for testing and fully statically linked snaps","description":"","installed-size":4096,"install-date":"2024-04-11T01:50:47.869171361+00:00","name":"bare","publisher":{"id":"canonical","username":"canonical","display-name":"Canonical","validation":"verified"},"developer":"canonical","status":"active","type":"base","version":"1.0","channel":"stable","tracking-channel":"latest/stable","ignore-validation":false,"revision":"5","confinement":"strict","private":false,"devmode":false,"jailmode":false,"mounted-from":"/var/lib/snapd/snaps/bare_5.snap","links":{"contact":["mailto:snaps@canonical.com"]},"contact":"mailto:snaps@canonical.com"},{"id":"99T7MUlRhtI3U0QFgl5mXXESAiSwt776","title":"core","summary":"snapd runtime environment","description":"The core runtime environment for snapd","installed-size":109043712,"install-date":"2024-04-11T01:42:05.749062355+00:00","name":"core","publisher":{"id":"canonical","username":"canonical","display-name":"Canonical","validation":"verified"},"developer":"canonical","status":"active","type":"os","version":"16-2.61.2","channel":"stable","tracking-channel":"latest/stable","ignore-validation":false,"revision":"16928","confinement":"strict","private":false,"devmode":false,"jailmode":false,"mounted-from":"/var/lib/snapd/snaps/core_16928.snap","links":{"contact":["mailto:snaps@canonical.com"],"website":["https://snapcraft.io"]},"contact":"mailto:snaps@canonical.com","website":"https://snapcraft.io"},{"id":"CSO04Jhav2yK0uz97cr0ipQRyqg0qQL6","title":"Core 18","summary":"Runtime environment based on Ubuntu 18.04","description":"The base snap based on the Ubuntu 18.04 release.","installed-size":58363904,"name":"core18","publisher":{"id":"canonical","username":"canonical","display-name":"Canonical","validation":"verified"},"developer":"canonical","status":"installed","type":"base","version":"20231027","channel":"stable","tracking-channel":"latest/stable","ignore-validation":false,"revision":"2812","confinement":"strict","private":false,"devmode":false,"jailmode":false,"mounted-from":"/var/lib/snapd/snaps/core18_2812.snap","links":{"contact":["https://github.com/snapcore/core18/issues"],"website":["https://snapcraft.io"]},"contact":"https://github.com/snapcore/core18/issues","website":"https://snapcraft.io"},{"id":"n0XNnJXxSdYYHRYwtfYV2mBSkzH1Fbkn","summary":"Bitwarden CLI - A secure and free password manager for all of your devices.","description":"Bitwarden, Inc. is the parent company of 8bit Solutions LLC.\\n\\nNAMED BEST PASSWORD MANAGER BY THE VERGE, U.S. NEWS &amp; WORLD REPORT, CNET, AND MORE.\\n\\nManage, store, secure, and share unlimited passwords across unlimited devices from anywhere. Bitwarden delivers open source password management solutions to everyone, whether at  home, at work, or on the go.\\n\\nGenerate strong, unique, and random passwords based on security requirements for every website you frequent.\\n\\nBitwarden Send quickly transmits encrypted information --- files and plaintext -- directly to anyone.\\n\\nBitwarden offers Teams and Enterprise plans for companies so you can securely share passwords with colleagues.\\n\\nWhy Choose Bitwarden:\\n\\nWorld-Class Encryption\\nPasswords are protected with advanced end-to-end encryption (AES-256 bit, salted hashing, and PBKDF2 SHA-256) so your data stays secure and private.\\n\\nBuilt-in Password Generator\\nGenerate strong, unique, and random passwords based on security requirements for every website you frequent.\\n\\nGlobal Translations\\nBitwarden translations exist in 40 languages and are growing, thanks to our global community.\\n\\nCross-Platform Applications\\nSecure and share sensitive data within your Bitwarden Vault from any browser, mobile device, or desktop OS, and more.\\n","installed-size":28114944,"install-date":"2024-04-12T22:32:02.614258854+00:00","name":"bw","publisher":{"id":"SflUpHyJuL9BkjUnFAgINhCW9QjI5tow","username":"bitwarden","display-name":"8bit Solutions LLC","validation":"verified"},"developer":"bitwarden","status":"active","type":"app","base":"core22","version":"2024.3.1","channel":"","ignore-validation":false,"revision":"60","confinement":"strict","private":false,"devmode":false,"jailmode":false,"apps":[{"snap":"bw","name":"bw"}],"mounted-from":"/var/lib/snapd/snaps/bw_60.snap","links":null,"contact":""},{"id":"TKv5Fm000l4XiUYJW9pjWHLkCPlDbIg1","title":"GNOME 3.28 runtime","summary":"Shared GNOME 3.28 runtime for Ubuntu 18.04","description":"This snap includes a GNOME 3.28 stack (the base libraries and desktop \\nintegration components) and shares it through the content interface.","icon":"/v2/icons/gnome-3-28-1804/icon","installed-size":172830720,"install-date":"2024-04-11T01:51:22.822580656+00:00","name":"gnome-3-28-1804","publisher":{"id":"canonical","username":"canonical","display-name":"Canonical","validation":"verified"},"developer":"canonical","status":"active","type":"app","base":"core18","version":"3.28.0-19-g98f9e67.98f9e67","channel":"stable","tracking-channel":"latest/stable","ignore-validation":false,"revision":"198","confinement":"strict","private":false,"devmode":false,"jailmode":false,"mounted-from":"/var/lib/snapd/snaps/gnome-3-28-1804_198.snap","links":{"contact":["https://gitlab.gnome.org/Community/Ubuntu/gnome-3-28-1804/issues"]},"contact":"https://gitlab.gnome.org/Community/Ubuntu/gnome-3-28-1804/issues","media":[{"type":"icon","url":"https://dashboard.snapcraft.io/site_media/appmedia/2018/04/icon_ysMJicB.png","width":256,"height":256}]},{"id":"amcUKQILKXHHTlmSa7NMdnXSx02dNeeT","title":"core22","summary":"Runtime environment based on Ubuntu 22.04","description":"The base snap based on the Ubuntu 22.04 release.","installed-size":77819904,"install-date":"2024-04-12T22:32:01.926250097+02:00","name":"core22","publisher":{"id":"canonical","username":"canonical","display-name":"Canonical","validation":"verified"},"developer":"canonical","status":"active","type":"base","version":"20240111","channel":"stable","tracking-channel":"latest/stable","ignore-validation":false,"revision":"1122","confinement":"strict","private":false,"devmode":false,"jailmode":false,"mounted-from":"/var/lib/snapd/snaps/core22_1122.snap","links":{"contact":["https://github.com/snapcore/core-base/issues"]},"contact":"https://github.com/snapcore/core-base/issues"},{"id":"Nvk8FZTYrAYFKXN74w5LtOrnOhE38fU8","title":"Bitwarden","summary":"Bitwarden","description":"A secure and free password manager for all of your devices.\\n\\n**Installation**\\n\\nBitwarden requires access to the `password-manager-service` for secure storage. Please enable it through permissions or by running `sudo snap connect bitwarden:password-manager-service`.","icon":"/v2/icons/bitwarden/icon","installed-size":97787904,"install-date":"2024-04-15T18:51:18.534146927+02:00","name":"bitwarden","publisher":{"id":"SflUpHyJuL9BkjUnFAgINhCW9QjI5tow","username":"bitwarden","display-name":"8bit Solutions LLC","validation":"verified"},"developer":"bitwarden","status":"active","type":"app","base":"core22","version":"2024.4.0","channel":"stable","tracking-channel":"latest/stable","ignore-validation":false,"revision":"108","confinement":"strict","private":false,"devmode":false,"jailmode":false,"apps":[{"snap":"bitwarden","name":"bitwarden","desktop-file":"/var/lib/snapd/desktop/applications/bitwarden_bitwarden.desktop"}],"mounted-from":"/var/lib/snapd/snaps/bitwarden_108.snap","links":{"contact":["https://bitwarden.com"]},"contact":"https://bitwarden.com","media":[{"type":"icon","url":"https://dashboard.snapcraft.io/site_media/appmedia/2020/07/512x512_XF6VNFl.png","width":512,"height":512},{"type":"screenshot","url":"https://dashboard.snapcraft.io/site_media/appmedia/2018/04/bitwarden_ubuntu.PNG"}]},{"id":"TIM9dBBJEceEjMpwaB3fiuZ3AdSykgDO","title":"gnome-3-34-1804","summary":"Shared GNOME 3.34 Ubuntu stack","description":"This snap includes a GNOME 3.34 stack (the base libraries and desktop \\nintegration components) and shares it through the content interface.","icon":"/v2/icons/gnome-3-34-1804/icon","installed-size":228999168,"install-date":"2024-04-12T17:54:04.335584052+02:00","name":"gnome-3-34-1804","publisher":{"id":"canonical","username":"canonical","display-name":"Canonical","validation":"verified"},"developer":"canonical","status":"active","type":"app","base":"core18","version":"0+git.3556cb3","channel":"stable","tracking-channel":"latest/stable","ignore-validation":false,"revision":"93","confinement":"strict","private":false,"devmode":false,"jailmode":false,"mounted-from":"/var/lib/snapd/snaps/gnome-3-34-1804_93.snap","links":null,"contact":"","media":[{"type":"icon","url":"https://dashboard.snapcraft.io/site_media/appmedia/2019/10/icon_l1zqb5t.png","width":256,"height":256}]}],"sources":["local"]}'


@pytest.fixture
def snap_list_api_revisions_out():
    return '{"type":"sync","status-code":200,"status":"OK","result":[{"id":"jZLfBRzf1cYlYysIjD2bwSzNtngY0qit","title":"GTK Common Themes","summary":"All the (common) themes","description":"A snap that exports the GTK and icon themes used on various Linux distros.","installed-size":96141312,"name":"gtk-common-themes","publisher":{"id":"canonical","username":"canonical","display-name":"Canonical","validation":"verified"},"developer":"canonical","status":"installed","type":"app","base":"bare","version":"0.1-81-g442e511","channel":"stable","tracking-channel":"latest/stable","ignore-validation":false,"revision":"1535","confinement":"strict","private":false,"devmode":false,"jailmode":false,"mounted-from":"/var/lib/snapd/snaps/gtk-common-themes_1535.snap","links":{"contact":["https://gitlab.gnome.org/Community/Ubuntu/gtk-common-themes/issues"]},"contact":"https://gitlab.gnome.org/Community/Ubuntu/gtk-common-themes/issues"},{"id":"buPKUD3TKqCOgLEjjHx5kSiCpIs5cMuQ","title":"Hello World","summary":"The \'hello-world\' of snaps","description":"This is a simple hello world example.","icon":"/v2/icons/hello-world/icon","installed-size":20480,"install-date":"2024-04-11T12:15:56.850202878+00:00","name":"hello-world","publisher":{"id":"canonical","username":"canonical","display-name":"Canonical","validation":"verified"},"developer":"canonical","status":"active","type":"app","version":"6.3","channel":"","tracking-channel":"latest/stable","ignore-validation":false,"revision":"28","confinement":"strict","private":false,"devmode":false,"jailmode":false,"apps":[{"snap":"hello-world","name":"env"},{"snap":"hello-world","name":"evil"},{"snap":"hello-world","name":"hello-world"},{"snap":"hello-world","name":"sh"}],"mounted-from":"/var/lib/snapd/snaps/hello-world_28.snap","links":{"contact":["mailto:snaps@canonical.com"]},"contact":"mailto:snaps@canonical.com","media":[{"type":"icon","url":"https://dashboard.snapcraft.io/site_media/appmedia/2015/03/hello.svg_NZLfWbh.png","width":256,"height":256},{"type":"screenshot","url":"https://dashboard.snapcraft.io/site_media/appmedia/2018/06/Screenshot_from_2018-06-14_09-33-31.png","width":199,"height":118},{"type":"video","url":"https://vimeo.com/194577403"}],"hold":"2316-07-22T12:19:33.173911003+00:00"},{"id":"osRLU2WSwcWCNSMFOgqpQoE6NPnD7r31","title":"Yubico Authenticator","summary":"2FA with YubiKey","description":"description_too_long \\n hi there","icon":"/v2/icons/yubioath-desktop/icon","installed-size":227135488,"install-date":"2024-04-11T12:15:23.66083664+00:00","name":"yubioath-desktop","publisher":{"id":"o2S2GYSCBxilwi1OFNftYfLhm2l3aEzI","username":"yubico-snap-store","display-name":"Yubico","validation":"unproven"},"developer":"yubico-snap-store","status":"active","type":"app","base":"core18","version":"5.0.5","channel":"","tracking-channel":"latest/stable","ignore-validation":false,"revision":"12","confinement":"strict","private":false,"devmode":false,"jailmode":false,"apps":[{"snap":"yubioath-desktop","name":"pcscd","daemon":"simple","daemon-scope":"system","enabled":true,"active":true,"common-id":"com.yubico.pcscd"},{"snap":"yubioath-desktop","name":"yubioath-desktop","desktop-file":"/var/lib/snapd/desktop/applications/yubioath-desktop_yubioath-desktop.desktop","common-id":"com.yubico.yubioath"}],"common-ids":["com.yubico.pcscd","com.yubico.yubioath"],"mounted-from":"/var/lib/snapd/snaps/yubioath-desktop_12.snap","links":{"contact":["https://support.yubico.com/support/tickets/new"],"website":["https://developers.yubico.com/yubioath-desktop"]},"contact":"https://support.yubico.com/support/tickets/new","website":"https://developers.yubico.com/yubioath-desktop","media":[{"type":"icon","url":"https://dashboard.snapcraft.io/site_media/appmedia/2020/05/com.yubico.yubioath.svg.png","width":512,"height":512},{"type":"screenshot","url":"https://dashboard.snapcraft.io/site_media/appmedia/2021/10/Linux-12x-100.jpg","width":2881,"height":1801},{"type":"screenshot","url":"https://dashboard.snapcraft.io/site_media/appmedia/2021/10/Linux-22x-100.jpg","width":2881,"height":1801},{"type":"screenshot","url":"https://dashboard.snapcraft.io/site_media/appmedia/2021/10/Linux-32x-100_1.jpg","width":2881,"height":1801},{"type":"screenshot","url":"https://dashboard.snapcraft.io/site_media/appmedia/2021/10/Linux-42x-100.jpg","width":2881,"height":1801}],"hold":"2024-04-11T12:43:59.00001288+00:00"},{"id":"osRLU2WSwcWCNSMFOgqpQoE6NPnD7r31","title":"Yubico Authenticator","summary":"2FA with YubiKey","description":"description_too_long \\n hi there","icon":"/v2/icons/yubioath-desktop/icon","installed-size":225135488,"install-date":"2024-03-11T12:15:23.66083664+00:00","name":"yubioath-desktop","publisher":{"id":"o2S2GYSCBxilwi1OFNftYfLhm2l3aEzI","username":"yubico-snap-store","display-name":"Yubico","validation":"unproven"},"developer":"yubico-snap-store","status":"active","type":"app","base":"core18","version":"5.0.4","channel":"","tracking-channel":"latest/stable","ignore-validation":false,"revision":"11","confinement":"strict","private":false,"devmode":false,"jailmode":false,"apps":[{"snap":"yubioath-desktop","name":"pcscd","daemon":"simple","daemon-scope":"system","enabled":true,"active":true,"common-id":"com.yubico.pcscd"},{"snap":"yubioath-desktop","name":"yubioath-desktop","desktop-file":"/var/lib/snapd/desktop/applications/yubioath-desktop_yubioath-desktop.desktop","common-id":"com.yubico.yubioath"}],"common-ids":["com.yubico.pcscd","com.yubico.yubioath"],"mounted-from":"/var/lib/snapd/snaps/yubioath-desktop_12.snap","links":{"contact":["https://support.yubico.com/support/tickets/new"],"website":["https://developers.yubico.com/yubioath-desktop"]},"contact":"https://support.yubico.com/support/tickets/new","website":"https://developers.yubico.com/yubioath-desktop","media":[{"type":"icon","url":"https://dashboard.snapcraft.io/site_media/appmedia/2020/05/com.yubico.yubioath.svg.png","width":512,"height":512},{"type":"screenshot","url":"https://dashboard.snapcraft.io/site_media/appmedia/2021/10/Linux-12x-100.jpg","width":2881,"height":1801},{"type":"screenshot","url":"https://dashboard.snapcraft.io/site_media/appmedia/2021/10/Linux-22x-100.jpg","width":2881,"height":1801},{"type":"screenshot","url":"https://dashboard.snapcraft.io/site_media/appmedia/2021/10/Linux-32x-100_1.jpg","width":2881,"height":1801},{"type":"screenshot","url":"https://dashboard.snapcraft.io/site_media/appmedia/2021/10/Linux-42x-100.jpg","width":2881,"height":1801}]},{"id":"osRLU2WSwcWCNSMFOgqpQoE6NPnD7r31","title":"Yubico Authenticator","summary":"2FA with YubiKey","description":"description_too_long \\n hi there","icon":"/v2/icons/yubioath-desktop/icon","installed-size":223135488,"install-date":"2024-02-11T12:15:23.66083664+00:00","name":"yubioath-desktop","publisher":{"id":"o2S2GYSCBxilwi1OFNftYfLhm2l3aEzI","username":"yubico-snap-store","display-name":"Yubico","validation":"unproven"},"developer":"yubico-snap-store","status":"active","type":"app","base":"core18","version":"5.0.3","channel":"","tracking-channel":"latest/stable","ignore-validation":false,"revision":"10","confinement":"strict","private":false,"devmode":false,"jailmode":false,"apps":[{"snap":"yubioath-desktop","name":"pcscd","daemon":"simple","daemon-scope":"system","enabled":true,"active":true,"common-id":"com.yubico.pcscd"},{"snap":"yubioath-desktop","name":"yubioath-desktop","desktop-file":"/var/lib/snapd/desktop/applications/yubioath-desktop_yubioath-desktop.desktop","common-id":"com.yubico.yubioath"}],"common-ids":["com.yubico.pcscd","com.yubico.yubioath"],"mounted-from":"/var/lib/snapd/snaps/yubioath-desktop_12.snap","links":{"contact":["https://support.yubico.com/support/tickets/new"],"website":["https://developers.yubico.com/yubioath-desktop"]},"contact":"https://support.yubico.com/support/tickets/new","website":"https://developers.yubico.com/yubioath-desktop","media":[{"type":"icon","url":"https://dashboard.snapcraft.io/site_media/appmedia/2020/05/com.yubico.yubioath.svg.png","width":512,"height":512},{"type":"screenshot","url":"https://dashboard.snapcraft.io/site_media/appmedia/2021/10/Linux-12x-100.jpg","width":2881,"height":1801},{"type":"screenshot","url":"https://dashboard.snapcraft.io/site_media/appmedia/2021/10/Linux-22x-100.jpg","width":2881,"height":1801},{"type":"screenshot","url":"https://dashboard.snapcraft.io/site_media/appmedia/2021/10/Linux-32x-100_1.jpg","width":2881,"height":1801},{"type":"screenshot","url":"https://dashboard.snapcraft.io/site_media/appmedia/2021/10/Linux-42x-100.jpg","width":2881,"height":1801}]},{"id":"EISPgh06mRh1vordZY9OZ34QHdd7OrdR","title":"bare","summary":"Empty base snap, useful for testing and fully statically linked snaps","description":"","installed-size":4096,"install-date":"2024-04-11T01:50:47.869171361+00:00","name":"bare","publisher":{"id":"canonical","username":"canonical","display-name":"Canonical","validation":"verified"},"developer":"canonical","status":"active","type":"base","version":"1.0","channel":"stable","tracking-channel":"latest/stable","ignore-validation":false,"revision":"5","confinement":"strict","private":false,"devmode":false,"jailmode":false,"mounted-from":"/var/lib/snapd/snaps/bare_5.snap","links":{"contact":["mailto:snaps@canonical.com"]},"contact":"mailto:snaps@canonical.com"},{"id":"99T7MUlRhtI3U0QFgl5mXXESAiSwt776","title":"core","summary":"snapd runtime environment","description":"The core runtime environment for snapd","installed-size":109043712,"install-date":"2024-04-11T01:42:05.749062355+00:00","name":"core","publisher":{"id":"canonical","username":"canonical","display-name":"Canonical","validation":"verified"},"developer":"canonical","status":"active","type":"os","version":"16-2.61.2","channel":"stable","tracking-channel":"latest/stable","ignore-validation":false,"revision":"16928","confinement":"strict","private":false,"devmode":false,"jailmode":false,"mounted-from":"/var/lib/snapd/snaps/core_16928.snap","links":{"contact":["mailto:snaps@canonical.com"],"website":["https://snapcraft.io"]},"contact":"mailto:snaps@canonical.com","website":"https://snapcraft.io"},{"id":"CSO04Jhav2yK0uz97cr0ipQRyqg0qQL6","title":"Core 18","summary":"Runtime environment based on Ubuntu 18.04","description":"The base snap based on the Ubuntu 18.04 release.","installed-size":58363904,"name":"core18","publisher":{"id":"canonical","username":"canonical","display-name":"Canonical","validation":"verified"},"developer":"canonical","status":"installed","type":"base","version":"20231027","channel":"stable","tracking-channel":"latest/stable","ignore-validation":false,"revision":"2812","confinement":"strict","private":false,"devmode":false,"jailmode":false,"mounted-from":"/var/lib/snapd/snaps/core18_2812.snap","links":{"contact":["https://github.com/snapcore/core18/issues"],"website":["https://snapcraft.io"]},"contact":"https://github.com/snapcore/core18/issues","website":"https://snapcraft.io"},{"id":"n0XNnJXxSdYYHRYwtfYV2mBSkzH1Fbkn","summary":"Bitwarden CLI - A secure and free password manager for all of your devices.","description":"Bitwarden, Inc. is the parent company of 8bit Solutions LLC.\\n\\nNAMED BEST PASSWORD MANAGER BY THE VERGE, U.S. NEWS &amp; WORLD REPORT, CNET, AND MORE.\\n\\nManage, store, secure, and share unlimited passwords across unlimited devices from anywhere. Bitwarden delivers open source password management solutions to everyone, whether at  home, at work, or on the go.\\n\\nGenerate strong, unique, and random passwords based on security requirements for every website you frequent.\\n\\nBitwarden Send quickly transmits encrypted information --- files and plaintext -- directly to anyone.\\n\\nBitwarden offers Teams and Enterprise plans for companies so you can securely share passwords with colleagues.\\n\\nWhy Choose Bitwarden:\\n\\nWorld-Class Encryption\\nPasswords are protected with advanced end-to-end encryption (AES-256 bit, salted hashing, and PBKDF2 SHA-256) so your data stays secure and private.\\n\\nBuilt-in Password Generator\\nGenerate strong, unique, and random passwords based on security requirements for every website you frequent.\\n\\nGlobal Translations\\nBitwarden translations exist in 40 languages and are growing, thanks to our global community.\\n\\nCross-Platform Applications\\nSecure and share sensitive data within your Bitwarden Vault from any browser, mobile device, or desktop OS, and more.\\n","installed-size":28114944,"install-date":"2024-04-12T22:32:02.614258854+00:00","name":"bw","publisher":{"id":"SflUpHyJuL9BkjUnFAgINhCW9QjI5tow","username":"bitwarden","display-name":"8bit Solutions LLC","validation":"verified"},"developer":"bitwarden","status":"active","type":"app","base":"core22","version":"2024.3.1","channel":"","ignore-validation":false,"revision":"60","confinement":"strict","private":false,"devmode":false,"jailmode":false,"apps":[{"snap":"bw","name":"bw"}],"mounted-from":"/var/lib/snapd/snaps/bw_60.snap","links":null,"contact":""},{"id":"TKv5Fm000l4XiUYJW9pjWHLkCPlDbIg1","title":"GNOME 3.28 runtime","summary":"Shared GNOME 3.28 runtime for Ubuntu 18.04","description":"This snap includes a GNOME 3.28 stack (the base libraries and desktop \\nintegration components) and shares it through the content interface.","icon":"/v2/icons/gnome-3-28-1804/icon","installed-size":172830720,"install-date":"2024-04-11T01:51:22.822580656+00:00","name":"gnome-3-28-1804","publisher":{"id":"canonical","username":"canonical","display-name":"Canonical","validation":"verified"},"developer":"canonical","status":"active","type":"app","base":"core18","version":"3.28.0-19-g98f9e67.98f9e67","channel":"stable","tracking-channel":"latest/stable","ignore-validation":false,"revision":"198","confinement":"strict","private":false,"devmode":false,"jailmode":false,"mounted-from":"/var/lib/snapd/snaps/gnome-3-28-1804_198.snap","links":{"contact":["https://gitlab.gnome.org/Community/Ubuntu/gnome-3-28-1804/issues"]},"contact":"https://gitlab.gnome.org/Community/Ubuntu/gnome-3-28-1804/issues","media":[{"type":"icon","url":"https://dashboard.snapcraft.io/site_media/appmedia/2018/04/icon_ysMJicB.png","width":256,"height":256}]},{"id":"amcUKQILKXHHTlmSa7NMdnXSx02dNeeT","title":"core22","summary":"Runtime environment based on Ubuntu 22.04","description":"The base snap based on the Ubuntu 22.04 release.","installed-size":77819904,"install-date":"2024-04-12T22:32:01.926250097+02:00","name":"core22","publisher":{"id":"canonical","username":"canonical","display-name":"Canonical","validation":"verified"},"developer":"canonical","status":"active","type":"base","version":"20240111","channel":"stable","tracking-channel":"latest/stable","ignore-validation":false,"revision":"1122","confinement":"strict","private":false,"devmode":false,"jailmode":false,"mounted-from":"/var/lib/snapd/snaps/core22_1122.snap","links":{"contact":["https://github.com/snapcore/core-base/issues"]},"contact":"https://github.com/snapcore/core-base/issues"},{"id":"Nvk8FZTYrAYFKXN74w5LtOrnOhE38fU8","title":"Bitwarden","summary":"Bitwarden","description":"A secure and free password manager for all of your devices.\\n\\n**Installation**\\n\\nBitwarden requires access to the `password-manager-service` for secure storage. Please enable it through permissions or by running `sudo snap connect bitwarden:password-manager-service`.","icon":"/v2/icons/bitwarden/icon","installed-size":97787904,"install-date":"2024-04-15T18:51:18.534146927+02:00","name":"bitwarden","publisher":{"id":"SflUpHyJuL9BkjUnFAgINhCW9QjI5tow","username":"bitwarden","display-name":"8bit Solutions LLC","validation":"verified"},"developer":"bitwarden","status":"active","type":"app","base":"core22","version":"2024.4.0","channel":"stable","tracking-channel":"latest/stable","ignore-validation":false,"revision":"108","confinement":"strict","private":false,"devmode":false,"jailmode":false,"apps":[{"snap":"bitwarden","name":"bitwarden","desktop-file":"/var/lib/snapd/desktop/applications/bitwarden_bitwarden.desktop"}],"mounted-from":"/var/lib/snapd/snaps/bitwarden_108.snap","links":{"contact":["https://bitwarden.com"]},"contact":"https://bitwarden.com","media":[{"type":"icon","url":"https://dashboard.snapcraft.io/site_media/appmedia/2020/07/512x512_XF6VNFl.png","width":512,"height":512},{"type":"screenshot","url":"https://dashboard.snapcraft.io/site_media/appmedia/2018/04/bitwarden_ubuntu.PNG"}]},{"id":"TIM9dBBJEceEjMpwaB3fiuZ3AdSykgDO","title":"gnome-3-34-1804","summary":"Shared GNOME 3.34 Ubuntu stack","description":"This snap includes a GNOME 3.34 stack (the base libraries and desktop \\nintegration components) and shares it through the content interface.","icon":"/v2/icons/gnome-3-34-1804/icon","installed-size":228999168,"install-date":"2024-04-12T17:54:04.335584052+02:00","name":"gnome-3-34-1804","publisher":{"id":"canonical","username":"canonical","display-name":"Canonical","validation":"verified"},"developer":"canonical","status":"active","type":"app","base":"core18","version":"0+git.3556cb3","channel":"stable","tracking-channel":"latest/stable","ignore-validation":false,"revision":"93","confinement":"strict","private":false,"devmode":false,"jailmode":false,"mounted-from":"/var/lib/snapd/snaps/gnome-3-34-1804_93.snap","links":null,"contact":"","media":[{"type":"icon","url":"https://dashboard.snapcraft.io/site_media/appmedia/2019/10/icon_l1zqb5t.png","width":256,"height":256}]}],"sources":["local"]}'


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
            refresh-date: today at 12:15 UTC
            channels:
              latest/stable:    6.4 2024-02-27 (29) 20kB -
              latest/candidate: 6.4 2024-02-27 (29) 20kB -
              latest/beta:      6.4 2024-02-27 (29) 20kB -
              latest/edge:      6.4 2024-02-27 (29) 20kB -
            installed:          6.3            (28) 20kB -
        """
    ).strip()


@pytest.fixture
def snap_info_multi_out():
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
            refresh-date: today at 12:15 UTC
            channels:
              latest/stable:    6.4 2024-02-27 (29) 20kB -
              latest/candidate: 6.4 2024-02-27 (29) 20kB -
              latest/beta:      6.4 2024-02-27 (29) 20kB -
              latest/edge:      6.4 2024-02-27 (29) 20kB -
            installed:          6.3            (28) 20kB -
            ---
            name:      core
            summary:   snapd runtime environment
            publisher: Canonical**
            store-url: https://snapcraft.io/core
            contact:   snaps@canonical.com
            license:   unset
            description: |
              The core runtime environment for snapd
            type:         core
            snap-id:      99T7MUlRhtI3U0QFgl5mXXESAiSwt776
            tracking:     latest/stable
            refresh-date: today at 01:42 UTC
            channels:
              latest/stable:    16-2.61.2                   2024-03-14 (16928) 109MB -
              latest/candidate: 16-2.61.2                   2024-03-05 (16928) 109MB -
              latest/beta:      16-2.61.2                   2024-02-19 (16928) 109MB -
              latest/edge:      16-2.61.2+git5069.72e4b6d66 2024-03-04 (16969) 109MB -
            installed:          16-2.61.2                              (16928) 109MB core
            ---
            warning: no snap found for "foobar"
        """
    ).strip()


@pytest.fixture
def snap_info_verbose_out():
    return dedent(
        """
            name:    hello-world
            summary: The 'hello-world' of snaps
            health:
              status:  unknown
              message: health has not been set
            publisher: Canonical**
            store-url: https://snapcraft.io/hello-world
            contact:   snaps@canonical.com
            links:
              contact:
                - mailto:snaps@canonical.com
            license: unset
            description: |
              This is a simple hello world example.
            commands:
              - hello-world.env
              - hello-world.evil
              - hello-world
              - hello-world.sh
            notes:
              private:           false
              confinement:       strict
              devmode:           false
              jailmode:          false
              trymode:           false
              enabled:           true
              broken:            false
              ignore-validation: false
            snap-id:      buPKUD3TKqCOgLEjjHx5kSiCpIs5cMuQ
            tracking:     latest/stable
            refresh-date: today at 12:15 UTC
            channels:
              latest/stable:    6.4 2024-02-27 (29) 20kB -
              latest/candidate: 6.4 2024-02-27 (29) 20kB -
              latest/beta:      6.4 2024-02-27 (29) 20kB -
              latest/edge:      6.4 2024-02-27 (29) 20kB -
            installed:          6.3            (28) 20kB -
        """
    ).strip()


@pytest.fixture
def snap_known_out():
    return dedent(
        """
            type: snap-revision
            authority-id: canonical
            snap-sha3-384: AH7zvZLOXzHcp3gxaWTmGUOrmsXYJmACXFiCBoydL-H1PlC9G43rGAJs3WiyzOb_
            developer-id: GKq9csPRQp1E5kUglZG9QTqDEBLrcszO
            provenance: global-upload
            snap-id: JUJH91Ved74jd4ZgJCpzMBtYbPOzTlsD
            snap-revision: 142
            snap-size: 123101184
            timestamp: 2024-04-03T17:49:48.613165Z
            sign-key-sha3-384: BWDEoaqyr25nF5SNCvEv2v7QnM9QsfCc0PBMYD_i2NGSQ32EF2d4D0hqUel3m8ul

            AcLBUgQAAQoABgUCZg2WvAAAQwMQAGUaERlgIpDMfBDlpzTnh7kvaTmCKaMikqPmtNpzINcPgkJ7
            F2ph+gsdSBMjgvOHe8mErmhQI2ggjZTPi2HQAVieJXfM127iry3BEcu/47EmVp4bU5BhmDtmkk9Q
            x2Kz+nJf9Tyvdh4YeMJ2xr2zubAPVbHFW1K0WLw6SWVqzhZHBKNmxUVehJi5gObH9QeLMieha5BW
            BcRaxhhozewBT2ZW3l8rtw9iTyoSneWoc27OeXjCKAfnvZAOiM8LN1oZ+x6ZpkBBygNbtdiayXU1
            bXguCxQfBIQYWf8PHap0TOxkS4+k2CZqnruCaw+OVjS2YiWLsjXcjTOEMXFVejx+Arhe0jPzh2ld
            uTnMu5jyJgCWv2j9qCN4LRLkwqb+eiEaMT1ZtFWhIyYgoTRwjDz5UpKVdkRYdcvuApBY0+Z0kNcW
            Nyja6T/BPeHhmkph5LD7rc7VBYiIr4yg04Fr1U4GWt6tduPPY4Sstg18ctHN0TNAJpffBg9/TRmA
            cjK96zqyNcp6KSJxDEd0szefiWJpyuqFuH0H56ABwOyzvBBP+HxtP9I7UvHp8QM7lDcir8uZu2Ny
            7HzVnpDizvyHARB6VEsakX4G/1HQrDXTSpNJVMGL/CzMLcGaXRZCAIjreGHx2H/QNxNCkxOTNRXw
            uz/npCnBX+6iSFGGxFS6+qZdv2T4

            type: snap-revision
            authority-id: canonical
            snap-sha3-384: tZ4sZcgQR8QSIdneZKmUj44OXwnVm_64iWwPmwh_3Jfi5eGCRyDYEnfrAcIsX2D_
            developer-id: canonical
            provenance: global-upload
            snap-id: TIM9dBBJEceEjMpwaB3fiuZ3AdSykgDO
            snap-revision: 93
            snap-size: 228999168
            timestamp: 2023-04-24T16:34:37.479211Z
            sign-key-sha3-384: BWDEoaqyr25nF5SNCvEv2v7QnM9QsfCc0PBMYD_i2NGSQ32EF2d4D0hqUel3m8ul

            AcLBUgQAAQoABgUCZEavnQAAtcUQAM4w7OG6xvJn5gLaANx1f+t7rYy/bF+Hu14ubkznUnHabICI
            hcJ9vbKug1/fl6aA7NCYDOvIza9XoYZvQ78qK+K1qxf9yy8rzYySBcIrjNq05lFpt41Sor8nUcik
            UOyHlObfRztAWHMqzCOUZqURd49jf9wOOVasssBLCio3S7L4zkMOFnw84TTvAzfijK2nqefc7FQl
            7BEHFudnv3Oxm9dYxZwoWYKrw+5hxVls6RUFZo5gWmeo+k6sgLTEegWLSRrFOquaj1YBOxKoK5TM
            ShXHWLYURkpcElAf4hyeutmdLph81jL4GdH/NZ6OP4DnFDU8SA+F2lmflZuw62FqOZ0uVrOTZcGS
            eIgEUxfAiH8fYsqgTI9UBfIuOdfAS4ide4dngyD+3rs+RBu4oDyk2nF+kB9v4yqknP4SqX3snVRz
            w/+pUki5I7Tz3OjzqRWL2CcNpVAHrXCBPhGsekU+Y+udDnifClD+fxNvD83NbnAgo5YH1h1jo+Wr
            RxbLk/8pUwm5/r9lwNGMgbZyErSEhp8UU7QYeL9ESfwfhXPN9P1cWlqG7++Y/ZMzp6Uy0bQNSWYe
            A5C3It4dLeTYzoLOy1BzxGvUnuVO71xU6MMrLHlD3yh9oQX2UOaiXJAEfLSJqZ05hqiZKeZnEZgX
            gxbmtLtZmYSEG09GbQUZMIZSdwO7

            type: snap-revision
            authority-id: canonical
            snap-sha3-384: rCj3QCM0PMpsn4FiyOqBpUBtjbU_PLGrTOcr96Q9jTKjV96NSRDpW9lZIpmrsSJU
            developer-id: SflUpHyJuL9BkjUnFAgINhCW9QjI5tow
            provenance: global-upload
            snap-id: n0XNnJXxSdYYHRYwtfYV2mBSkzH1Fbkn
            snap-revision: 60
            snap-size: 28114944
            timestamp: 2024-04-08T12:46:12.441719Z
            sign-key-sha3-384: BWDEoaqyr25nF5SNCvEv2v7QnM9QsfCc0PBMYD_i2NGSQ32EF2d4D0hqUel3m8ul

            AcLBUgQAAQoABgUCZhPnFAAA5oAQAFP/x06Ywt87L8k/2SmHcW7WTjD1QmdMPgKfORm/VqVLhnrE
            Gr8nRl/30cNTpmcwA9VtkQXk+swnocctbam/uyFyaGjQqLbeNfy57hvCdPw4+bRg6YXh8KvdS+fR
            /gbGdCUFDO2z8yxeLctgmGDmPo6wpacNzwjGGshqcNhLkoNyWdq20Jk/a0WLgYk7qFIcNDr8chw0
            EMb1FjsFPaki6A//kIB4VC9oQVz/EYX0kUhqAV5ww/GdMpQHbv1YStqLHsv+iLSmAtcBxsmRt9NT
            gaVCjfzomaic05lYHCE5B6Vh/yjcimsfnfzVgp4tcHMv+QOc1CqBRh3EbdLSP4evvB9VHPgHwBgS
            Lym7loToxuv1N7wUX1V9UHib0ITymjVc9KjcnBga4XueceVNeMnh1e6MdpPpzFVJiavHXz9yMXir
            3yafQVlqdtULjqjKAm+uoh1vs6bJk0FMb3uWeXVGPO9AvpbXH6kH0bKt/3+zeCDh823Ssy9Jo0Zo
            JpKjiXFTXIFvwO/cnD21OBqVHbApmVofhXCNu6z1OotwPmmNkBHgBFPy1H82kZI11dERooWN9OyF
            P7t755KpF+ET1U9N7ErJcks9uMdzyJ3Vg9zN78PnlyfTtfTaOQBUk4zrCX+80ZXbVEzfX3yVuLuE
            M4NtDfCg5eaYf+TRtlSJz9MBqYNy

            type: snap-revision
            authority-id: canonical
            snap-sha3-384: 7uNHCak9aSwcICRfP1YmJNGrRqROw45Ihj1aFx7S74MUfXYedKyZQzbjkJC2CCYd
            developer-id: canonical
            provenance: global-upload
            snap-id: amcUKQILKXHHTlmSa7NMdnXSx02dNeeT
            snap-revision: 1122
            snap-size: 77819904
            timestamp: 2024-01-11T16:31:37.728357Z
            sign-key-sha3-384: BWDEoaqyr25nF5SNCvEv2v7QnM9QsfCc0PBMYD_i2NGSQ32EF2d4D0hqUel3m8ul

            AcLBUgQAAQoABgUCZaAX6QAAXBwQACkwxo0cONmFB70cfHFZ7U6G2MyAYKK9kHd2NRAqFhH4eD+j
            xAukCT8QksQYrY0C0pO0vocY5yPUBDIsg5p64PXSd0vSBjPL8hHEe6qce00sYGPyPCQM3BqqAM/f
            bs5lAL/h9+WyQrGNZBz8hBB5e++o+bKtGWqMeG2CsEsJvR/hpwdmyQ0NxOS7CpecKnDbhh3dYDm1
            GDrO1htJ2MkBVUdLlF4LczSnsZDO1j65CStyOgebQ/bttNM5HgGQqo2w4rIJw6Ms9LqB7hJqacbb
            ZW3P6oEQhi/T6Q5YqffxPHV5Ry0iRIR2c64gZVywrUjg8x48oDtwx5y55iJ2q5OjYQWXSpJx1fxD
            u7mAbz1W0/0/VSOmqiW0mjuM6DgWrg3x2Vxc86P2N+YrqLLXwwf+vFD26UMCtSes/kn9hJnrQosC
            UAtRIY06KRA6dDfSIHoYr+KD/VvbUOKxNRBgbS3uR4m6NvIgtTMZsR6ntIcIKeo7LdLfbnQ7XnlO
            KcFL/PoJrr3QuAkbMXhhRSbq0PvoC1Z8BbGg9kp/LF6R7oG49U/+MEQBoc5Tb3NQWZBO7ya9Wr9u
            wgEIEiuZMwzMtvY7RrkO1UpncUEcZcwDOUF+d0+BvYVrIYup66yK3Shd6DXOK3DMq8LVLupj10Il
            mD9rT/NIvhoPJgX2UIrZwrXBBpkY
        """
    ).strip()


@pytest.fixture
def snap_connections_out():
    return '{"type":"sync","status-code":200,"status":"OK","result":{"established":[{"slot":{"snap":"core","slot":"audio-playback"},"plug":{"snap":"bitwarden","plug":"audio-playback"},"interface":"audio-playback"},{"slot":{"snap":"core","slot":"browser-support"},"plug":{"snap":"bitwarden","plug":"browser-support"},"interface":"browser-support"},{"slot":{"snap":"core","slot":"desktop"},"plug":{"snap":"bitwarden","plug":"desktop"},"interface":"desktop"},{"slot":{"snap":"core","slot":"desktop-legacy"},"plug":{"snap":"bitwarden","plug":"desktop-legacy"},"interface":"desktop-legacy"},{"slot":{"snap":"gnome-3-28-1804","slot":"gnome-3-28-1804"},"plug":{"snap":"bitwarden","plug":"gnome-3-28-1804"},"interface":"content","slot-attrs":{"content":"gnome-3-28-1804","read":["/"]},"plug-attrs":{"content":"gnome-3-28-1804","default-provider":"gnome-3-28-1804","target":"$SNAP/gnome-platform"}},{"slot":{"snap":"core","slot":"gsettings"},"plug":{"snap":"bitwarden","plug":"gsettings"},"interface":"gsettings"},{"slot":{"snap":"core","slot":"home"},"plug":{"snap":"bitwarden","plug":"home"},"interface":"home"},{"slot":{"snap":"core","slot":"network"},"plug":{"snap":"bitwarden","plug":"network"},"interface":"network"},{"slot":{"snap":"core","slot":"opengl"},"plug":{"snap":"bitwarden","plug":"opengl"},"interface":"opengl"},{"slot":{"snap":"core","slot":"pulseaudio"},"plug":{"snap":"bitwarden","plug":"pulseaudio"},"interface":"pulseaudio"},{"slot":{"snap":"core","slot":"unity7"},"plug":{"snap":"bitwarden","plug":"unity7"},"interface":"unity7"},{"slot":{"snap":"core","slot":"wayland"},"plug":{"snap":"bitwarden","plug":"wayland"},"interface":"wayland"},{"slot":{"snap":"core","slot":"x11"},"plug":{"snap":"bitwarden","plug":"x11"},"interface":"x11"},{"slot":{"snap":"core","slot":"network"},"plug":{"snap":"bw","plug":"network"},"interface":"network"},{"slot":{"snap":"core","slot":"network-bind"},"plug":{"snap":"bw","plug":"network-bind"},"interface":"network-bind"}],"plugs":[{"snap":"bitwarden","plug":"audio-playback","interface":"audio-playback","apps":["bitwarden"],"connections":[{"snap":"core","slot":"audio-playback"}]},{"snap":"bitwarden","plug":"browser-support","interface":"browser-support","apps":["bitwarden"],"connections":[{"snap":"core","slot":"browser-support"}]},{"snap":"bitwarden","plug":"desktop","interface":"desktop","apps":["bitwarden"],"connections":[{"snap":"core","slot":"desktop"}]},{"snap":"bitwarden","plug":"desktop-legacy","interface":"desktop-legacy","apps":["bitwarden"],"connections":[{"snap":"core","slot":"desktop-legacy"}]},{"snap":"bitwarden","plug":"gnome-3-28-1804","interface":"content","attrs":{"content":"gnome-3-28-1804","default-provider":"gnome-3-28-1804","target":"$SNAP/gnome-platform"},"apps":["bitwarden"],"connections":[{"snap":"gnome-3-28-1804","slot":"gnome-3-28-1804"}]},{"snap":"bitwarden","plug":"gsettings","interface":"gsettings","apps":["bitwarden"],"connections":[{"snap":"core","slot":"gsettings"}]},{"snap":"bitwarden","plug":"home","interface":"home","apps":["bitwarden"],"connections":[{"snap":"core","slot":"home"}]},{"snap":"bitwarden","plug":"network","interface":"network","apps":["bitwarden"],"connections":[{"snap":"core","slot":"network"}]},{"snap":"bitwarden","plug":"opengl","interface":"opengl","apps":["bitwarden"],"connections":[{"snap":"core","slot":"opengl"}]},{"snap":"bitwarden","plug":"pulseaudio","interface":"pulseaudio","apps":["bitwarden"],"connections":[{"snap":"core","slot":"pulseaudio"}]},{"snap":"bitwarden","plug":"unity7","interface":"unity7","apps":["bitwarden"],"connections":[{"snap":"core","slot":"unity7"}]},{"snap":"bitwarden","plug":"wayland","interface":"wayland","apps":["bitwarden"],"connections":[{"snap":"core","slot":"wayland"}]},{"snap":"bitwarden","plug":"x11","interface":"x11","apps":["bitwarden"],"connections":[{"snap":"core","slot":"x11"}]},{"snap":"bw","plug":"network","interface":"network","apps":["bw"],"connections":[{"snap":"core","slot":"network"}]},{"snap":"bw","plug":"network-bind","interface":"network-bind","apps":["bw"],"connections":[{"snap":"core","slot":"network-bind"}]}],"slots":[{"snap":"core","slot":"audio-playback","interface":"audio-playback","connections":[{"snap":"bitwarden","plug":"audio-playback"}]},{"snap":"core","slot":"browser-support","interface":"browser-support","connections":[{"snap":"bitwarden","plug":"browser-support"}]},{"snap":"core","slot":"desktop","interface":"desktop","connections":[{"snap":"bitwarden","plug":"desktop"}]},{"snap":"core","slot":"desktop-legacy","interface":"desktop-legacy","connections":[{"snap":"bitwarden","plug":"desktop-legacy"}]},{"snap":"core","slot":"gsettings","interface":"gsettings","connections":[{"snap":"bitwarden","plug":"gsettings"}]},{"snap":"core","slot":"home","interface":"home","connections":[{"snap":"bitwarden","plug":"home"}]},{"snap":"core","slot":"network","interface":"network","connections":[{"snap":"bitwarden","plug":"network"},{"snap":"bw","plug":"network"}]},{"snap":"core","slot":"network-bind","interface":"network-bind","connections":[{"snap":"bw","plug":"network-bind"}]},{"snap":"core","slot":"opengl","interface":"opengl","connections":[{"snap":"bitwarden","plug":"opengl"}]},{"snap":"core","slot":"pulseaudio","interface":"pulseaudio","connections":[{"snap":"bitwarden","plug":"pulseaudio"}]},{"snap":"core","slot":"unity7","interface":"unity7","connections":[{"snap":"bitwarden","plug":"unity7"}]},{"snap":"core","slot":"wayland","interface":"wayland","connections":[{"snap":"bitwarden","plug":"wayland"}]},{"snap":"core","slot":"x11","interface":"x11","connections":[{"snap":"bitwarden","plug":"x11"}]},{"snap":"gnome-3-28-1804","slot":"gnome-3-28-1804","interface":"content","attrs":{"content":"gnome-3-28-1804","read":["/"]},"connections":[{"snap":"bitwarden","plug":"gnome-3-28-1804"}]}]}}'


@pytest.fixture
def snap_connections_all_out():
    return '{"type":"sync","status-code":200,"status":"OK","result":{"established":[{"slot":{"snap":"core","slot":"audio-playback"},"plug":{"snap":"bitwarden","plug":"audio-playback"},"interface":"audio-playback"},{"slot":{"snap":"core","slot":"browser-support"},"plug":{"snap":"bitwarden","plug":"browser-support"},"interface":"browser-support"},{"slot":{"snap":"core","slot":"desktop"},"plug":{"snap":"bitwarden","plug":"desktop"},"interface":"desktop"},{"slot":{"snap":"core","slot":"desktop-legacy"},"plug":{"snap":"bitwarden","plug":"desktop-legacy"},"interface":"desktop-legacy"},{"slot":{"snap":"gnome-3-28-1804","slot":"gnome-3-28-1804"},"plug":{"snap":"bitwarden","plug":"gnome-3-28-1804"},"interface":"content","slot-attrs":{"content":"gnome-3-28-1804","read":["/"]},"plug-attrs":{"content":"gnome-3-28-1804","default-provider":"gnome-3-28-1804","target":"$SNAP/gnome-platform"}},{"slot":{"snap":"core","slot":"gsettings"},"plug":{"snap":"bitwarden","plug":"gsettings"},"interface":"gsettings"},{"slot":{"snap":"core","slot":"home"},"plug":{"snap":"bitwarden","plug":"home"},"interface":"home"},{"slot":{"snap":"core","slot":"network"},"plug":{"snap":"bitwarden","plug":"network"},"interface":"network"},{"slot":{"snap":"core","slot":"opengl"},"plug":{"snap":"bitwarden","plug":"opengl"},"interface":"opengl"},{"slot":{"snap":"core","slot":"pulseaudio"},"plug":{"snap":"bitwarden","plug":"pulseaudio"},"interface":"pulseaudio"},{"slot":{"snap":"core","slot":"unity7"},"plug":{"snap":"bitwarden","plug":"unity7"},"interface":"unity7"},{"slot":{"snap":"core","slot":"wayland"},"plug":{"snap":"bitwarden","plug":"wayland"},"interface":"wayland"},{"slot":{"snap":"core","slot":"x11"},"plug":{"snap":"bitwarden","plug":"x11"},"interface":"x11"},{"slot":{"snap":"core","slot":"network"},"plug":{"snap":"bw","plug":"network"},"interface":"network"},{"slot":{"snap":"core","slot":"network-bind"},"plug":{"snap":"bw","plug":"network-bind"},"interface":"network-bind"}],"plugs":[{"snap":"bitwarden","plug":"audio-playback","interface":"audio-playback","apps":["bitwarden"],"connections":[{"snap":"core","slot":"audio-playback"}]},{"snap":"bitwarden","plug":"browser-support","interface":"browser-support","apps":["bitwarden"],"connections":[{"snap":"core","slot":"browser-support"}]},{"snap":"bitwarden","plug":"desktop","interface":"desktop","apps":["bitwarden"],"connections":[{"snap":"core","slot":"desktop"}]},{"snap":"bitwarden","plug":"desktop-legacy","interface":"desktop-legacy","apps":["bitwarden"],"connections":[{"snap":"core","slot":"desktop-legacy"}]},{"snap":"bitwarden","plug":"gnome-3-28-1804","interface":"content","attrs":{"content":"gnome-3-28-1804","default-provider":"gnome-3-28-1804","target":"$SNAP/gnome-platform"},"apps":["bitwarden"],"connections":[{"snap":"gnome-3-28-1804","slot":"gnome-3-28-1804"}]},{"snap":"bitwarden","plug":"gsettings","interface":"gsettings","apps":["bitwarden"],"connections":[{"snap":"core","slot":"gsettings"}]},{"snap":"bitwarden","plug":"gtk-3-themes","interface":"content","attrs":{"content":"gtk-3-themes","default-provider":"gtk-common-themes","target":"$SNAP/data-dir/themes"},"apps":["bitwarden"]},{"snap":"bitwarden","plug":"home","interface":"home","apps":["bitwarden"],"connections":[{"snap":"core","slot":"home"}]},{"snap":"bitwarden","plug":"icon-themes","interface":"content","attrs":{"content":"icon-themes","default-provider":"gtk-common-themes","target":"$SNAP/data-dir/icons"},"apps":["bitwarden"]},{"snap":"bitwarden","plug":"network","interface":"network","apps":["bitwarden"],"connections":[{"snap":"core","slot":"network"}]},{"snap":"bitwarden","plug":"opengl","interface":"opengl","apps":["bitwarden"],"connections":[{"snap":"core","slot":"opengl"}]},{"snap":"bitwarden","plug":"password-manager-service","interface":"password-manager-service","apps":["bitwarden"]},{"snap":"bitwarden","plug":"pulseaudio","interface":"pulseaudio","apps":["bitwarden"],"connections":[{"snap":"core","slot":"pulseaudio"}]},{"snap":"bitwarden","plug":"sound-themes","interface":"content","attrs":{"content":"sound-themes","default-provider":"gtk-common-themes","target":"$SNAP/data-dir/sounds"},"apps":["bitwarden"]},{"snap":"bitwarden","plug":"unity7","interface":"unity7","apps":["bitwarden"],"connections":[{"snap":"core","slot":"unity7"}]},{"snap":"bitwarden","plug":"wayland","interface":"wayland","apps":["bitwarden"],"connections":[{"snap":"core","slot":"wayland"}]},{"snap":"bitwarden","plug":"x11","interface":"x11","apps":["bitwarden"],"connections":[{"snap":"core","slot":"x11"}]},{"snap":"bw","plug":"network","interface":"network","apps":["bw"],"connections":[{"snap":"core","slot":"network"}]},{"snap":"bw","plug":"network-bind","interface":"network-bind","apps":["bw"],"connections":[{"snap":"core","slot":"network-bind"}]}],"slots":[{"snap":"core","slot":"account-control","interface":"account-control"},{"snap":"core","slot":"accounts-service","interface":"accounts-service"},{"snap":"core","slot":"acrn-support","interface":"acrn-support"},{"snap":"core","slot":"adb-support","interface":"adb-support"},{"snap":"core","slot":"allegro-vcu","interface":"allegro-vcu"},{"snap":"core","slot":"alsa","interface":"alsa"},{"snap":"core","slot":"appstream-metadata","interface":"appstream-metadata"},{"snap":"core","slot":"audio-playback","interface":"audio-playback","connections":[{"snap":"bitwarden","plug":"audio-playback"}]},{"snap":"core","slot":"audio-record","interface":"audio-record"},{"snap":"core","slot":"autopilot-introspection","interface":"autopilot-introspection"},{"snap":"core","slot":"avahi-control","interface":"avahi-control"},{"snap":"core","slot":"avahi-observe","interface":"avahi-observe"},{"snap":"core","slot":"block-devices","interface":"block-devices"},{"snap":"core","slot":"bluetooth-control","interface":"bluetooth-control"},{"snap":"core","slot":"bluez","interface":"bluez"},{"snap":"core","slot":"broadcom-asic-control","interface":"broadcom-asic-control"},{"snap":"core","slot":"browser-support","interface":"browser-support","connections":[{"snap":"bitwarden","plug":"browser-support"}]},{"snap":"core","slot":"calendar-service","interface":"calendar-service"},{"snap":"core","slot":"camera","interface":"camera"},{"snap":"core","slot":"can-bus","interface":"can-bus"},{"snap":"core","slot":"cifs-mount","interface":"cifs-mount"},{"snap":"core","slot":"classic-support","interface":"classic-support"},{"snap":"core","slot":"contacts-service","interface":"contacts-service"},{"snap":"core","slot":"core-support","interface":"core-support"},{"snap":"core","slot":"cpu-control","interface":"cpu-control"},{"snap":"core","slot":"cups-control","interface":"cups-control"},{"snap":"core","slot":"daemon-notify","interface":"daemon-notify"},{"snap":"core","slot":"dcdbas-control","interface":"dcdbas-control"},{"snap":"core","slot":"desktop","interface":"desktop","connections":[{"snap":"bitwarden","plug":"desktop"}]},{"snap":"core","slot":"desktop-launch","interface":"desktop-launch"},{"snap":"core","slot":"desktop-legacy","interface":"desktop-legacy","connections":[{"snap":"bitwarden","plug":"desktop-legacy"}]},{"snap":"core","slot":"device-buttons","interface":"device-buttons"},{"snap":"core","slot":"display-control","interface":"display-control"},{"snap":"core","slot":"dm-crypt","interface":"dm-crypt"},{"snap":"core","slot":"docker-support","interface":"docker-support"},{"snap":"core","slot":"dvb","interface":"dvb"},{"snap":"core","slot":"firewall-control","interface":"firewall-control"},{"snap":"core","slot":"fpga","interface":"fpga"},{"snap":"core","slot":"framebuffer","interface":"framebuffer"},{"snap":"core","slot":"fuse-support","interface":"fuse-support"},{"snap":"core","slot":"fwupd","interface":"fwupd"},{"snap":"core","slot":"gconf","interface":"gconf"},{"snap":"core","slot":"gpg-keys","interface":"gpg-keys"},{"snap":"core","slot":"gpg-public-keys","interface":"gpg-public-keys"},{"snap":"core","slot":"gpio-control","interface":"gpio-control"},{"snap":"core","slot":"gpio-memory-control","interface":"gpio-memory-control"},{"snap":"core","slot":"greengrass-support","interface":"greengrass-support"},{"snap":"core","slot":"gsettings","interface":"gsettings","connections":[{"snap":"bitwarden","plug":"gsettings"}]},{"snap":"core","slot":"hardware-observe","interface":"hardware-observe"},{"snap":"core","slot":"hardware-random-control","interface":"hardware-random-control"},{"snap":"core","slot":"hardware-random-observe","interface":"hardware-random-observe"},{"snap":"core","slot":"home","interface":"home","connections":[{"snap":"bitwarden","plug":"home"}]},{"snap":"core","slot":"hostname-control","interface":"hostname-control"},{"snap":"core","slot":"hugepages-control","interface":"hugepages-control"},{"snap":"core","slot":"intel-mei","interface":"intel-mei"},{"snap":"core","slot":"io-ports-control","interface":"io-ports-control"},{"snap":"core","slot":"ion-memory-control","interface":"ion-memory-control"},{"snap":"core","slot":"jack1","interface":"jack1"},{"snap":"core","slot":"joystick","interface":"joystick"},{"snap":"core","slot":"juju-client-observe","interface":"juju-client-observe"},{"snap":"core","slot":"kernel-crypto-api","interface":"kernel-crypto-api"},{"snap":"core","slot":"kernel-module-control","interface":"kernel-module-control"},{"snap":"core","slot":"kernel-module-load","interface":"kernel-module-load"},{"snap":"core","slot":"kernel-module-observe","interface":"kernel-module-observe"},{"snap":"core","slot":"kubernetes-support","interface":"kubernetes-support"},{"snap":"core","slot":"kvm","interface":"kvm"},{"snap":"core","slot":"libvirt","interface":"libvirt"},{"snap":"core","slot":"locale-control","interface":"locale-control"},{"snap":"core","slot":"log-observe","interface":"log-observe"},{"snap":"core","slot":"login-session-control","interface":"login-session-control"},{"snap":"core","slot":"login-session-observe","interface":"login-session-observe"},{"snap":"core","slot":"lxd-support","interface":"lxd-support"},{"snap":"core","slot":"media-control","interface":"media-control"},{"snap":"core","slot":"microstack-support","interface":"microstack-support"},{"snap":"core","slot":"modem-manager","interface":"modem-manager"},{"snap":"core","slot":"mount-control","interface":"mount-control"},{"snap":"core","slot":"mount-observe","interface":"mount-observe"},{"snap":"core","slot":"multipass-support","interface":"multipass-support"},{"snap":"core","slot":"netlink-audit","interface":"netlink-audit"},{"snap":"core","slot":"netlink-connector","interface":"netlink-connector"},{"snap":"core","slot":"network","interface":"network","connections":[{"snap":"bitwarden","plug":"network"},{"snap":"bw","plug":"network"}]},{"snap":"core","slot":"network-bind","interface":"network-bind","connections":[{"snap":"bw","plug":"network-bind"}]},{"snap":"core","slot":"network-control","interface":"network-control"},{"snap":"core","slot":"network-manager","interface":"network-manager"},{"snap":"core","slot":"network-manager-observe","interface":"network-manager-observe"},{"snap":"core","slot":"network-observe","interface":"network-observe"},{"snap":"core","slot":"network-setup-control","interface":"network-setup-control"},{"snap":"core","slot":"network-setup-observe","interface":"network-setup-observe"},{"snap":"core","slot":"network-status","interface":"network-status"},{"snap":"core","slot":"nvidia-drivers-support","interface":"nvidia-drivers-support"},{"snap":"core","slot":"ofono","interface":"ofono"},{"snap":"core","slot":"opengl","interface":"opengl","connections":[{"snap":"bitwarden","plug":"opengl"}]},{"snap":"core","slot":"openvswitch","interface":"openvswitch"},{"snap":"core","slot":"openvswitch-support","interface":"openvswitch-support"},{"snap":"core","slot":"optical-drive","interface":"optical-drive"},{"snap":"core","slot":"packagekit-control","interface":"packagekit-control"},{"snap":"core","slot":"password-manager-service","interface":"password-manager-service"},{"snap":"core","slot":"pcscd","interface":"pcscd"},{"snap":"core","slot":"personal-files","interface":"personal-files"},{"snap":"core","slot":"physical-memory-control","interface":"physical-memory-control"},{"snap":"core","slot":"physical-memory-observe","interface":"physical-memory-observe"},{"snap":"core","slot":"polkit","interface":"polkit"},{"snap":"core","slot":"power-control","interface":"power-control"},{"snap":"core","slot":"ppp","interface":"ppp"},{"snap":"core","slot":"process-control","interface":"process-control"},{"snap":"core","slot":"ptp","interface":"ptp"},{"snap":"core","slot":"pulseaudio","interface":"pulseaudio","connections":[{"snap":"bitwarden","plug":"pulseaudio"}]},{"snap":"core","slot":"qualcomm-ipc-router","interface":"qualcomm-ipc-router"},{"snap":"core","slot":"raw-input","interface":"raw-input"},{"snap":"core","slot":"raw-usb","interface":"raw-usb"},{"snap":"core","slot":"removable-media","interface":"removable-media"},{"snap":"core","slot":"screen-inhibit-control","interface":"screen-inhibit-control"},{"snap":"core","slot":"screencast-legacy","interface":"screencast-legacy"},{"snap":"core","slot":"scsi-generic","interface":"scsi-generic"},{"snap":"core","slot":"sd-control","interface":"sd-control"},{"snap":"core","slot":"shared-memory","interface":"shared-memory"},{"snap":"core","slot":"shutdown","interface":"shutdown"},{"snap":"core","slot":"snap-refresh-control","interface":"snap-refresh-control"},{"snap":"core","slot":"snap-themes-control","interface":"snap-themes-control"},{"snap":"core","slot":"snapd-control","interface":"snapd-control"},{"snap":"core","slot":"ssh-keys","interface":"ssh-keys"},{"snap":"core","slot":"ssh-public-keys","interface":"ssh-public-keys"},{"snap":"core","slot":"steam-support","interface":"steam-support"},{"snap":"core","slot":"system-backup","interface":"system-backup"},{"snap":"core","slot":"system-files","interface":"system-files"},{"snap":"core","slot":"system-observe","interface":"system-observe"},{"snap":"core","slot":"system-packages-doc","interface":"system-packages-doc"},{"snap":"core","slot":"system-source-code","interface":"system-source-code"},{"snap":"core","slot":"system-trace","interface":"system-trace"},{"snap":"core","slot":"tee","interface":"tee"},{"snap":"core","slot":"time-control","interface":"time-control"},{"snap":"core","slot":"timeserver-control","interface":"timeserver-control"},{"snap":"core","slot":"timezone-control","interface":"timezone-control"},{"snap":"core","slot":"tpm","interface":"tpm"},{"snap":"core","slot":"u2f-devices","interface":"u2f-devices"},{"snap":"core","slot":"udisks2","interface":"udisks2"},{"snap":"core","slot":"uhid","interface":"uhid"},{"snap":"core","slot":"uinput","interface":"uinput"},{"snap":"core","slot":"unity7","interface":"unity7","connections":[{"snap":"bitwarden","plug":"unity7"}]},{"snap":"core","slot":"upower-observe","interface":"upower-observe"},{"snap":"core","slot":"userns","interface":"userns"},{"snap":"core","slot":"vcio","interface":"vcio"},{"snap":"core","slot":"wayland","interface":"wayland","connections":[{"snap":"bitwarden","plug":"wayland"}]},{"snap":"core","slot":"x11","interface":"x11","connections":[{"snap":"bitwarden","plug":"x11"}]},{"snap":"core","slot":"xilinx-dma","interface":"xilinx-dma"},{"snap":"gnome-3-28-1804","slot":"gnome-3-28-1804","interface":"content","attrs":{"content":"gnome-3-28-1804","read":["/"]},"connections":[{"snap":"bitwarden","plug":"gnome-3-28-1804"}]},{"snap":"gnome-3-34-1804","slot":"gnome-3-34-1804","interface":"content","attrs":{"content":"gnome-3-34-1804","read":["/"]}}]}}'


@pytest.fixture
def snap_connections_name_out():
    return '{"type":"sync","status-code":200,"status":"OK","result":{"established":[{"slot":{"snap":"core","slot":"audio-playback"},"plug":{"snap":"bitwarden","plug":"audio-playback"},"interface":"audio-playback"},{"slot":{"snap":"core","slot":"browser-support"},"plug":{"snap":"bitwarden","plug":"browser-support"},"interface":"browser-support"},{"slot":{"snap":"core","slot":"desktop"},"plug":{"snap":"bitwarden","plug":"desktop"},"interface":"desktop"},{"slot":{"snap":"core","slot":"desktop-legacy"},"plug":{"snap":"bitwarden","plug":"desktop-legacy"},"interface":"desktop-legacy"},{"slot":{"snap":"gnome-3-28-1804","slot":"gnome-3-28-1804"},"plug":{"snap":"bitwarden","plug":"gnome-3-28-1804"},"interface":"content","slot-attrs":{"content":"gnome-3-28-1804","read":["/"]},"plug-attrs":{"content":"gnome-3-28-1804","default-provider":"gnome-3-28-1804","target":"$SNAP/gnome-platform"}},{"slot":{"snap":"core","slot":"gsettings"},"plug":{"snap":"bitwarden","plug":"gsettings"},"interface":"gsettings"},{"slot":{"snap":"core","slot":"home"},"plug":{"snap":"bitwarden","plug":"home"},"interface":"home"},{"slot":{"snap":"core","slot":"network"},"plug":{"snap":"bitwarden","plug":"network"},"interface":"network"},{"slot":{"snap":"core","slot":"opengl"},"plug":{"snap":"bitwarden","plug":"opengl"},"interface":"opengl"},{"slot":{"snap":"core","slot":"pulseaudio"},"plug":{"snap":"bitwarden","plug":"pulseaudio"},"interface":"pulseaudio"},{"slot":{"snap":"core","slot":"unity7"},"plug":{"snap":"bitwarden","plug":"unity7"},"interface":"unity7"},{"slot":{"snap":"core","slot":"wayland"},"plug":{"snap":"bitwarden","plug":"wayland"},"interface":"wayland"},{"slot":{"snap":"core","slot":"x11"},"plug":{"snap":"bitwarden","plug":"x11"},"interface":"x11"}],"plugs":[{"snap":"bitwarden","plug":"audio-playback","interface":"audio-playback","apps":["bitwarden"],"connections":[{"snap":"core","slot":"audio-playback"}]},{"snap":"bitwarden","plug":"browser-support","interface":"browser-support","apps":["bitwarden"],"connections":[{"snap":"core","slot":"browser-support"}]},{"snap":"bitwarden","plug":"desktop","interface":"desktop","apps":["bitwarden"],"connections":[{"snap":"core","slot":"desktop"}]},{"snap":"bitwarden","plug":"desktop-legacy","interface":"desktop-legacy","apps":["bitwarden"],"connections":[{"snap":"core","slot":"desktop-legacy"}]},{"snap":"bitwarden","plug":"gnome-3-28-1804","interface":"content","attrs":{"content":"gnome-3-28-1804","default-provider":"gnome-3-28-1804","target":"$SNAP/gnome-platform"},"apps":["bitwarden"],"connections":[{"snap":"gnome-3-28-1804","slot":"gnome-3-28-1804"}]},{"snap":"bitwarden","plug":"gsettings","interface":"gsettings","apps":["bitwarden"],"connections":[{"snap":"core","slot":"gsettings"}]},{"snap":"bitwarden","plug":"home","interface":"home","apps":["bitwarden"],"connections":[{"snap":"core","slot":"home"}]},{"snap":"bitwarden","plug":"network","interface":"network","apps":["bitwarden"],"connections":[{"snap":"core","slot":"network"}]},{"snap":"bitwarden","plug":"opengl","interface":"opengl","apps":["bitwarden"],"connections":[{"snap":"core","slot":"opengl"}]},{"snap":"bitwarden","plug":"pulseaudio","interface":"pulseaudio","apps":["bitwarden"],"connections":[{"snap":"core","slot":"pulseaudio"}]},{"snap":"bitwarden","plug":"unity7","interface":"unity7","apps":["bitwarden"],"connections":[{"snap":"core","slot":"unity7"}]},{"snap":"bitwarden","plug":"wayland","interface":"wayland","apps":["bitwarden"],"connections":[{"snap":"core","slot":"wayland"}]},{"snap":"bitwarden","plug":"x11","interface":"x11","apps":["bitwarden"],"connections":[{"snap":"core","slot":"x11"}]}],"slots":[{"snap":"core","slot":"audio-playback","interface":"audio-playback","connections":[{"snap":"bitwarden","plug":"audio-playback"}]},{"snap":"core","slot":"browser-support","interface":"browser-support","connections":[{"snap":"bitwarden","plug":"browser-support"}]},{"snap":"core","slot":"desktop","interface":"desktop","connections":[{"snap":"bitwarden","plug":"desktop"}]},{"snap":"core","slot":"desktop-legacy","interface":"desktop-legacy","connections":[{"snap":"bitwarden","plug":"desktop-legacy"}]},{"snap":"core","slot":"gsettings","interface":"gsettings","connections":[{"snap":"bitwarden","plug":"gsettings"}]},{"snap":"core","slot":"home","interface":"home","connections":[{"snap":"bitwarden","plug":"home"}]},{"snap":"core","slot":"network","interface":"network","connections":[{"snap":"bitwarden","plug":"network"}]},{"snap":"core","slot":"opengl","interface":"opengl","connections":[{"snap":"bitwarden","plug":"opengl"}]},{"snap":"core","slot":"pulseaudio","interface":"pulseaudio","connections":[{"snap":"bitwarden","plug":"pulseaudio"}]},{"snap":"core","slot":"unity7","interface":"unity7","connections":[{"snap":"bitwarden","plug":"unity7"}]},{"snap":"core","slot":"wayland","interface":"wayland","connections":[{"snap":"bitwarden","plug":"wayland"}]},{"snap":"core","slot":"x11","interface":"x11","connections":[{"snap":"bitwarden","plug":"x11"}]},{"snap":"gnome-3-28-1804","slot":"gnome-3-28-1804","interface":"content","attrs":{"content":"gnome-3-28-1804","read":["/"]},"connections":[{"snap":"bitwarden","plug":"gnome-3-28-1804"}]}]}}'


@pytest.fixture
def snap_connections_interface_out():
    return '{"type":"sync","status-code":200,"status":"OK","result":{"established":[{"slot":{"snap":"core","slot":"network"},"plug":{"snap":"bitwarden","plug":"network"},"interface":"network"},{"slot":{"snap":"core","slot":"network"},"plug":{"snap":"bw","plug":"network"},"interface":"network"}],"plugs":[{"snap":"bitwarden","plug":"network","interface":"network","apps":["bitwarden"],"connections":[{"snap":"core","slot":"network"}]},{"snap":"bw","plug":"network","interface":"network","apps":["bw"],"connections":[{"snap":"core","slot":"network"}]}],"slots":[{"snap":"core","slot":"network","interface":"network","connections":[{"snap":"bitwarden","plug":"network"},{"snap":"bw","plug":"network"}]}]}}'


@pytest.fixture
def snap_connections_interface_name_out():
    return '{"type":"sync","status-code":200,"status":"OK","result":{"established":[{"slot":{"snap":"core","slot":"network"},"plug":{"snap":"bitwarden","plug":"network"},"interface":"network"}],"plugs":[{"snap":"bitwarden","plug":"network","interface":"network","apps":["bitwarden"],"connections":[{"snap":"core","slot":"network"}]}],"slots":[{"snap":"core","slot":"network","interface":"network","connections":[{"snap":"bitwarden","plug":"network"}]}]}}'


@pytest.fixture
def snap_interfaces_out():
    return '{"type":"sync","status-code":200,"status":"OK","result":[{"name":"audio-playback","summary":"allows audio playback via supporting services","plugs":[{"snap":"bitwarden","plug":"audio-playback"}],"slots":[{"snap":"core","slot":"audio-playback"}]},{"name":"browser-support","summary":"allows access to various APIs needed by modern web browsers","plugs":[{"snap":"bitwarden","plug":"browser-support"}],"slots":[{"snap":"core","slot":"browser-support"}]},{"name":"content","summary":"allows sharing code and data with other snaps","plugs":[{"snap":"bitwarden","plug":"gnome-3-28-1804","attrs":{"content":"gnome-3-28-1804","default-provider":"gnome-3-28-1804","target":"$SNAP/gnome-platform"}},{"snap":"bitwarden","plug":"gtk-3-themes","attrs":{"content":"gtk-3-themes","default-provider":"gtk-common-themes","target":"$SNAP/data-dir/themes"}},{"snap":"bitwarden","plug":"icon-themes","attrs":{"content":"icon-themes","default-provider":"gtk-common-themes","target":"$SNAP/data-dir/icons"}},{"snap":"bitwarden","plug":"sound-themes","attrs":{"content":"sound-themes","default-provider":"gtk-common-themes","target":"$SNAP/data-dir/sounds"}}],"slots":[{"snap":"gnome-3-28-1804","slot":"gnome-3-28-1804","attrs":{"content":"gnome-3-28-1804","read":["/"]}},{"snap":"gnome-3-34-1804","slot":"gnome-3-34-1804","attrs":{"content":"gnome-3-34-1804","read":["/"]}}]},{"name":"desktop","summary":"allows access to basic graphical desktop resources","plugs":[{"snap":"bitwarden","plug":"desktop"}],"slots":[{"snap":"core","slot":"desktop"}]},{"name":"desktop-legacy","summary":"allows privileged access to desktop legacy methods","plugs":[{"snap":"bitwarden","plug":"desktop-legacy"}],"slots":[{"snap":"core","slot":"desktop-legacy"}]},{"name":"gsettings","summary":"allows access to any gsettings item of current user","plugs":[{"snap":"bitwarden","plug":"gsettings"}],"slots":[{"snap":"core","slot":"gsettings"}]},{"name":"home","summary":"allows access to non-hidden files in the home directory","plugs":[{"snap":"bitwarden","plug":"home"}],"slots":[{"snap":"core","slot":"home"}]},{"name":"network","summary":"allows access to the network","plugs":[{"snap":"bitwarden","plug":"network"},{"snap":"bw","plug":"network"}],"slots":[{"snap":"core","slot":"network"}]},{"name":"network-bind","summary":"allows operating as a network service","plugs":[{"snap":"bw","plug":"network-bind"}],"slots":[{"snap":"core","slot":"network-bind"}]},{"name":"opengl","summary":"allows access to OpenGL stack","plugs":[{"snap":"bitwarden","plug":"opengl"}],"slots":[{"snap":"core","slot":"opengl"}]},{"name":"pulseaudio","summary":"allows operating as or interacting with the pulseaudio service","plugs":[{"snap":"bitwarden","plug":"pulseaudio"}],"slots":[{"snap":"core","slot":"pulseaudio"}]},{"name":"unity7","summary":"allows interacting with Unity 7 services","plugs":[{"snap":"bitwarden","plug":"unity7"}],"slots":[{"snap":"core","slot":"unity7"}]},{"name":"wayland","summary":"allows access to compositors supporting wayland protocol","plugs":[{"snap":"bitwarden","plug":"wayland"}],"slots":[{"snap":"core","slot":"wayland"}]},{"name":"x11","summary":"allows interacting with or running as an X11 server","plugs":[{"snap":"bitwarden","plug":"x11"}],"slots":[{"snap":"core","slot":"x11"}]}]}'


@pytest.fixture
def snap_interfaces_all_out():
    return """{"type":"sync","status-code":200,"status":"OK","result":[{"name":"account-control","summary":"allows managing non-system user accounts","slots":[{"snap":"core","slot":"account-control"}]},{"name":"accounts-service","summary":"allows communication with the Accounts service like GNOME Online Accounts","slots":[{"snap":"core","slot":"accounts-service"}]},{"name":"acrn-support","summary":"allows operating managing the ACRN hypervisor","slots":[{"snap":"core","slot":"acrn-support"}]},{"name":"adb-support","summary":"allows operating as Android Debug Bridge service","slots":[{"snap":"core","slot":"adb-support"}]},{"name":"allegro-vcu","summary":"allows access to Allegro Video Code Unit","slots":[{"snap":"core","slot":"allegro-vcu"}]},{"name":"alsa","summary":"allows access to raw ALSA devices","slots":[{"snap":"core","slot":"alsa"}]},{"name":"appstream-metadata","summary":"allows access to AppStream metadata","slots":[{"snap":"core","slot":"appstream-metadata"}]},{"name":"audio-playback","summary":"allows audio playback via supporting services","plugs":[{"snap":"bitwarden","plug":"audio-playback"}],"slots":[{"snap":"core","slot":"audio-playback"}]},{"name":"audio-record","summary":"allows audio recording via supporting services","slots":[{"snap":"core","slot":"audio-record"}]},{"name":"autopilot-introspection","summary":"allows introspection of application user interface","slots":[{"snap":"core","slot":"autopilot-introspection"}]},{"name":"avahi-control","summary":"allows control over service discovery on a local network via the mDNS/DNS-SD protocol suite","slots":[{"snap":"core","slot":"avahi-control"}]},{"name":"avahi-observe","summary":"allows discovery on a local network via the mDNS/DNS-SD protocol suite","slots":[{"snap":"core","slot":"avahi-observe"}]},{"name":"block-devices","summary":"allows access to disk block devices","slots":[{"snap":"core","slot":"block-devices"}]},{"name":"bluetooth-control","summary":"allows managing the kernel bluetooth stack","slots":[{"snap":"core","slot":"bluetooth-control"}]},{"name":"bluez","summary":"allows operating as the bluez service","slots":[{"snap":"core","slot":"bluez"}]},{"name":"bool-file","summary":"allows access to specific file with bool semantics"},{"name":"broadcom-asic-control","summary":"allows using the broadcom-asic kernel module","slots":[{"snap":"core","slot":"broadcom-asic-control"}]},{"name":"browser-support","summary":"allows access to various APIs needed by modern web browsers","plugs":[{"snap":"bitwarden","plug":"browser-support"}],"slots":[{"snap":"core","slot":"browser-support"}]},{"name":"calendar-service","summary":"allows communication with Evolution Data Service Calendar","slots":[{"snap":"core","slot":"calendar-service"}]},{"name":"camera","summary":"allows access to all cameras","slots":[{"snap":"core","slot":"camera"}]},{"name":"can-bus","summary":"allows access to the CAN bus","slots":[{"snap":"core","slot":"can-bus"}]},{"name":"cifs-mount","summary":"allows mounting and unmounting CIFS filesystems","slots":[{"snap":"core","slot":"cifs-mount"}]},{"name":"classic-support","summary":"special permissions for the classic snap","slots":[{"snap":"core","slot":"classic-support"}]},{"name":"contacts-service","summary":"allows communication with Evolution Data Service Address Book","slots":[{"snap":"core","slot":"contacts-service"}]},{"name":"content","summary":"allows sharing code and data with other snaps","plugs":[{"snap":"bitwarden","plug":"gnome-3-28-1804","attrs":{"content":"gnome-3-28-1804","default-provider":"gnome-3-28-1804","target":"$SNAP/gnome-platform"}},{"snap":"bitwarden","plug":"gtk-3-themes","attrs":{"content":"gtk-3-themes","default-provider":"gtk-common-themes","target":"$SNAP/data-dir/themes"}},{"snap":"bitwarden","plug":"icon-themes","attrs":{"content":"icon-themes","default-provider":"gtk-common-themes","target":"$SNAP/data-dir/icons"}},{"snap":"bitwarden","plug":"sound-themes","attrs":{"content":"sound-themes","default-provider":"gtk-common-themes","target":"$SNAP/data-dir/sounds"}}],"slots":[{"snap":"gnome-3-28-1804","slot":"gnome-3-28-1804","attrs":{"content":"gnome-3-28-1804","read":["/"]}},{"snap":"gnome-3-34-1804","slot":"gnome-3-34-1804","attrs":{"content":"gnome-3-34-1804","read":["/"]}}]},{"name":"core-support","summary":"special permissions for the core snap","slots":[{"snap":"core","slot":"core-support"}]},{"name":"cpu-control","summary":"allows setting CPU tunables","slots":[{"snap":"core","slot":"cpu-control"}]},{"name":"cups","summary":"allows access to the CUPS socket for printing"},{"name":"cups-control","summary":"allows access to the CUPS control socket","slots":[{"snap":"core","slot":"cups-control"}]},{"name":"custom-device","summary":"provides access to custom devices specified via the gadget snap"},{"name":"daemon-notify","summary":"allows sending daemon status changes to service manager","slots":[{"snap":"core","slot":"daemon-notify"}]},{"name":"dbus","summary":"allows owning a specific name on DBus"},{"name":"dcdbas-control","summary":"allows access to Dell Systems Management Base Driver","slots":[{"snap":"core","slot":"dcdbas-control"}]},{"name":"desktop","summary":"allows access to basic graphical desktop resources","plugs":[{"snap":"bitwarden","plug":"desktop"}],"slots":[{"snap":"core","slot":"desktop"}]},{"name":"desktop-launch","summary":"allows snaps to identify and launch desktop applications in (or from) other snaps","slots":[{"snap":"core","slot":"desktop-launch"}]},{"name":"desktop-legacy","summary":"allows privileged access to desktop legacy methods","plugs":[{"snap":"bitwarden","plug":"desktop-legacy"}],"slots":[{"snap":"core","slot":"desktop-legacy"}]},{"name":"device-buttons","summary":"allows access to device buttons as input events","slots":[{"snap":"core","slot":"device-buttons"}]},{"name":"display-control","summary":"allows configuring display parameters","slots":[{"snap":"core","slot":"display-control"}]},{"name":"dm-crypt","summary":"allows encryption and decryption of block storage devices","slots":[{"snap":"core","slot":"dm-crypt"}]},{"name":"docker","summary":"allows access to Docker socket"},{"name":"docker-support","summary":"allows operating as the Docker daemon","slots":[{"snap":"core","slot":"docker-support"}]},{"name":"dsp","summary":"allows controlling digital signal processors on certain boards"},{"name":"dvb","summary":"allows access to all DVB (Digital Video Broadcasting) devices and APIs","slots":[{"snap":"core","slot":"dvb"}]},{"name":"empty","summary":"allows testing without providing any additional permissions"},{"name":"firewall-control","summary":"allows control over network firewall","slots":[{"snap":"core","slot":"firewall-control"}]},{"name":"fpga","summary":"allows access to the FPGA subsystem","slots":[{"snap":"core","slot":"fpga"}]},{"name":"framebuffer","summary":"allows access to universal framebuffer devices","slots":[{"snap":"core","slot":"framebuffer"}]},{"name":"fuse-support","summary":"allows access to the FUSE file system","slots":[{"snap":"core","slot":"fuse-support"}]},{"name":"fwupd","summary":"allows operating as the fwupd service","slots":[{"snap":"core","slot":"fwupd"}]},{"name":"gconf","summary":"allows access to any item from the legacy gconf configuration system for the current user","slots":[{"snap":"core","slot":"gconf"}]},{"name":"gpg-keys","summary":"allows reading gpg user configuration and keys and updating gpg's random seed file","slots":[{"snap":"core","slot":"gpg-keys"}]},{"name":"gpg-public-keys","summary":"allows reading gpg public keys and non-sensitive configuration","slots":[{"snap":"core","slot":"gpg-public-keys"}]},{"name":"gpio","summary":"allows access to specific GPIO pin"},{"name":"gpio-control","summary":"allows control of all aspects of GPIO pins","slots":[{"snap":"core","slot":"gpio-control"}]},{"name":"gpio-memory-control","summary":"allows write access to all gpio memory","slots":[{"snap":"core","slot":"gpio-memory-control"}]},{"name":"greengrass-support","summary":"allows operating as the Greengrass service","slots":[{"snap":"core","slot":"greengrass-support"}]},{"name":"gsettings","summary":"allows access to any gsettings item of current user","plugs":[{"snap":"bitwarden","plug":"gsettings"}],"slots":[{"snap":"core","slot":"gsettings"}]},{"name":"hardware-observe","summary":"allows reading information about system hardware","slots":[{"snap":"core","slot":"hardware-observe"}]},{"name":"hardware-random-control","summary":"allows control over the hardware random number generator","slots":[{"snap":"core","slot":"hardware-random-control"}]},{"name":"hardware-random-observe","summary":"allows reading from hardware random number generator","slots":[{"snap":"core","slot":"hardware-random-observe"}]},{"name":"hidraw","summary":"allows access to specific hidraw device"},{"name":"home","summary":"allows access to non-hidden files in the home directory","plugs":[{"snap":"bitwarden","plug":"home"}],"slots":[{"snap":"core","slot":"home"}]},{"name":"hostname-control","summary":"allows configuring the system hostname","slots":[{"snap":"core","slot":"hostname-control"}]},{"name":"hugepages-control","summary":"allows controlling hugepages","slots":[{"snap":"core","slot":"hugepages-control"}]},{"name":"i2c","summary":"allows access to specific I2C controller"},{"name":"iio","summary":"allows access to a specific IIO device"},{"name":"intel-mei","summary":"allows access to the Intel MEI management interface","slots":[{"snap":"core","slot":"intel-mei"}]},{"name":"io-ports-control","summary":"allows access to all I/O ports","slots":[{"snap":"core","slot":"io-ports-control"}]},{"name":"ion-memory-control","summary":"allows access to The Android ION memory allocator","slots":[{"snap":"core","slot":"ion-memory-control"}]},{"name":"jack1","summary":"allows interacting with a JACK1 server","slots":[{"snap":"core","slot":"jack1"}]},{"name":"joystick","summary":"allows access to joystick devices","slots":[{"snap":"core","slot":"joystick"}]},{"name":"juju-client-observe","summary":"allows read access to juju client configuration","slots":[{"snap":"core","slot":"juju-client-observe"}]},{"name":"kernel-crypto-api","summary":"allows access to the Linux kernel crypto API","slots":[{"snap":"core","slot":"kernel-crypto-api"}]},{"name":"kernel-module-control","summary":"allows insertion, removal and querying of kernel modules","slots":[{"snap":"core","slot":"kernel-module-control"}]},{"name":"kernel-module-load","summary":"allows constrained control over kernel module loading","slots":[{"snap":"core","slot":"kernel-module-load"}]},{"name":"kernel-module-observe","summary":"allows querying of kernel modules","slots":[{"snap":"core","slot":"kernel-module-observe"}]},{"name":"kubernetes-support","summary":"allows operating as the Kubernetes service","slots":[{"snap":"core","slot":"kubernetes-support"}]},{"name":"kvm","summary":"allows access to the kvm device","slots":[{"snap":"core","slot":"kvm"}]},{"name":"libvirt","summary":"allows access to libvirt service","slots":[{"snap":"core","slot":"libvirt"}]},{"name":"locale-control","summary":"allows control over system locale","slots":[{"snap":"core","slot":"locale-control"}]},{"name":"location-control","summary":"allows operating as the location service"},{"name":"location-observe","summary":"allows access to the current physical location"},{"name":"log-observe","summary":"allows read access to system logs","slots":[{"snap":"core","slot":"log-observe"}]},{"name":"login-session-control","summary":"allows setup of login session & seat","slots":[{"snap":"core","slot":"login-session-control"}]},{"name":"login-session-observe","summary":"allows reading login and session information","slots":[{"snap":"core","slot":"login-session-observe"}]},{"name":"lxd","summary":"allows access to the LXD socket"},{"name":"lxd-support","summary":"allows operating as the LXD service","slots":[{"snap":"core","slot":"lxd-support"}]},{"name":"maliit","summary":"allows operating as the Maliit service"},{"name":"media-control","summary":"allows access to media control devices","slots":[{"snap":"core","slot":"media-control"}]},{"name":"media-hub","summary":"allows operating as the media-hub service"},{"name":"microceph","summary":"allows access to the MicroCeph socket"},{"name":"microovn","summary":"allows access to the MicroOVN socket"},{"name":"microstack-support","summary":"allows operating as the MicroStack service","slots":[{"snap":"core","slot":"microstack-support"}]},{"name":"mir","summary":"allows operating as the Mir server"},{"name":"modem-manager","summary":"allows operating as the ModemManager service","slots":[{"snap":"core","slot":"modem-manager"}]},{"name":"mount-control","summary":"allows creating transient and persistent mounts","slots":[{"snap":"core","slot":"mount-control"}]},{"name":"mount-observe","summary":"allows reading mount table and quota information","slots":[{"snap":"core","slot":"mount-observe"}]},{"name":"mpris","summary":"allows operating as an MPRIS player"},{"name":"multipass-support","summary":"allows operating as the Multipass service","slots":[{"snap":"core","slot":"multipass-support"}]},{"name":"netlink-audit","summary":"allows access to kernel audit system through netlink","slots":[{"snap":"core","slot":"netlink-audit"}]},{"name":"netlink-connector","summary":"allows communication through the kernel netlink connector","slots":[{"snap":"core","slot":"netlink-connector"}]},{"name":"netlink-driver","summary":"allows operating a kernel driver module exposing itself via a netlink protocol family"},{"name":"network","summary":"allows access to the network","plugs":[{"snap":"bitwarden","plug":"network"},{"snap":"bw","plug":"network"}],"slots":[{"snap":"core","slot":"network"}]},{"name":"network-bind","summary":"allows operating as a network service","plugs":[{"snap":"bw","plug":"network-bind"}],"slots":[{"snap":"core","slot":"network-bind"}]},{"name":"network-control","summary":"allows configuring networking and network namespaces","slots":[{"snap":"core","slot":"network-control"}]},{"name":"network-manager","summary":"allows operating as the NetworkManager service","slots":[{"snap":"core","slot":"network-manager"}]},{"name":"network-manager-observe","summary":"allows observing NetworkManager settings","slots":[{"snap":"core","slot":"network-manager-observe"}]},{"name":"network-observe","summary":"allows querying network status","slots":[{"snap":"core","slot":"network-observe"}]},{"name":"network-setup-control","summary":"allows access to netplan configuration","slots":[{"snap":"core","slot":"network-setup-control"}]},{"name":"network-setup-observe","summary":"allows read access to netplan configuration","slots":[{"snap":"core","slot":"network-setup-observe"}]},{"name":"network-status","summary":"allows access to network connectivity status","slots":[{"snap":"core","slot":"network-status"}]},{"name":"nvidia-drivers-support","summary":"NVIDIA drivers userspace system setup support","slots":[{"snap":"core","slot":"nvidia-drivers-support"}]},{"name":"ofono","summary":"allows operating as the ofono service","slots":[{"snap":"core","slot":"ofono"}]},{"name":"online-accounts-service","summary":"allows operating as the Online Accounts service"},{"name":"opengl","summary":"allows access to OpenGL stack","plugs":[{"snap":"bitwarden","plug":"opengl"}],"slots":[{"snap":"core","slot":"opengl"}]},{"name":"openvswitch","summary":"allows access to openvswitch management sockets","slots":[{"snap":"core","slot":"openvswitch"}]},{"name":"openvswitch-support","summary":"allows operating as the openvswitch service","slots":[{"snap":"core","slot":"openvswitch-support"}]},{"name":"optical-drive","summary":"allows access to optical drives","slots":[{"snap":"core","slot":"optical-drive"}]},{"name":"packagekit-control","summary":"allows control of the PackageKit service","slots":[{"snap":"core","slot":"packagekit-control"}]},{"name":"password-manager-service","summary":"allows access to common password manager services","plugs":[{"snap":"bitwarden","plug":"password-manager-service"}],"slots":[{"snap":"core","slot":"password-manager-service"}]},{"name":"pcscd","summary":"allows interacting with PCSD daemon\\n(e.g. for the PS/SC API library).","slots":[{"snap":"core","slot":"pcscd"}]},{"name":"personal-files","summary":"allows access to personal files or directories","slots":[{"snap":"core","slot":"personal-files"}]},{"name":"physical-memory-control","summary":"allows write access to all physical memory","slots":[{"snap":"core","slot":"physical-memory-control"}]},{"name":"physical-memory-observe","summary":"allows read access to all physical memory","slots":[{"snap":"core","slot":"physical-memory-observe"}]},{"name":"pkcs11","summary":"allows use of pkcs11 framework and access to exposed tokens"},{"name":"polkit","summary":"allows access to polkitd to check authorisation","slots":[{"snap":"core","slot":"polkit"}]},{"name":"polkit-agent","summary":"allows operation as a polkit agent"},{"name":"posix-mq","summary":"allows access to POSIX message queues"},{"name":"power-control","summary":"allows setting system power settings","slots":[{"snap":"core","slot":"power-control"}]},{"name":"ppp","summary":"allows operating as the ppp service","slots":[{"snap":"core","slot":"ppp"}]},{"name":"process-control","summary":"allows controlling other processes","slots":[{"snap":"core","slot":"process-control"}]},{"name":"ptp","summary":"allows access to the PTP Hardware Clock subsystem","slots":[{"snap":"core","slot":"ptp"}]},{"name":"pulseaudio","summary":"allows operating as or interacting with the pulseaudio service","plugs":[{"snap":"bitwarden","plug":"pulseaudio"}],"slots":[{"snap":"core","slot":"pulseaudio"}]},{"name":"pwm","summary":"allows access to specific PWM channel"},{"name":"qualcomm-ipc-router","summary":"allows access to the Qualcomm IPC Router sockets","slots":[{"snap":"core","slot":"qualcomm-ipc-router"}]},{"name":"raw-input","summary":"allows access to raw input devices","slots":[{"snap":"core","slot":"raw-input"}]},{"name":"raw-usb","summary":"allows raw access to all USB devices","slots":[{"snap":"core","slot":"raw-usb"}]},{"name":"raw-volume","summary":"allows read/write access to specific disk partition"},{"name":"removable-media","summary":"allows access to mounted removable storage","slots":[{"snap":"core","slot":"removable-media"}]},{"name":"screen-inhibit-control","summary":"allows inhibiting the screen saver","slots":[{"snap":"core","slot":"screen-inhibit-control"}]},{"name":"screencast-legacy","summary":"allows screen recording and audio recording, and also writing to arbitrary filesystem paths","slots":[{"snap":"core","slot":"screencast-legacy"}]},{"name":"scsi-generic","summary":"allows access to SCSI generic driver devices","slots":[{"snap":"core","slot":"scsi-generic"}]},{"name":"sd-control","summary":"allows controlling SD cards on certain boards","slots":[{"snap":"core","slot":"sd-control"}]},{"name":"serial-port","summary":"allows accessing a specific serial port"},{"name":"shared-memory","summary":"allows two snaps to use predefined shared memory objects","slots":[{"snap":"core","slot":"shared-memory"}]},{"name":"shutdown","summary":"allows shutting down or rebooting the system","slots":[{"snap":"core","slot":"shutdown"}]},{"name":"snap-refresh-control","summary":"allows extended control via snapctl over refreshes involving the snap","slots":[{"snap":"core","slot":"snap-refresh-control"}]},{"name":"snap-themes-control","summary":"allows use of snapd's theme installation API","slots":[{"snap":"core","slot":"snap-themes-control"}]},{"name":"snapd-control","summary":"allows communicating with snapd","slots":[{"snap":"core","slot":"snapd-control"}]},{"name":"spi","summary":"allows access to specific spi controller"},{"name":"ssh-keys","summary":"allows reading ssh user configuration and keys","slots":[{"snap":"core","slot":"ssh-keys"}]},{"name":"ssh-public-keys","summary":"allows reading ssh public keys and non-sensitive configuration","slots":[{"snap":"core","slot":"ssh-public-keys"}]},{"name":"steam-support","summary":"allow Steam to configure pressure-vessel containers","slots":[{"snap":"core","slot":"steam-support"}]},{"name":"storage-framework-service","summary":"allows operating as or interacting with the Storage Framework"},{"name":"system-backup","summary":"allows read-only access to the entire system for backups","slots":[{"snap":"core","slot":"system-backup"}]},{"name":"system-files","summary":"allows access to system files or directories","slots":[{"snap":"core","slot":"system-files"}]},{"name":"system-observe","summary":"allows observing all processes and drivers","slots":[{"snap":"core","slot":"system-observe"}]},{"name":"system-packages-doc","summary":"allows access to documentation of system packages","slots":[{"snap":"core","slot":"system-packages-doc"}]},{"name":"system-source-code","summary":"allows read-only access to /usr/src on the system","slots":[{"snap":"core","slot":"system-source-code"}]},{"name":"system-trace","summary":"allows using kernel tracing facilities","slots":[{"snap":"core","slot":"system-trace"}]},{"name":"tee","summary":"allows access to Trusted Execution Environment devices","slots":[{"snap":"core","slot":"tee"}]},{"name":"thumbnailer-service","summary":"allows operating as or interacting with the Thumbnailer service"},{"name":"time-control","summary":"allows setting system date and time","slots":[{"snap":"core","slot":"time-control"}]},{"name":"timeserver-control","summary":"allows setting system time synchronization servers","slots":[{"snap":"core","slot":"timeserver-control"}]},{"name":"timezone-control","summary":"allows setting system timezone","slots":[{"snap":"core","slot":"timezone-control"}]},{"name":"tpm","summary":"allows access to the Trusted Platform Module device","slots":[{"snap":"core","slot":"tpm"}]},{"name":"u2f-devices","summary":"allows access to u2f devices","slots":[{"snap":"core","slot":"u2f-devices"}]},{"name":"ubuntu-download-manager","summary":"allows operating as or interacting with the Ubuntu download manager"},{"name":"udisks2","summary":"allows operating as or interacting with the UDisks2 service","slots":[{"snap":"core","slot":"udisks2"}]},{"name":"uhid","summary":"allows control over UHID devices","slots":[{"snap":"core","slot":"uhid"}]},{"name":"uinput","summary":"allows access to the uinput device","slots":[{"snap":"core","slot":"uinput"}]},{"name":"uio","summary":"allows access to specific uio device"},{"name":"unity7","summary":"allows interacting with Unity 7 services","plugs":[{"snap":"bitwarden","plug":"unity7"}],"slots":[{"snap":"core","slot":"unity7"}]},{"name":"unity8","summary":"allows operating as or interacting with Unity 8"},{"name":"unity8-calendar","summary":"allows operating as or interacting with the Unity 8 Calendar Service"},{"name":"unity8-contacts","summary":"allows operating as or interacting with the Unity 8 Contacts Service"},{"name":"upower-observe","summary":"allows operating as or reading from the UPower service","slots":[{"snap":"core","slot":"upower-observe"}]},{"name":"userns","summary":"allows the ability to use user namespaces","slots":[{"snap":"core","slot":"userns"}]},{"name":"vcio","summary":"allows access to VideoCore I/O","slots":[{"snap":"core","slot":"vcio"}]},{"name":"wayland","summary":"allows access to compositors supporting wayland protocol","plugs":[{"snap":"bitwarden","plug":"wayland"}],"slots":[{"snap":"core","slot":"wayland"}]},{"name":"x11","summary":"allows interacting with or running as an X11 server","plugs":[{"snap":"bitwarden","plug":"x11"}],"slots":[{"snap":"core","slot":"x11"}]},{"name":"xilinx-dma","summary":"allows access to Xilinx DMA IP on a connected PCIe card","slots":[{"snap":"core","slot":"xilinx-dma"}]}]}"""


@pytest.fixture
def run_mock():
    def _run(*args, **kwargs):  # pylint: disable=unused-argument
        if kwargs.get("full"):
            if isinstance(run.return_value, dict):
                return run.return_value
            return {
                "stdout": (
                    run.return_value
                    if run.return_value is not None
                    else "potentially gar?bled output"
                ),
                "stderr": "",
                "retcode": 0,
            }
        return run.return_value if run.return_value is not None else "potentially gar?bled output"

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
def conn():
    _conn = Mock(spec=snap.SnapdApi)
    with patch("saltext.snap.modules.snap_mod._conn", return_value=_conn):
        yield _conn


@pytest.fixture
def sess(requests_available):
    _sess = Mock()
    if requests_available:
        ctx = patch("requests.Session", return_value=_sess)
    else:
        ctx = patch("saltext.snap.modules.snap_mod.SnapdConnection", return_value=_sess)
    with ctx:
        yield _sess


@pytest.fixture
def list_upgrades_mock(snap_refresh_list):
    with patch(
        "saltext.snap.modules.snap_mod.list_upgrades", autospec=True, return_value=snap_refresh_list
    ) as lst:
        yield lst


def test_ack(run_mock):
    res = snap.ack("/tmp/foo_28.assert")
    assert res is True
    run_mock.assert_called_once_with(["snap", "ack", "/tmp/foo_28.assert"])


@pytest.mark.parametrize("target", (None, "core", "core:network"))
@pytest.mark.parametrize("wait", (False, True))
def test_connect(run_mock, target, wait):
    res = snap.connect("foo", "network", target=target, wait=wait)
    assert res is True
    cmd = run_mock.call_args[0][0]
    assert cmd[:2] == ["snap", "connect"]
    assert "foo:network" in cmd
    assert (target in cmd) is bool(target)
    assert ("--no-wait" in cmd) is not wait


@pytest.mark.parametrize("target", (None, "core:network"))
@pytest.mark.parametrize("wait", (False, True))
@pytest.mark.parametrize("forget", (False, True))
def test_disconnect(run_mock, target, wait, forget):
    res = snap.disconnect("foo", "network", target=target, wait=wait, forget=forget)
    assert res is True
    cmd = run_mock.call_args[0][0]
    assert cmd[:2] == ["snap", "disconnect"]
    assert "foo:network" in cmd
    assert (target in cmd) is bool(target)
    assert ("--no-wait" in cmd) is not wait
    assert ("--forget" in cmd) is forget


@pytest.mark.usefixtures("requests_available")
@pytest.mark.parametrize("requests_available", (True, None), indirect=True)
def test_connections(sess, snap_connections_out, snap_connections, requests_available):
    if requests_available is None:
        sess.getresponse.return_value.read.return_value = snap_connections_out
        expected = "/v2/connections?"
    else:
        sess.request.return_value.json.return_value = json.loads(snap_connections_out)
        expected = "http://snapd/v2/connections?"
    res = snap.connections()
    url = sess.request.call_args[0][1]
    assert url.startswith(expected)
    assert "attrs=true" in url
    assert res == snap_connections


@pytest.mark.usefixtures("requests_available")
@pytest.mark.parametrize("requests_available", (True,), indirect=True)
def test_connections_all(sess, snap_connections_all_out, snap_connections_all):
    sess.request.return_value.json.return_value = json.loads(snap_connections_all_out)
    res = snap.connections(all=True)
    url = sess.request.call_args[0][1]
    assert url.startswith("http://snapd/v2/connections?")
    assert "attrs=true" in url
    assert "select=all" in url
    assert res == snap_connections_all


@pytest.mark.usefixtures("requests_available")
@pytest.mark.parametrize("requests_available", (True,), indirect=True)
def test_connections_name(sess, snap_connections_name_out, snap_connections_name):
    sess.request.return_value.json.return_value = json.loads(snap_connections_name_out)
    res = snap.connections(name="bitwarden")
    url = sess.request.call_args[0][1]
    assert url.startswith("http://snapd/v2/connections?")
    assert "attrs=true" in url
    assert "snap=bitwarden" in url
    assert res == snap_connections_name


@pytest.mark.usefixtures("requests_available")
@pytest.mark.parametrize("requests_available", (True,), indirect=True)
def test_connections_interface(sess, snap_connections_interface_out, snap_connections_interface):
    sess.request.return_value.json.return_value = json.loads(snap_connections_interface_out)
    res = snap.connections(interface="network")
    url = sess.request.call_args[0][1]
    assert url.startswith("http://snapd/v2/connections?")
    assert "attrs=true" in url
    assert "interface=network" in url
    assert res == snap_connections_interface


@pytest.mark.usefixtures("requests_available")
@pytest.mark.parametrize("requests_available", (True,), indirect=True)
def test_connections_interface_name(
    sess, snap_connections_interface_name_out, snap_connections_interface_name
):
    sess.request.return_value.json.return_value = json.loads(snap_connections_interface_name_out)
    res = snap.connections(name="bitwarden", interface="network")
    url = sess.request.call_args[0][1]
    assert url.startswith("http://snapd/v2/connections?")
    assert "attrs=true" in url
    assert "interface=network" in url
    assert "snap=bitwarden" in url
    assert res == snap_connections_interface_name


@pytest.mark.parametrize("func", ("enable", "disable"))
def test_en_dis_able(run_mock, func):
    res = getattr(snap, func)("foo")
    assert res is True
    run_mock.assert_called_once_with(["snap", func, "foo"])


@pytest.mark.parametrize("func", ("hold", "unhold"))
def test_un_hold(run_mock, func):
    res = getattr(snap, func)("foo")
    assert res is True
    run_mock.assert_called_once_with(["snap", "refresh", f"--{func}", "foo"])


def test_hold_with_duration(run_mock):
    res = snap.hold("foo", duration="10s")
    assert res is True
    run_mock.assert_called_once_with(["snap", "refresh", "--hold=10s", "foo"])


@pytest.mark.parametrize("verbose", (False, True))
def test_info(
    verbose, run_mock, snap_info_out, snap_info_verbose_out, snap_info, snap_info_verbose
):
    run_mock.side_effect = lambda c, **_: (
        snap_info_verbose_out if "--verbose" in c else snap_info_out
    )
    res = snap.info("hello-world", verbose=verbose)
    if verbose:
        assert res == snap_info_verbose
    else:
        assert res == snap_info
    cmd = run_mock.call_args[0][0]
    assert ("--verbose" in cmd) is verbose
    assert cmd[:4] == ["snap", "info", "--unicode=never", "--color=never"]
    assert cmd[-1] == "hello-world"


def test_info_multi(run_mock, snap_info_multi_out, caplog):
    tgts = ["hello-world", "core", "foobar"]
    run_mock.return_value = snap_info_multi_out
    with caplog.at_level(logging.WARNING):
        res = snap.info(tgts)
    assert len(res) == len(tgts)
    for tgt in tgts:
        assert tgt in res
        if tgt != "foobar":
            assert res[tgt]["name"] == tgt
        else:
            assert not res[tgt]
    assert 'no snap found for "foobar"' in caplog.text


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


@pytest.mark.usefixtures("run_mock")
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
def test_install_channel_validation(channel, err):
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


@pytest.mark.usefixtures("requests_available")
@pytest.mark.parametrize("requests_available", (True,), indirect=True)
def test_interfaces(sess, snap_interfaces_out, snap_interfaces):
    sess.request.return_value.json.return_value = json.loads(snap_interfaces_out)
    res = snap.interfaces()
    url = sess.request.call_args[0][1]
    assert url.startswith("http://snapd/v2/interfaces?")
    assert "plugs=true" in url
    assert "slots=true" in url
    assert "select=connected" in url
    assert res == snap_interfaces


@pytest.mark.usefixtures("requests_available")
@pytest.mark.parametrize("requests_available", (True, None), indirect=True)
def test_interfaces_all(sess, snap_interfaces_all_out, snap_interfaces_all, requests_available):
    if requests_available is None:
        sess.getresponse.return_value.read.return_value = snap_interfaces_all_out
        expected = "/v2/interfaces?"
    else:
        sess.request.return_value.json.return_value = json.loads(snap_interfaces_all_out)
        expected = "http://snapd/v2/interfaces?"
    res = snap.interfaces(all=True)
    url = sess.request.call_args[0][1]
    assert url.startswith(expected)
    assert "plugs=true" in url
    assert "slots=true" in url
    assert "select=all" in url
    assert res == snap_interfaces_all


@pytest.mark.usefixtures("requests_available")
@pytest.mark.parametrize("requests_available", (True,), indirect=True)
@pytest.mark.parametrize("names", ("x11", ["x11", "xilinx-dma"]))
def test_interfaces_name_all(names, sess, snap_interfaces_all_out, snap_interfaces_all):
    names_list = names
    if isinstance(names, str):
        names_list = [names]
    resp = json.loads(snap_interfaces_all_out)
    resp["result"] = [x for x in resp["result"] if x["name"] in names_list]
    exp = {k: v for k, v in snap_interfaces_all.items() if k in names_list}
    if isinstance(names, str):
        exp = exp[next(iter(exp))]
    sess.request.return_value.json.return_value = resp
    res = snap.interfaces(names, all=True)
    url = sess.request.call_args[0][1]
    assert url.startswith("http://snapd/v2/interfaces?")
    assert "plugs=true" in url
    assert "slots=true" in url
    assert "select=all" in url
    assert f"names={'%2C'.join(names_list)}" in url
    assert res == exp


@pytest.mark.usefixtures("list_mock")
@pytest.mark.parametrize("name,expected", (("hello-world", True), ("core18", False)))
def test_is_enabled(name, expected):
    assert snap.is_enabled(name) is expected


@pytest.mark.usefixtures("list_mock")
@pytest.mark.parametrize("name,expected", (("hello-world", True), ("yubioath-desktop", False)))
def test_is_held(name, expected):
    assert snap.is_held(name) is expected


@pytest.mark.usefixtures("cmd_run_list_err")
@pytest.mark.parametrize("func", ("is_enabled", "is_uptodate", "is_held"))
def test_status_checks_not_installed(func):
    with pytest.raises(CommandExecutionError, match="is not installed"):
        getattr(snap, func)("foo")


@pytest.mark.parametrize("requests_available", (False, True), indirect=True)
@pytest.mark.parametrize("name,expected", (("hello-world", True), ("foobar", False)))
def test_is_installed(
    name, expected, snap_list_out, snap_list_api_out, cmd_run, sess, requests_available
):
    if requests_available:
        sess.request.return_value.json.return_value = (
            json.loads(snap_list_api_out)
            if expected
            else {
                "type": "sync",
                "status-code": 200,
                "status": "OK",
                "result": [],
                "sources": ["local"],
            }
        )
    else:
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


@pytest.mark.parametrize("headers", (None, {"authority-id": "canonical"}))
def test_known(cmd_run, headers, snap_known_out, snap_known):
    cmd_run.return_value = snap_known_out
    assert snap.known("snap-revision", **(headers or {})) == snap_known
    cmd = cmd_run.call_args[0][0]
    exp = "snap known snap-revision"
    if headers:
        exp += " authority-id=canonical"
    assert cmd == exp


def test_known_empty(cmd_run):
    """
    Ensure that the empty document is not YAML-parsed as None and appended
    """
    cmd_run.return_value = ""
    assert not snap.known("snap-revision")


def test_list_cli(cmd_run, snap_list_out, snap_list):
    cmd_run.return_value = snap_list_out
    assert snap.list_() == snap_list


def test_list_cli_revisions(cmd_run, snap_list_revisions_out, snap_list):
    cmd_run.return_value = snap_list_revisions_out
    res = snap.list_(revisions=True)
    assert set(res) == set(snap_list)
    for snp, data in res.items():
        if snp == "yubioath-desktop":
            continue
        assert data == [snap_list[snp]]
    assert len(res["yubioath-desktop"]) == 3
    revisions = set()
    for snp in res["yubioath-desktop"]:
        assert set(snp) == set(snap_list["yubioath-desktop"])
        revisions.add(snp["revision"])
    assert revisions == {"10", "11", "12"}


@pytest.mark.usefixtures("requests_available")
@pytest.mark.parametrize("requests_available", (True,), indirect=True)
def test_list_api(sess, snap_list_api_out, snap_list):
    sess.request.return_value.json.return_value = json.loads(snap_list_api_out)
    assert snap.list_() == snap_list


@pytest.mark.usefixtures("requests_available")
@pytest.mark.parametrize("requests_available", (True,), indirect=True)
def test_list_api_revisions(sess, snap_list_api_revisions_out, snap_list):
    sess.request.return_value.json.return_value = json.loads(snap_list_api_revisions_out)
    res = snap.list_(revisions=True)
    assert set(res) == set(snap_list)
    for snp, data in res.items():
        if snp == "yubioath-desktop":
            continue
        assert data == [snap_list[snp]]
    assert len(res["yubioath-desktop"]) == 3
    revisions = set()
    for snp in res["yubioath-desktop"]:
        assert set(snp) == set(snap_list["yubioath-desktop"])
        revisions.add(snp["revision"])
    assert revisions == {"10", "11", "12"}


@pytest.mark.usefixtures("list_mock")
@pytest.mark.parametrize("exclude_held", (False, True))
def test_list_upgrades(cmd_run, exclude_held, snap_refresh_list_out, snap_refresh_list, snap_list):
    cmd_run.return_value = snap_refresh_list_out
    if exclude_held:
        snap_refresh_list = {
            name: data for name, data in snap_refresh_list.items() if not snap_list[name]["held"]
        }
    assert snap.list_upgrades(exclude_held=exclude_held) == snap_refresh_list


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


@pytest.mark.usefixtures("requests_available")
@pytest.mark.parametrize("requests_available", (True,), indirect=True)
@pytest.mark.parametrize("connected", (None, False, True))
@pytest.mark.parametrize("interface", (None, "password-manager-service"))
@pytest.mark.parametrize("plug", (None, "password-manager-service"))
def test_plugs(connected, interface, plug, sess, snap_connections_all_out, snap_plugs):
    sess.request.return_value.json.return_value = json.loads(snap_connections_all_out)
    res = snap.plugs("bitwarden", plug=plug, interface=interface, connected=connected)
    exp = snap_plugs
    if connected is not None:
        exp = {k: v for k, v in exp.items() if bool(v.get("connections")) is connected}
    if interface is not None:
        exp = {k: v for k, v in exp.items() if v["interface"] == interface}
    if plug is not None:
        exp = {k: v for k, v in exp.items() if k == plug}
    assert res == exp


@pytest.mark.usefixtures("requests_available")
@pytest.mark.parametrize("requests_available", (True,), indirect=True)
@pytest.mark.parametrize("connected", (None, False, True))
@pytest.mark.parametrize("interface", (None, "network"))
@pytest.mark.parametrize("slot", (None, "network"))
def test_slots(connected, interface, slot, sess, snap_connections_all_out, snap_slots):
    sess.request.return_value.json.return_value = json.loads(snap_connections_all_out)
    res = snap.slots("core", slot=slot, interface=interface, connected=connected)
    exp = snap_slots
    if connected is not None:
        exp = {k: v for k, v in exp.items() if bool(v.get("connections")) is connected}
    if interface is not None:
        exp = {k: v for k, v in exp.items() if v["interface"] == interface}
    if slot is not None:
        exp = {k: v for k, v in exp.items() if k == slot}
    assert res == exp


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
def test_services_filtering(name, snp, expected, run_mock, snap_services_out):
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
def test_service_status_missing_service(func):
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
