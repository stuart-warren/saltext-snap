import pytest

pytestmark = [
    pytest.mark.requires_salt_modules("snap.example_function"),
]


@pytest.fixture
def snap(modules):
    return modules.snap


def test_replace_this_this_with_something_meaningful(snap):
    echo_str = "Echoed!"
    res = snap.example_function(echo_str)
    assert res == echo_str
