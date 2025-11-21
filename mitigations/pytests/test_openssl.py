import socket
import pytest
from OpenSSL import SSL


HOST = "192.168.0.232" # change to your server IP
PORT = 443

def connect_with_version(minv, maxv):
    """
    Helper: perform handshake with forced TLS versions.
    Returns negotiated protocol name string, or raises SSL.Error.
    """
    ctx = SSL.Context(SSL.TLS_METHOD)
    ctx.set_min_proto_version(minv)
    ctx.set_max_proto_version(maxv)

    sock = socket.create_connection((HOST, PORT))
    conn = SSL.Connection(ctx, sock)
    conn.set_connect_state()

    try:
        conn.do_handshake()
        return conn.get_protocol_version_name()
    finally:
        try:
            conn.shutdown()
        except Exception:
            pass
        sock.close()

def test_tlsv1_23_succeeds():
    """Server must negotiate TLSv1.3 when asked."""
    negotiated = connect_with_version(SSL.TLS1_3_VERSION, SSL.TLS1_3_VERSION)
    assert negotiated == "TLSv1.3", f"Expected TLSv1.3, got {negotiated}"
    negotiated = connect_with_version(SSL.TLS1_2_VERSION, SSL.TLS1_2_VERSION)
    assert negotiated == "TLSv.2", f"Expected TLSv1.2, got {negotiated}"
    

@pytest.mark.parametrize("version, name", [
    (SSL.TLS1_1_VERSION, "TLSv1.1"),
    (SSL.TLS1_VERSION,   "TLSv1.0"),
])
def test_old_protocols_fail(version, name):
    """
    Server must reject all older TLS versions.
    These tests PASS only if handshake fails.
    """
    with pytest.raises(SSL.Error):
        connect_with_version(version, version)
