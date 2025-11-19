# Wrapper Mitigations for YachtDestroy Vulnerability

> Note: WIP.
> TODO: Make an all in one script to set this up automatically.

This directory contains configuration files and instructions to help mitigate the YachtDestroy vulnerability by setting up a secure reverse proxy using Nginx. The reverse proxy will handle incoming requests and forward them to the appropriate backend services while enforcing HTTPS and proper routing.

# 1. Generate SSL Certificates

Example output is provided for the [key](./private.key.sample) and [certificate](./public.crt.sample) files. You can generate your own self-signed SSL certificates using the following command:
```bash
openssl req -x509 -newkey rsa:2048 -keyout private.key -out public.crt -days 365 -nodes
```

# 2. Nginx Configuration

Download nginx and place the provided `ydwg-proxy.conf` file in the appropriate configuration directory (e.g., `/etc/nginx/conf.d/`).

# 3. Flask Proxy Application

```bash
pip install flask requests
```
Then run the smart proxy:
```bash
python3 ./ydwg-proxyapp.py
```