import pytest
import re

import salt.utils.platform
import salt.utils.pycrypto
from salt.exceptions import SaltInvocationError
from tests.support.mock import patch


passwd = "test_password"
invalid_salt = "thissaltistoolong" * 10
expecteds = {
    "sha512": {
        "hashed": "$6$rounds=65601$goodsalt$lZFhiN5M8RTLd9WKDin50H4lF4F8HGMIdwvKs.nTG7f8F0Y4P447Zb9/E8SkUWjY.K10QT3NuHZNDgc/P/NjT1",
        "salt": "rounds=65601$goodsalt",
        "badsalt": "badsalt",
    },
    "sha256": {
        "hashed": "$5$rounds=53501$goodsalt$W.uoco0wMfGLDOlsbW52E6raFS1Nhj0McfUTj2vORt7",
        "salt": "rounds=53501$goodsalt",
        "badsalt": "badsalt",
    },
    "blowfish": {
        "hashed": "$2b$10$goodsaltgoodsaltgoodsObFfGrJwfV.13QddrZIh2w1ccESmvj8K",
        "salt": "10$goodsaltgoodsaltgoodsa",
        "badsalt": "badsaltbadsaltbadsaltb",
    },
    "md5": {
        "hashed": "$1$goodsalt$4XQMx4a4e1MpBB8xzz.TQ0",
        "salt": "goodsalt",
        "badsalt": "badsalt",
    },
    "crypt": {"hashed": "goVHulDpuGA7w", "salt": "go", "badsalt": "ba"},
}


@pytest.mark.skipif(not salt.utils.pycrypto.HAS_CRYPT, reason="crypt not available")
def test_gen_hash_crypt():
    """
    Test gen_hash with crypt library
    """
    methods = salt.utils.pycrypto.methods

    for algorithm in methods:
        expected = expecteds[algorithm]
        ret = salt.utils.pycrypto.gen_hash(crypt_salt=expected["salt"], password=passwd, algorithm=algorithm)
        assert ret == expected["hashed"]

        ret = salt.utils.pycrypto.gen_hash(crypt_salt=expected["badsalt"], password=passwd, algorithm=algorithm)
        assert ret != expected["hashed"]

        ret = salt.utils.pycrypto.gen_hash(crypt_salt=None, password=passwd, algorithm=algorithm)
        assert ret != expected["hashed"]

    # Assert it works without arguments passed
    assert salt.utils.pycrypto.gen_hash() is not None

    # Assert it works without algorithm passed
    default_algorithm = salt.utils.pycrypto.crypt.methods[0].name.lower()
    expected = expecteds[default_algorithm]
    ret = salt.utils.pycrypto.gen_hash(crypt_salt=expected["salt"], password=passwd)
    assert ret == expected["hashed"]


@pytest.mark.skipif(not salt.utils.pycrypto.HAS_PASSLIB, reason="passlib not available")
@patch("salt.utils.pycrypto.methods", {})
@patch("salt.utils.pycrypto.HAS_CRYPT", False)
def test_gen_hash_passlib():
    """
    Test gen_hash with passlib
    """
    methods = salt.utils.pycrypto.known_methods

    for algorithm in methods:
        expected = expecteds[algorithm]
        ret = salt.utils.pycrypto.gen_hash(crypt_salt=expected["salt"], password=passwd, algorithm=algorithm)
        assert ret == expected["hashed"]

        ret = salt.utils.pycrypto.gen_hash(crypt_salt=expected["badsalt"],password=passwd, algorithm=algorithm)
        assert ret != expected["hashed"]

        ret = salt.utils.pycrypto.gen_hash(crypt_salt=None, password=passwd, algorithm=algorithm)
        assert ret != expected["hashed"]

    # Assert it works without arguments passed
    assert salt.utils.pycrypto.gen_hash() is not None

    # Assert it works without algorithm passed
    default_algorithm = salt.utils.pycrypto.known_methods[0]
    expected = expecteds[default_algorithm]
    if default_algorithm in expecteds:
        ret = salt.utils.pycrypto.gen_hash(crypt_salt=expected["salt"], password=passwd)
        assert ret == expected["hashed"]


@patch("salt.utils.pycrypto.HAS_CRYPT", False)
@patch("salt.utils.pycrypto.HAS_PASSLIB", False)
def test_gen_hash_no_lib():
    """
    test gen_hash with no crypt library available
    """
    with pytest.raises(SaltInvocationError):
        salt.utils.pycrypto.gen_hash()


@patch("salt.utils.pycrypto.HAS_CRYPT", True)
@patch("salt.utils.pycrypto.methods", {"crypt": None})
@patch("salt.utils.pycrypto.HAS_PASSLIB", True)
def test_gen_hash_selection():
    """
    verify the hash backend selection works correctly
    """
    with patch("salt.utils.pycrypto._gen_hash_crypt", autospec=True) as gh_crypt:
        with patch("salt.utils.pycrypto._gen_hash_passlib", autospec=True) as gh_passlib:
            with pytest.raises(SaltInvocationError):
                salt.utils.pycrypto.gen_hash(algorithm="doesntexist")

            salt.utils.pycrypto.gen_hash(algorithm="crypt")
            gh_crypt.assert_called_once()
            gh_passlib.assert_not_called()

            gh_crypt.reset_mock()
            salt.utils.pycrypto.gen_hash(algorithm="sha512")
            gh_crypt.assert_not_called()
            gh_passlib.assert_called_once()


def test_gen_hash_crypt_warning():
    """
    Verify that a bad crypt salt triggers a warning
    """
    with patch("salt.utils.pycrypto.log", autospec=True) as log:
        try:
            salt.utils.pycrypto.gen_hash(crypt_salt="toolong", password=passwd, algorithm="crypt")
        except Exception:  # pylint: disable=broad-except
            pass
    log.warning.assert_called_with("Hash salt is too long for 'crypt' hash.")


def test_secure_password():
    """
    test secure_password
    """
    ret = salt.utils.pycrypto.secure_password()
    check = re.compile(r"[!@#$%^&*()_=+]")
    assert check.search(ret) is None
    assert type(ret) is str
