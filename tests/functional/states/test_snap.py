import pytest

pytestmark = [
    pytest.mark.requires_salt_states("snap.exampled"),
]


@pytest.fixture
def snap(states):
    return states.snap


def test_replace_this_this_with_something_meaningful(snap):
    echo_str = "Echoed!"
    ret = snap.exampled(echo_str)
    assert ret.result
    assert not ret.changes
    assert echo_str in ret.comment
