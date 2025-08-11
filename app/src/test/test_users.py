"""
Documentation
"""

import kutils


def test_users():
    """
    Tests something
    """

    token = kutils.get_token("admin", "admin")
    assert token is not None

    token = kutils.get_token("someone", "secret")
    assert token is None
