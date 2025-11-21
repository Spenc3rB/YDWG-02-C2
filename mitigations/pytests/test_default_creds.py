import pytest
import requests
import urllib3

BASE_URL = "https://192.168.0.232" # change to your server IP


@pytest.fixture(scope="module")
def session():
    s = requests.Session()

    # If your proxy/flask app expects a session cookie, keep this; otherwise omit.
    s.cookies.set(
        "session",
        "D033E22AE348AEB5660FC2140AEC35850C4DA997",
        domain="192.168.0.232",
    )

    s.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/142.0.0.0 Safari/537.36"
            ),
            "Accept": "*/*",
            "Origin": BASE_URL,
        }
    )

    # If using HTTPS with self-signed certs:
    s.verify = False
    return s


# ======== Tests for /admin/changepassword ========

@pytest.mark.parametrize(
    "password, expected_msg",
    [
        # Too short (< 8 chars)
        ("Admin1$", "Password must be at least 8 characters long."),
        # No lowercase letters
        ("ABCDEFG1$", "Password must contain at least one lowercase letter."),
        # No uppercase letters
        ("abcdefgh1$", "Password must contain at least one uppercase letter."),
        # No digits
        ("Abcdefgh$", "Password must contain at least one digit."),
        # No allowed special characters
        ("Abcdefg1", "Password must contain at least one special character (_ @ $)."),
        # Invalid character (e.g. '!' is not in _@$)
        (
            "Abcdef1!",
            "Password contains invalid character '!'. Allowed specials: _@$",
        ),
    ],
)
def test_change_password_weak_passwords(session, password, expected_msg):
    """
    For weak passwords, /admin/changepassword should respond with HTTP 400
    and the exact message from is_strong_password().
    """
    url = f"{BASE_URL}/admin/changepassword"
    params = {"1": "1", "password": password}

    resp = session.post(url, params=params, data=None)

    assert resp.status_code == 400
    assert resp.text.strip() == expected_msg


def test_change_password_missing_password(session):
    """
    If password is missing entirely, is_strong_password(None) -> 'Password is required.'
    """
    url = f"{BASE_URL}/admin/changepassword"
    params = {"1": "1"}  # note: no 'password' key

    resp = session.post(url, params=params, data=None)

    assert resp.status_code == 400
    assert resp.text.strip() == "Password is required."


@pytest.mark.parametrize(
    "password",
    [
        "Abcdef1_",  # valid: >=8, has lower, upper, digit, special _
        "StrongP4ss$",  # another valid example
    ],
)
def test_change_password_strong_password_not_blocked(session, password):
    """
    For strong passwords, the Flask code calls the backend and does NOT return 400.
    We don't assert the exact backend response here, only that it's not a validation error.
    NOTE: this requires your backend (192.168.0.69) to be reachable.
    """
    url = f"{BASE_URL}/admin/changepassword"
    params = {"1": "1", "password": password}

    resp = session.post(url, params=params, data=None)

    # Just ensure we did NOT hit the validation error path.
    assert resp.status_code != 400
    # Optionally you can assert more if you know what backend returns (e.g. 204).


# ======== Tests for /login interception (same password rules) ========

@pytest.mark.parametrize(
    "password",
    [
        "Admin1$",    # too short
        "ABCDEFG1$",  # no lowercase
        "abcdefgh1$", # no uppercase
        "Abcdefgh$",  # no digit
        "Abcdefg1",   # no special
        "Abcdef1!",   # invalid char
        "",           # empty
    ],
)
def test_login_weak_password_redirects_to_admin(session, password):
    """
    /login with weak password should NOT hit the device.
    It should redirect (302) to /admin.html and set the default admin session cookie.
    """
    url = f"{BASE_URL}/login"
    params = {"password": password} if password != "" else {}

    # IMPORTANT: don't follow redirects so we can inspect the 302 and headers.
    resp = session.post(url, params=params, data=None, allow_redirects=False)

    assert resp.status_code == 302
    assert resp.headers.get("Location") == "/admin.html"

    # Check for the default admin cookie set in your code:
    # resp.set_cookie("session", "D033E22AE348AEB5660FC2140AEC35850C4DA997", ...)
    cookie_header = resp.headers.get("Set-Cookie", "")
    assert "session=D033E22AE348AEB5660FC2140AEC35850C4DA997" in cookie_header


@pytest.mark.parametrize(
    "password",
    [
        "Abcdef1_",
        "StrongP4ss$", # might need to login with this after this test is run
    ],
)
def test_login_strong_password_proxied(session, password):
    """
    /login with strong passwords should be proxied to the backend, not blocked.
    We only assert that we don't get redirected back to /admin.html with 302.
    """
    url = f"{BASE_URL}/login"
    params = {"password": password}

    resp = session.post(url, params=params, data=None, allow_redirects=False)

    # For strong passwords, we shouldn't see the "force redirect to /admin.html" path.
    assert not (resp.status_code == 302 and resp.headers.get("Location") == "/admin.html")
    # Optionally assert more depending on expected backend behavior.
