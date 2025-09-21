from flask import Flask, request, Response, send_from_directory
import requests
import os

# Simple static + API proxy dev server.
# - Serves your project files (HTML/CSS/JS) from the current directory
# - Proxies any /api/* request to the real backend on http://127.0.0.1:8000
# - This lets you use http://127.0.0.1:5501 for both pages and API (same-origin),
#   so cookies and sessions work reliably in the browser.

APP_PORT = int(os.getenv("DEV_PORT", 5501))
BACKEND_BASE = os.getenv("BACKEND_BASE", "http://127.0.0.1:8000")

app = Flask(__name__, static_folder='.', static_url_path='')

# -------- Proxy helpers --------
IGNORED_HEADERS = {"content-encoding", "transfer-encoding", "content-length", "connection"}


def _proxy(method: str, path: str):
    url = f"{BACKEND_BASE}/api/{path}"

    # Forward query string and body
    params = request.args.to_dict(flat=False)
    data = request.get_data() if method in ("POST", "PUT", "PATCH") else None

    # Forward headers (except Host) and cookies
    headers = {k: v for k, v in request.headers.items() if k.lower() != "host"}

    try:
        resp = requests.request(
            method,
            url,
            params=params,
            data=data,
            headers=headers,
            cookies=request.cookies,
            allow_redirects=False,
            timeout=30,
        )
    except requests.RequestException as e:
        return Response(str(e), status=502)

    # Build the Flask response
    excluded = set(h.lower() for h in IGNORED_HEADERS)
    response_headers = [(name, value) for name, value in resp.headers.items() if name.lower() not in excluded]

    # Ensure Set-Cookie headers are forwarded correctly (requests exposes combined header)
    # Flask Response will handle splitting if multiple Set-Cookie headers are provided.
    flask_resp = Response(resp.content, status=resp.status_code)
    for name, value in response_headers:
        # Preserve multiple Set-Cookie headers
        if name.lower() == 'set-cookie':
            for cookie in resp.headers.getlist('Set-Cookie') if hasattr(resp.headers, 'getlist') else [value]:
                flask_resp.headers.add('Set-Cookie', cookie)
        else:
            flask_resp.headers[name] = value

    return flask_resp


# -------- Proxy routes --------
@app.route('/api/<path:path>', methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'])
def api_proxy(path):
    return _proxy(request.method, path)


# -------- Static routes --------
@app.route('/')
@app.route('/<path:filename>')
def static_files(filename: str = 'index.html'):
    # Serve any file from the project directory
    if os.path.isdir(filename):
        # Prevent directory listing by serving index.html if present, else 404
        index_path = os.path.join(filename, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(filename, 'index.html')
        return Response('Not found', status=404)
    try:
        # Try to serve exact file
        return send_from_directory('.', filename)
    except Exception:
        # Fallback to 404
        return Response('Not found', status=404)


if __name__ == '__main__':
    print(f"\nDev proxy server running:")
    print(f"- Frontend:  http://127.0.0.1:{APP_PORT}")
    print(f"- Backend -> {BACKEND_BASE}")
    print("  (All requests to /api/* are proxied to the backend)\n")
    app.run(host='127.0.0.1', port=APP_PORT, debug=False)

