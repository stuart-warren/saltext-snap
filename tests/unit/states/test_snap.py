import pytest
import salt.modules.test as testmod
import saltext.snap.modules.snap_mod as snap_module
import saltext.snap.states.snap_mod as snap_state


@pytest.fixture
def configure_loader_modules():
    return {
        snap_module: {
            "__salt__": {
                "test.echo": testmod.echo,
            },
        },
        snap_state: {
            "__salt__": {
                "snap.example_function": snap_module.example_function,
            },
        },
    }


def test_replace_this_this_with_something_meaningful():
    echo_str = "Echoed!"
    expected = {
        "name": echo_str,
        "changes": {},
        "result": True,
        "comment": f"The 'snap.example_function' returned: '{echo_str}'",
    }
    assert snap_state.exampled(echo_str) == expected
