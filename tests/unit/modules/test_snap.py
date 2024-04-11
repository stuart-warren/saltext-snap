import contextlib
import json
import logging
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


@pytest.fixture(params=(False,), autouse=True)
def requests_available(request):
    with patch("saltext.snap.modules.snap_mod.HAS_REQUESTS", request.param):
        yield request.param


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
    # the testapp will fail to parse
    return dedent(
        """
            Name               Version                     Rev    Tracking       Publisher          Notes
            bare               1.0                         5      latest/stable  canonical**        base
            core               16-2.61.2                   16928  latest/stable  canonical**        core
            core18             20231027                    2812   latest/stable  canonical**        base,disabled
            gnome-3-28-1804    3.28.0-19-g98f9e67.98f9e67  198    latest/stable  canonical**        -
            gtk-common-themes  0.1-81-g442e511             1535   latest/stable  canonical**        disabled
            hello-world        6.3                         28     latest/stable  canonical**        -
            yubioath-desktop   5.0.5                       12     latest/stable  yubico-snap-store  -
            testapp            1.0                         x2                                       try
        """
    ).strip()


@pytest.fixture
def snap_list_revisions_out():
    return dedent(
        """
            Name               Version                     Rev    Tracking       Publisher          Notes
            bare               1.0                         5      latest/stable  canonical**        base
            core               16-2.61.2                   16928  latest/stable  canonical**        core
            core18             20231027                    2812   latest/stable  canonical**        base,disabled
            gnome-3-28-1804    3.28.0-19-g98f9e67.98f9e67  198    latest/stable  canonical**        -
            gtk-common-themes  0.1-81-g442e511             1535   latest/stable  canonical**        disabled
            hello-world        6.3                         28     latest/stable  canonical**        -
            yubioath-desktop   5.0.5                       12     latest/stable  yubico-snap-store  -
            yubioath-desktop   5.0.4                       11     latest/stable  yubico-snap-store  disabled
            yubioath-desktop   5.0.3                       10     latest/stable  yubico-snap-store  disabled
        """
    ).strip()


