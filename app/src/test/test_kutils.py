"""
Documentation
"""

import kutils


def test_kutils_get_kc_admin():
    """
    Tests the function get_kc_admin() from kutils.
    """

    kc_admin = kutils.get_kc_admin()
    assert kc_admin is not None


def test_is_username_unique():
    """
    Tests the function is_username_unique from kutils.
    """

    assert kutils.is_username_unique("admin") is True
