from flask import Flask, request, Response, redirect
import requests

app = Flask(__name__)

BACKEND_IP = "http://192.168.0.69" # IP of the legacy device; change as needed

# State: block everything until default/weak password has been replaced
WEAK_PASS_ACTIVE = True

def proxy_to_backend(full_url, method=None, headers=None, data=None, cookies=None):
    """Helper to proxy a single request to the backend."""
    
    if method is None:
        method = request.method

    if headers is None:
        headers = {}
        for k, v in request.headers.items():
            lk = k.lower()
            if lk in ("host", "content-length", "connection", "accept-encoding"):
                continue
            headers[k] = v
        headers["Host"] = "192.168.0.69"

    resp = requests.request(
        method=method,
        url=full_url,
        headers=headers,
        data=data if data is not None else request.get_data(),
        cookies=cookies if cookies is not None else request.cookies,
        allow_redirects=False,
        stream=True,
        timeout=5,
    )

    excluded_headers = {
        "content-encoding",
        "content-length",
        "transfer-encoding",
        "connection",
    }

    response_headers = [
        (name, value)
        for name, value in resp.raw.headers.items()
        if name.lower() not in excluded_headers
    ]

    return Response(resp.content, resp.status_code, response_headers)


def is_strong_password(pw: str):
    if not pw:
        return False, "Password is required."
    if len(pw) < 8:
        return False, "Password must be at least 8 characters long."

    lp = up = dg = sp = 0
    allowed_specials = "_@$"

    for ch in pw:
        if "a" <= ch <= "z":
            lp += 1
        elif "A" <= ch <= "Z":
            up += 1
        elif "0" <= ch <= "9":
            dg += 1
        elif ch in allowed_specials:
            sp += 1
        else:
            return False, f"Password contains invalid character '{ch}'. Allowed specials: {allowed_specials}"

    if lp < 1:
        return False, "Password must contain at least one lowercase letter."
    if up < 1:
        return False, "Password must contain at least one uppercase letter."
    if dg < 1:
        return False, "Password must contain at least one digit."
    if sp < 1:
        return False, "Password must contain at least one special character (_ @ $)."

    return True, "OK"

def init_filter():
    backend_url = f"{BACKEND_IP}/filters/setfilter?1=1&server=3&protocol=1&filter=0&type=0&data=%20"

    proxied = proxy_to_backend(
        backend_url,
        method="POST",
        headers={"Host": "192.168.0.69"},
        data=b"",
        cookies={"session": "D033E22AE348AEB5660FC2140AEC35850C4DA997"}, # default admin session cookie
    )

    print(
        f"Status code {proxied.status_code} with body: "
        f"{proxied.data.decode('utf-8', errors='ignore')} for initial filter reset attempt."
    )

init_filter()

@app.route("/", defaults={"path": ""}, methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@app.route("/<path:path>", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
def generic_proxy(path):
    global WEAK_PASS_ACTIVE

    normalized = (path or "").lstrip("/")

    # case 1: intercept login attempt on FIRST login to change hardcoded, weak, default password
    if normalized == "login" and request.method == "POST":
        password = request.args.get("password") or request.form.get("password")
        print(f"Login attempt with password: {password}")

        # Block weak passwords before they hit the device (admin)
        ok, msg = is_strong_password(password)
        if not ok:
            # Redirect to device's own /admin.html page
            resp = redirect("/admin.html", code=302)
            # Give the browser a default admin session cookie so the page works ;)
            resp.set_cookie(
                "session",
                "D033E22AE348AEB5660FC2140AEC35850C4DA997",
                httponly=True,
                secure=True,
                path="/",
            )
            return resp

        backend_url = f"{BACKEND_IP}/{normalized}"
        if request.query_string: # if there are query parameters, append them
            backend_url += "?" + request.query_string.decode("utf-8", errors="ignore")

        proxied = proxy_to_backend(backend_url)

        # consider fixed
        if proxied.status_code == 204:
            WEAK_PASS_ACTIVE = False

        return proxied
    
    # case 2: intercept password change attempt to enforce strong password
    if normalized == "admin/changepassword" and request.method == "POST":
        new_password = request.args.get("password") or request.form.get("password")
        ok, msg = is_strong_password(new_password)
        if not ok:
            # Block weak passwords before they hit the device
            return Response(msg, status=400)

        backend_url = f"{BACKEND_IP}/{normalized}"
        if request.query_string:
            backend_url += "?" + request.query_string.decode("utf-8", errors="ignore")

        proxied = proxy_to_backend(backend_url)

        # consider fixed
        if proxied.status_code == 204:
            WEAK_PASS_ACTIVE = False

        return proxied
    
    ALWAYS_ALLOW = {
        "",
        "login",
        "login.html",
        "admin.html",
        "admin/changepassword",
        "y.css",
        "ui.js",
        "version",
        "yachtd.png",
        "favicon.ico",
        "menu"
    }

    if WEAK_PASS_ACTIVE:
        if normalized not in ALWAYS_ALLOW:
            # Force user back to page until it's fixed
            return redirect("/admin.html", code=302)

    # default: proxy everything else
    backend_url = f"{BACKEND_IP}/{normalized}"
    if request.query_string:
        backend_url += "?" + request.query_string.decode("utf-8", errors="ignore")

    return proxy_to_backend(backend_url)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