@pytest.fixture
def snap_list_api_out():
    return '{"type":"sync","status-code":200,"status":"OK","result":[{"id":"jZLfBRzf1cYlYysIjD2bwSzNtngY0qit","title":"GTK Common Themes","summary":"All the (common) themes","description":"A snap that exports the GTK and icon themes used on various Linux distros.","installed-size":96141312,"name":"gtk-common-themes","publisher":{"id":"canonical","username":"canonical","display-name":"Canonical","validation":"verified"},"developer":"canonical","status":"installed","type":"app","base":"bare","version":"0.1-81-g442e511","channel":"stable","tracking-channel":"latest/stable","ignore-validation":false,"revision":"1535","confinement":"strict","private":false,"devmode":false,"jailmode":false,"mounted-from":"/var/lib/snapd/snaps/gtk-common-themes_1535.snap","links":{"contact":["https://gitlab.gnome.org/Community/Ubuntu/gtk-common-themes/issues"]},"contact":"https://gitlab.gnome.org/Community/Ubuntu/gtk-common-themes/issues"},{"id":"buPKUD3TKqCOgLEjjHx5kSiCpIs5cMuQ","title":"Hello World","summary":"The \'hello-world\' of snaps","description":"This is a simple hello world example.","icon":"/v2/icons/hello-world/icon","installed-size":20480,"install-date":"2024-04-11T12:15:56.850202878+00:00","name":"hello-world","publisher":{"id":"canonical","username":"canonical","display-name":"Canonical","validation":"verified"},"developer":"canonical","status":"active","type":"app","version":"6.3","channel":"","tracking-channel":"latest/stable","ignore-validation":false,"revision":"28","confinement":"strict","private":false,"devmode":false,"jailmode":false,"apps":[{"snap":"hello-world","name":"env"},{"snap":"hello-world","name":"evil"},{"snap":"hello-world","name":"hello-world"},{"snap":"hello-world","name":"sh"}],"mounted-from":"/var/lib/snapd/snaps/hello-world_28.snap","links":{"contact":["mailto:snaps@canonical.com"]},"contact":"mailto:snaps@canonical.com","media":[{"type":"icon","url":"https://dashboard.snapcraft.io/site_media/appmedia/2015/03/hello.svg_NZLfWbh.png","width":256,"height":256},{"type":"screenshot","url":"https://dashboard.snapcraft.io/site_media/appmedia/2018/06/Screenshot_from_2018-06-14_09-33-31.png","width":199,"height":118},{"type":"video","url":"https://vimeo.com/194577403"}]},{"id":"osRLU2WSwcWCNSMFOgqpQoE6NPnD7r31","title":"Yubico Authenticator","summary":"2FA with YubiKey","description":"Store your unique credential on a hardware-backed security key and take it wherever you go from mobile to desktop. No more storing sensitive secrets on your mobile phone, leaving your account vulnerable to takeovers. With the Yubico Authenticator you can raise the bar for security.\\n\\nThe Yubico Authenticator generates a one time code used to verify your identity as you’re logging into various services. No connectivity needed! This is based on Open Authentication (OATH) time-based TOTP and event-based HOTP one-time password codes.\\n\\nSetting up the Yubico Authenticator desktop app is easy. Simply download and open the app, insert your YubiKey, and begin adding the accounts you wish to protect by using the QR code provided by each service.\\n\\nExperience security the modern way with the Yubico Authenticator. Visit yubico.com to learn more about the YubiKey and security solutions for mobile.\\n\\nFeatures on desktop include:\\n- Touch Authentication - Touch the YubiKey 5 Series security key to store your credential on the YubiKey\\n- Biometric Authentication - Manage PINs and fingerprints on your FIDO-enabled YubiKeys, as well as add, delete and rename fingerprints on your Yubikey Bio Series keys.\\n- Easy Setup - QR codes available from the services you wish to protect with strong authentication\\n- User Presence - New codes generated with just a touch of the YubiKey\\n- Compatible - Secure all the services currently compatible with other Authenticator apps\\n- Secure - Hardware-backed strong two-factor authentication with secret stored on the YubiKey, not on the desktop\\n- Versatile - Support for multiple work and personal accounts\\n- Portable - Get the same set of codes across our other Yubico Authenticator apps for desktops as well as for all leading mobile platforms\\n- Flexible - Support for time-based and counter-based code generation\\n\\n---\\n\\nThis snap bundles its own version of the pcscd daemon, and is not compatible with running a system-wide version of pcscd.\\n\\nTo stop the system-wide pcscd:\\n\\n   sudo systemctl stop pcscd\\n   sudo systemctl stop pcscd.socket\\n\\nTo restart the bundled pcscd:\\n\\n   sudo snap restart yubioath-desktop.pcscd","icon":"/v2/icons/yubioath-desktop/icon","installed-size":227135488,"install-date":"2024-04-11T12:15:23.66083664+00:00","name":"yubioath-desktop","publisher":{"id":"o2S2GYSCBxilwi1OFNftYfLhm2l3aEzI","username":"yubico-snap-store","display-name":"Yubico","validation":"unproven"},"developer":"yubico-snap-store","status":"active","type":"app","base":"core18","version":"5.0.5","channel":"","tracking-channel":"latest/stable","ignore-validation":false,"revision":"12","confinement":"strict","private":false,"devmode":false,"jailmode":false,"apps":[{"snap":"yubioath-desktop","name":"pcscd","daemon":"simple","daemon-scope":"system","enabled":true,"active":true,"common-id":"com.yubico.pcscd"},{"snap":"yubioath-desktop","name":"yubioath-desktop","desktop-file":"/var/lib/snapd/desktop/applications/yubioath-desktop_yubioath-desktop.desktop","common-id":"com.yubico.yubioath"}],"common-ids":["com.yubico.pcscd","com.yubico.yubioath"],"mounted-from":"/var/lib/snapd/snaps/yubioath-desktop_12.snap","links":{"contact":["https://support.yubico.com/support/tickets/new"],"website":["https://developers.yubico.com/yubioath-desktop"]},"contact":"https://support.yubico.com/support/tickets/new","website":"https://developers.yubico.com/yubioath-desktop","media":[{"type":"icon","url":"https://dashboard.snapcraft.io/site_media/appmedia/2020/05/com.yubico.yubioath.svg.png","width":512,"height":512},{"type":"screenshot","url":"https://dashboard.snapcraft.io/site_media/appmedia/2021/10/Linux-12x-100.jpg","width":2881,"height":1801},{"type":"screenshot","url":"https://dashboard.snapcraft.io/site_media/appmedia/2021/10/Linux-22x-100.jpg","width":2881,"height":1801},{"type":"screenshot","url":"https://dashboard.snapcraft.io/site_media/appmedia/2021/10/Linux-32x-100_1.jpg","width":2881,"height":1801},{"type":"screenshot","url":"https://dashboard.snapcraft.io/site_media/appmedia/2021/10/Linux-42x-100.jpg","width":2881,"height":1801}]},{"id":"EISPgh06mRh1vordZY9OZ34QHdd7OrdR","title":"bare","summary":"Empty base snap, useful for testing and fully statically linked snaps","description":"","installed-size":4096,"install-date":"2024-04-11T01:50:47.869171361+00:00","name":"bare","publisher":{"id":"canonical","username":"canonical","display-name":"Canonical","validation":"verified"},"developer":"canonical","status":"active","type":"base","version":"1.0","channel":"stable","tracking-channel":"latest/stable","ignore-validation":false,"revision":"5","confinement":"strict","private":false,"devmode":false,"jailmode":false,"mounted-from":"/var/lib/snapd/snaps/bare_5.snap","links":{"contact":["mailto:snaps@canonical.com"]},"contact":"mailto:snaps@canonical.com"},{"id":"99T7MUlRhtI3U0QFgl5mXXESAiSwt776","title":"core","summary":"snapd runtime environment","description":"The core runtime environment for snapd","installed-size":109043712,"install-date":"2024-04-11T01:42:05.749062355+00:00","name":"core","publisher":{"id":"canonical","username":"canonical","display-name":"Canonical","validation":"verified"},"developer":"canonical","status":"active","type":"os","version":"16-2.61.2","channel":"stable","tracking-channel":"latest/stable","ignore-validation":false,"revision":"16928","confinement":"strict","private":false,"devmode":false,"jailmode":false,"mounted-from":"/var/lib/snapd/snaps/core_16928.snap","links":{"contact":["mailto:snaps@canonical.com"],"website":["https://snapcraft.io"]},"contact":"mailto:snaps@canonical.com","website":"https://snapcraft.io"},{"id":"CSO04Jhav2yK0uz97cr0ipQRyqg0qQL6","title":"Core 18","summary":"Runtime environment based on Ubuntu 18.04","description":"The base snap based on the Ubuntu 18.04 release.","installed-size":58363904,"name":"core18","publisher":{"id":"canonical","username":"canonical","display-name":"Canonical","validation":"verified"},"developer":"canonical","status":"installed","type":"base","version":"20231027","channel":"stable","tracking-channel":"latest/stable","ignore-validation":false,"revision":"2812","confinement":"strict","private":false,"devmode":false,"jailmode":false,"mounted-from":"/var/lib/snapd/snaps/core18_2812.snap","links":{"contact":["https://github.com/snapcore/core18/issues"],"website":["https://snapcraft.io"]},"contact":"https://github.com/snapcore/core18/issues","website":"https://snapcraft.io"},{"id":"TKv5Fm000l4XiUYJW9pjWHLkCPlDbIg1","title":"GNOME 3.28 runtime","summary":"Shared GNOME 3.28 runtime for Ubuntu 18.04","description":"This snap includes a GNOME 3.28 stack (the base libraries and desktop \\nintegration components) and shares it through the content interface.","icon":"/v2/icons/gnome-3-28-1804/icon","installed-size":172830720,"install-date":"2024-04-11T01:51:22.822580656+00:00","name":"gnome-3-28-1804","publisher":{"id":"canonical","username":"canonical","display-name":"Canonical","validation":"verified"},"developer":"canonical","status":"active","type":"app","base":"core18","version":"3.28.0-19-g98f9e67.98f9e67","channel":"stable","tracking-channel":"latest/stable","ignore-validation":false,"revision":"198","confinement":"strict","private":false,"devmode":false,"jailmode":false,"mounted-from":"/var/lib/snapd/snaps/gnome-3-28-1804_198.snap","links":{"contact":["https://gitlab.gnome.org/Community/Ubuntu/gnome-3-28-1804/issues"]},"contact":"https://gitlab.gnome.org/Community/Ubuntu/gnome-3-28-1804/issues","media":[{"type":"icon","url":"https://dashboard.snapcraft.io/site_media/appmedia/2018/04/icon_ysMJicB.png","width":256,"height":256}]}],"sources":["local"]}'


