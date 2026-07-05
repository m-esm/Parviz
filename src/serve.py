#!/usr/bin/env python3
"""Tiny localhost static server for the Three.js viewer.
Browsers won't fetch assembly.glb over file://, so serve it over http.

    python3 serve.py 8765      # then open http://localhost:8765/viewer_glb.html

Serves the directory that holds the viewer + assembly.glb. In the full project layout
(scripts in src/, assets in web/) that is web/; in the flat single-part layout it is the
script's own dir. Override with: python3 serve.py 8765 <dir>.
"""
import http.server, socketserver, sys, os

port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765

HERE = os.path.dirname(os.path.abspath(__file__))
# repo root = parent of src/ when this lives in src/, else the script dir itself
ROOT = os.path.dirname(HERE) if os.path.basename(HERE) == "src" else HERE
web = os.path.join(ROOT, "web")
serve_dir = sys.argv[2] if len(sys.argv) > 2 else (web if os.path.isdir(web) else HERE)
os.chdir(serve_dir)


class Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map,
                      ".glb": "model/gltf-binary"}
    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()


socketserver.TCPServer.allow_reuse_address = True   # rebind immediately after a restart (no TIME_WAIT wait)
with socketserver.TCPServer(("127.0.0.1", port), Handler) as httpd:
    print(f"Serving {os.getcwd()}\n  -> http://localhost:{port}/viewer_glb.html\nCtrl-C to stop")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")
