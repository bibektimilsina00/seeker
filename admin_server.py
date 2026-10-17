#!/usr/bin/env python3
"""
Seeker Admin Dashboard Server
Serves a modern Tailwind CSS dashboard and provides a REST API
reading db/results.csv in real-time.
"""

import os
import json
import base64
import time
import mimetypes
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
import db_manager
import tracker_service

PORT = int(os.environ.get('ADMIN_PORT', 8088))
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, 'admin')

class AdminHandler(BaseHTTPRequestHandler):
    def send_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()

    def do_HEAD(self):
        parsed = urlparse(self.path)
        path = parsed.path
        if path in ['/', '/index.html', '/admin', '/admin/']:
            file_path = os.path.join(STATIC_DIR, 'index.html')
        else:
            clean_path = path[7:] if path.startswith('/admin/') else path.lstrip('/')
            file_path = os.path.join(STATIC_DIR, clean_path)

        if os.path.isfile(file_path):
            content_type, _ = mimetypes.guess_type(file_path)
            content_type = content_type or 'text/html'
            self.send_response(200)
            self.send_cors_headers()
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(os.path.getsize(file_path)))
            self.end_headers()
        else:
            self.send_error(404, "Page Not Found")

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # REST API endpoint for targets data
        if path == '/api/targets':
            try:
                targets = db_manager.get_all_targets()
                payload = json.dumps({"status": "success", "count": len(targets), "targets": targets}).encode('utf-8')
                self.send_response(200)
                self.send_cors_headers()
                self.send_header('Content-Type', 'application/json')
                self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
                self.send_header('Content-Length', str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
            except Exception as e:
                err_payload = json.dumps({"status": "error", "message": str(e)}).encode('utf-8')
                self.send_response(500)
                self.send_cors_headers()
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(err_payload)
            return

        # Tracker status endpoint
        if path == '/api/tracker/status':
            try:
                status = tracker_service.get_tracker_status()
                payload = json.dumps({"status": "success", **status}).encode('utf-8')
                self.send_response(200)
                self.send_cors_headers()
                self.send_header('Content-Type', 'application/json')
                self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
                self.send_header('Content-Length', str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
            except Exception as e:
                err_payload = json.dumps({"status": "error", "message": str(e)}).encode('utf-8')
                self.send_response(500)
                self.send_cors_headers()
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(err_payload)
            return

        # Export raw CSV
        if path == '/api/export':
            try:
                csv_data = db_manager.export_csv_data().encode('utf-8')
                self.send_response(200)
                self.send_cors_headers()
                self.send_header('Content-Type', 'text/csv')
                self.send_header('Content-Disposition', 'attachment; filename="telemetry.csv"')
                self.send_header('Content-Length', str(len(csv_data)))
                self.end_headers()
                self.wfile.write(csv_data)
            except Exception as e:
                self.send_error(500, f"Export error: {e}")
            return

        # Fetch live tracker logs
        if path == '/api/tracker/logs':
            try:
                logs = tracker_service.get_tracker_logs(100)
                payload = json.dumps({"logs": logs}).encode('utf-8')
                self.send_response(200)
                self.send_cors_headers()
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
            except Exception as e:
                err_payload = json.dumps({"logs": [], "error": str(e)}).encode('utf-8')
                self.send_response(500)
                self.send_cors_headers()
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(err_payload)
            return

        # Static files & dashboard UI
        if path in ['/', '/index.html', '/admin', '/admin/']:
            file_path = os.path.join(STATIC_DIR, 'index.html')
        else:
            clean_path = path[7:] if path.startswith('/admin/') else path.lstrip('/')
            file_path = os.path.join(STATIC_DIR, clean_path)

        if os.path.isfile(file_path):
            content_type, _ = mimetypes.guess_type(file_path)
            content_type = content_type or 'application/octet-stream'
            with open(file_path, 'rb') as f:
                content = f.read()
            self.send_response(200)
            self.send_cors_headers()
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        else:
            self.send_error(404, "Page Not Found")

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == '/api/tracker/start':
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else '{}'
                data = json.loads(body) if body else {}
                status = tracker_service.start_tracker(data)
                payload = json.dumps({"status": "success", "message": "Tracker started successfully", **status}).encode('utf-8')
                self.send_response(200)
                self.send_cors_headers()
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
            except Exception as e:
                err_payload = json.dumps({"status": "error", "message": str(e)}).encode('utf-8')
                self.send_response(500)
                self.send_cors_headers()
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(err_payload)
            return

        if path == '/api/tracker/upload_image':
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length).decode('utf-8') if content_length > 0 else '{}'
                data = json.loads(body) if body else {}
                img_data_str = data.get('image', '')
                filename = data.get('filename', f'preview_{int(time.time())}.png')
                filename = os.path.basename(filename)
                if not any(filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.webp', '.gif']):
                    filename += '.png'

                if ',' in img_data_str:
                    img_data_str = img_data_str.split(',', 1)[1]

                raw_bytes = base64.b64decode(img_data_str)

                # Save file to template images directories
                for d in ['template/whatsapp/images', 'template/whatsapp_redirect/images', 'template/custom_og_tags/images']:
                    abs_d = os.path.join(BASE_DIR, d)
                    os.makedirs(abs_d, exist_ok=True)
                    with open(os.path.join(abs_d, filename), 'wb') as f:
                        f.write(raw_bytes)

                public_url = f"https://seeker.riocut.com/images/{filename}"
                payload = json.dumps({
                    "status": "success",
                    "url": public_url,
                    "filename": filename
                }).encode('utf-8')
                self.send_response(200)
                self.send_cors_headers()
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
            except Exception as e:
                err_payload = json.dumps({"status": "error", "message": str(e)}).encode('utf-8')
                self.send_response(500)
                self.send_cors_headers()
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(err_payload)
            return

        if path == '/api/tracker/logs/clear':
            try:
                tracker_service.clear_tracker_logs()
                payload = json.dumps({"status": "success", "message": "Logs cleared successfully"}).encode('utf-8')
                self.send_response(200)
                self.send_cors_headers()
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
            except Exception as e:
                err_payload = json.dumps({"status": "error", "message": str(e)}).encode('utf-8')
                self.send_response(500)
                self.send_cors_headers()
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(err_payload)
            return

        if path == '/api/tracker/stop':
            try:
                status = tracker_service.stop_tracker()
                payload = json.dumps({"status": "success", "message": "Tracker stopped successfully", **status}).encode('utf-8')
                self.send_response(200)
                self.send_cors_headers()
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
            except Exception as e:
                err_payload = json.dumps({"status": "error", "message": str(e)}).encode('utf-8')
                self.send_response(500)
                self.send_cors_headers()
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(err_payload)
            return

        if path == '/api/clear':
            try:
                db_manager.clear_db()
                payload = json.dumps({"status": "success", "message": "Telemetry database cleared. Backup saved."}).encode('utf-8')
                self.send_response(200)
                self.send_cors_headers()
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
            except Exception as e:
                err_payload = json.dumps({"status": "error", "message": str(e)}).encode('utf-8')
                self.send_response(500)
                self.send_cors_headers()
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(err_payload)
            return

        self.send_error(404, "Endpoint Not Found")

    def log_message(self, format, *args):
        # Clean logging
        pass


def run():
    server_address = ('0.0.0.0', PORT)
    httpd = ThreadingHTTPServer(server_address, AdminHandler)
    print(f"[+] Seeker Admin Dashboard running at http://0.0.0.0:{PORT}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()


if __name__ == '__main__':
    run()