@pytest.fixture
def snap_list_api_revisions_out():
    return '{"type":"sync","status-code":200,"status":"OK","result":[{"id":"jZLfBRzf1cYlYysIjD2bwSzNtngY0qit","title":"GTK Common Themes","summary":"All the (common) themes","description":"A snap that exports the GTK and icon themes used on various Linux distros.","installed-size":96141312,"name":"gtk-common-themes","publisher":{"id":"canonical","username":"canonical","display-name":"Canonical","validation":"verified"},"developer":"canonical","status":"installed","type":"app","base":"bare","version":"0.1-81-g442e511","channel":"stable","tracking-channel":"latest/stable","ignore-validation":false,"revision":"1535","confinement":"strict","private":false,"devmode":false,"jailmode":false,"mounted-from":"/var/lib/snapd/snaps/gtk-common-themes_1535.snap","links":{"contact":["https://gitlab.gnome.org/Community/Ubuntu/gtk-common-themes/issues"]},"contact":"https://gitlab.gnome.org/Community/Ubuntu/gtk-common-themes/issues"},{"id":"buPKUD3TKqCOgLEjjHx5kSiCpIs5cMuQ","title":"Hello World","summary":"The \'hello-world\' of snaps","description":"This is a simple hello world example.","icon":"/v2/icons/hello-world/icon","installed-size":20480,"install-date":"2024-04-11T12:15:56.850202878+00:00","name":"hello-world","publisher":{"id":"canonical","username":"canonical","display-name":"Canonical","validation":"verified"},"developer":"canonical","status":"active","type":"app","version":"6.3","channel":"","tracking-channel":"latest/stable","ignore-validation":false,"revision":"28","confinement":"strict","private":false,"devmode":false,"jailmode":false,"apps":[{"snap":"hello-world","name":"env"},{"snap":"hello-world","name":"evil"},{"snap":"hello-world","name":"hello-world"},{"snap":"hello-world","name":"sh"}],"mounted-from":"/var/lib/snapd/snaps/hello-world_28.snap","links":{"contact":["mailto:snaps@canonical.com"]},"contact":"mailto:snaps@canonical.com","media":[{"type":"icon","url":"https://dashboard.snapcraft.io/site_media/appmedia/2015/03/hello.svg_NZLfWbh.png","width":256,"height":256},{"type":"screenshot","url":"https://dashboard.snapcraft.io/site_media/appmedia/2018/06/Screenshot_from_2018-06-14_09-33-31.png","width":199,"height":118},{"type":"video","url":"https://vimeo.com/194577403"}]},{"id":"osRLU2WSwcWCNSMFOgqpQoE6NPnD7r31","title":"Yubico Authenticator","summary":"2FA with YubiKey","description":"description_too_long \\n hi there","icon":"/v2/icons/yubioath-desktop/icon","installed-size":227135488,"install-date":"2024-04-11T12:15:23.66083664+00:00","name":"yubioath-desktop","publisher":{"id":"o2S2GYSCBxilwi1OFNftYfLhm2l3aEzI","username":"yubico-snap-store","display-name":"Yubico","validation":"unproven"},"developer":"yubico-snap-store","status":"active","type":"app","base":"core18","version":"5.0.5","channel":"","tracking-channel":"latest/stable","ignore-validation":false,"revision":"12","confinement":"strict","private":false,"devmode":false,"jailmode":false,"apps":[{"snap":"yubioath-desktop","name":"pcscd","daemon":"simple","daemon-scope":"system","enabled":true,"active":true,"common-id":"com.yubico.pcscd"},{"snap":"yubioath-desktop","name":"yubioath-desktop","desktop-file":"/var/lib/snapd/desktop/applications/yubioath-desktop_yubioath-desktop.desktop","common-id":"com.yubico.yubioath"}],"common-ids":["com.yubico.pcscd","com.yubico.yubioath"],"mounted-from":"/var/lib/snapd/snaps/yubioath-desktop_12.snap","links":{"contact":["https://support.yubico.com/support/tickets/new"],"website":["https://developers.yubico.com/yubioath-desktop"]},"contact":"https://support.yubico.com/support/tickets/new","website":"https://developers.yubico.com/yubioath-desktop","media":[{"type":"icon","url":"https://dashboard.snapcraft.io/site_media/appmedia/2020/05/com.yubico.yubioath.svg.png","width":512,"height":512},{"type":"screenshot","url":"https://dashboard.snapcraft.io/site_media/appmedia/2021/10/Linux-12x-100.jpg","width":2881,"height":1801},{"type":"screenshot","url":"https://dashboard.snapcraft.io/site_media/appmedia/2021/10/Linux-22x-100.jpg","width":2881,"height":1801},{"type":"screenshot","url":"https://dashboard.snapcraft.io/site_media/appmedia/2021/10/Linux-32x-100_1.jpg","width":2881,"height":1801},{"type":"screenshot","url":"https://dashboard.snapcraft.io/site_media/appmedia/2021/10/Linux-42x-100.jpg","width":2881,"height":1801}]},{"id":"osRLU2WSwcWCNSMFOgqpQoE6NPnD7r31","title":"Yubico Authenticator","summary":"2FA with YubiKey","description":"description_too_long \\n hi there","icon":"/v2/icons/yubioath-desktop/icon","installed-size":225135488,"install-date":"2024-03-11T12:15:23.66083664+00:00","name":"yubioath-desktop","publisher":{"id":"o2S2GYSCBxilwi1OFNftYfLhm2l3aEzI","username":"yubico-snap-store","display-name":"Yubico","validation":"unproven"},"developer":"yubico-snap-store","status":"active","type":"app","base":"core18","version":"5.0.4","channel":"","tracking-channel":"latest/stable","ignore-validation":false,"revision":"11","confinement":"strict","private":false,"devmode":false,"jailmode":false,"apps":[{"snap":"yubioath-desktop","name":"pcscd","daemon":"simple","daemon-scope":"system","enabled":true,"active":true,"common-id":"com.yubico.pcscd"},{"snap":"yubioath-desktop","name":"yubioath-desktop","desktop-file":"/var/lib/snapd/desktop/applications/yubioath-desktop_yubioath-desktop.desktop","common-id":"com.yubico.yubioath"}],"common-ids":["com.yubico.pcscd","com.yubico.yubioath"],"mounted-from":"/var/lib/snapd/snaps/yubioath-desktop_12.snap","links":{"contact":["https://support.yubico.com/support/tickets/new"],"website":["https://developers.yubico.com/yubioath-desktop"]},"contact":"https://support.yubico.com/support/tickets/new","website":"https://developers.yubico.com/yubioath-desktop","media":[{"type":"icon","url":"https://dashboard.snapcraft.io/site_media/appmedia/2020/05/com.yubico.yubioath.svg.png","width":512,"height":512},{"type":"screenshot","url":"https://dashboard.snapcraft.io/site_media/appmedia/2021/10/Linux-12x-100.jpg","width":2881,"height":1801},{"type":"screenshot","url":"https://dashboard.snapcraft.io/site_media/appmedia/2021/10/Linux-22x-100.jpg","width":2881,"height":1801},{"type":"screenshot","url":"https://dashboard.snapcraft.io/site_media/appmedia/2021/10/Linux-32x-100_1.jpg","width":2881,"height":1801},{"type":"screenshot","url":"https://dashboard.snapcraft.io/site_media/appmedia/2021/10/Linux-42x-100.jpg","width":2881,"height":1801}]},{"id":"osRLU2WSwcWCNSMFOgqpQoE6NPnD7r31","title":"Yubico Authenticator","summary":"2FA with YubiKey","description":"description_too_long \\n hi there","icon":"/v2/icons/yubioath-desktop/icon","installed-size":223135488,"install-date":"2024-02-11T12:15:23.66083664+00:00","name":"yubioath-desktop","publisher":{"id":"o2S2GYSCBxilwi1OFNftYfLhm2l3aEzI","username":"yubico-snap-store","display-name":"Yubico","validation":"unproven"},"developer":"yubico-snap-store","status":"active","type":"app","base":"core18","version":"5.0.3","channel":"","tracking-channel":"latest/stable","ignore-validation":false,"revision":"10","confinement":"strict","private":false,"devmode":false,"jailmode":false,"apps":[{"snap":"yubioath-desktop","name":"pcscd","daemon":"simple","daemon-scope":"system","enabled":true,"active":true,"common-id":"com.yubico.pcscd"},{"snap":"yubioath-desktop","name":"yubioath-desktop","desktop-file":"/var/lib/snapd/desktop/applications/yubioath-desktop_yubioath-desktop.desktop","common-id":"com.yubico.yubioath"}],"common-ids":["com.yubico.pcscd","com.yubico.yubioath"],"mounted-from":"/var/lib/snapd/snaps/yubioath-desktop_12.snap","links":{"contact":["https://support.yubico.com/support/tickets/new"],"website":["https://developers.yubico.com/yubioath-desktop"]},"contact":"https://support.yubico.com/support/tickets/new","website":"https://developers.yubico.com/yubioath-desktop","media":[{"type":"icon","url":"https://dashboard.snapcraft.io/site_media/appmedia/2020/05/com.yubico.yubioath.svg.png","width":512,"height":512},{"type":"screenshot","url":"https://dashboard.snapcraft.io/site_media/appmedia/2021/10/Linux-12x-100.jpg","width":2881,"height":1801},{"type":"screenshot","url":"https://dashboard.snapcraft.io/site_media/appmedia/2021/10/Linux-22x-100.jpg","width":2881,"height":1801},{"type":"screenshot","url":"https://dashboard.snapcraft.io/site_media/appmedia/2021/10/Linux-32x-100_1.jpg","width":2881,"height":1801},{"type":"screenshot","url":"https://dashboard.snapcraft.io/site_media/appmedia/2021/10/Linux-42x-100.jpg","width":2881,"height":1801}]},{"id":"EISPgh06mRh1vordZY9OZ34QHdd7OrdR","title":"bare","summary":"Empty base snap, useful for testing and fully statically linked snaps","description":"","installed-size":4096,"install-date":"2024-04-11T01:50:47.869171361+00:00","name":"bare","publisher":{"id":"canonical","username":"canonical","display-name":"Canonical","validation":"verified"},"developer":"canonical","status":"active","type":"base","version":"1.0","channel":"stable","tracking-channel":"latest/stable","ignore-validation":false,"revision":"5","confinement":"strict","private":false,"devmode":false,"jailmode":false,"mounted-from":"/var/lib/snapd/snaps/bare_5.snap","links":{"contact":["mailto:snaps@canonical.com"]},"contact":"mailto:snaps@canonical.com"},{"id":"99T7MUlRhtI3U0QFgl5mXXESAiSwt776","title":"core","summary":"snapd runtime environment","description":"The core runtime environment for snapd","installed-size":109043712,"install-date":"2024-04-11T01:42:05.749062355+00:00","name":"core","publisher":{"id":"canonical","username":"canonical","display-name":"Canonical","validation":"verified"},"developer":"canonical","status":"active","type":"os","version":"16-2.61.2","channel":"stable","tracking-channel":"latest/stable","ignore-validation":false,"revision":"16928","confinement":"strict","private":false,"devmode":false,"jailmode":false,"mounted-from":"/var/lib/snapd/snaps/core_16928.snap","links":{"contact":["mailto:snaps@canonical.com"],"website":["https://snapcraft.io"]},"contact":"mailto:snaps@canonical.com","website":"https://snapcraft.io"},{"id":"CSO04Jhav2yK0uz97cr0ipQRyqg0qQL6","title":"Core 18","summary":"Runtime environment based on Ubuntu 18.04","description":"The base snap based on the Ubuntu 18.04 release.","installed-size":58363904,"name":"core18","publisher":{"id":"canonical","username":"canonical","display-name":"Canonical","validation":"verified"},"developer":"canonical","status":"installed","type":"base","version":"20231027","channel":"stable","tracking-channel":"latest/stable","ignore-validation":false,"revision":"2812","confinement":"strict","private":false,"devmode":false,"jailmode":false,"mounted-from":"/var/lib/snapd/snaps/core18_2812.snap","links":{"contact":["https://github.com/snapcore/core18/issues"],"website":["https://snapcraft.io"]},"contact":"https://github.com/snapcore/core18/issues","website":"https://snapcraft.io"},{"id":"TKv5Fm000l4XiUYJW9pjWHLkCPlDbIg1","title":"GNOME 3.28 runtime","summary":"Shared GNOME 3.28 runtime for Ubuntu 18.04","description":"This snap includes a GNOME 3.28 stack (the base libraries and desktop \\nintegration components) and shares it through the content interface.","icon":"/v2/icons/gnome-3-28-1804/icon","installed-size":172830720,"install-date":"2024-04-11T01:51:22.822580656+00:00","name":"gnome-3-28-1804","publisher":{"id":"canonical","username":"canonical","display-name":"Canonical","validation":"verified"},"developer":"canonical","status":"active","type":"app","base":"core18","version":"3.28.0-19-g98f9e67.98f9e67","channel":"stable","tracking-channel":"latest/stable","ignore-validation":false,"revision":"198","confinement":"strict","private":false,"devmode":false,"jailmode":false,"mounted-from":"/var/lib/snapd/snaps/gnome-3-28-1804_198.snap","links":{"contact":["https://gitlab.gnome.org/Community/Ubuntu/gnome-3-28-1804/issues"]},"contact":"https://gitlab.gnome.org/Community/Ubuntu/gnome-3-28-1804/issues","media":[{"type":"icon","url":"https://dashboard.snapcraft.io/site_media/appmedia/2018/04/icon_ysMJicB.png","width":256,"height":256}]}],"sources":["local"]}'


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
def conn():
    _conn = Mock(spec=snap.SnapdApi)
    with patch("saltext.snap.modules.snap_mod._conn", return_value=_conn):
        yield _conn


@pytest.fixture
def sess():
    _sess = Mock()
    with patch("requests.Session", return_value=_sess):
        yield _sess


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
def test_info(
    verbose, run_mock, snap_info_out, snap_info_verbose_out, snap_info, snap_info_verbose
):
    run_mock.side_effect = (
        lambda c, **_: snap_info_verbose_out if "--verbose" in c else snap_info_out
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


@pytest.mark.parametrize("requests_available", (False, True), indirect=True)
@pytest.mark.parametrize("name,expected", (("hello-world", True), ("foobar", False)))
def test_is_installed(
    name, expected, snap_list_out, snap_list_api_out, cmd_run, sess, requests_available
):
    if requests_available:
        sess.get.return_value.json.return_value = (
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
    sess.get.return_value.json.return_value = json.loads(snap_list_api_out)
    assert snap.list_() == snap_list


@pytest.mark.usefixtures("requests_available")
@pytest.mark.parametrize("requests_available", (True,), indirect=True)
def test_list_api_revisions(sess, snap_list_api_revisions_out, snap_list):
    sess.get.return_value.json.return_value = json.loads(snap_list_api_revisions_out)
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
