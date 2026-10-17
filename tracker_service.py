#!/usr/bin/env python3
"""
Tracker Service Supervisor
Controls starting, stopping, and monitoring seeker.py and PHP server
via REST API for the Admin Dashboard.
"""

import os
import sys
import subprocess
import signal
import psutil
import json
import time
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PID_FILE = os.path.join(BASE_DIR, 'pid')
TEMPLATES_JSON = os.path.join(BASE_DIR, 'template', 'templates.json')
LOG_DIR = os.path.join(BASE_DIR, 'logs')
RUNTIME_LOG = os.path.join(LOG_DIR, 'seeker_runtime.log')

tracker_process = None
current_config = {
    "template_id": 0,
    "template_name": "NearYou",
    "port": 8080,
    "started_at": None,
}


def get_templates():
    if not os.path.exists(TEMPLATES_JSON):
        return []
    with open(TEMPLATES_JSON, 'r', encoding='utf-8') as f:
        data = json.load(f)
        templates = data.get('templates', [])
        result = []
        for idx, t in enumerate(templates):
            result.append({
                "id": idx,
                "name": t.get("name"),
                "dir_name": t.get("dir_name"),
            })
        return result


def is_tracker_running():
    global tracker_process
    
    # 1. Check if our tracker_process object is alive
    if tracker_process is not None:
        if tracker_process.poll() is None:
            return True
        else:
            tracker_process = None

    # 2. Check if PHP process in pid file is alive
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, 'r') as f:
                content = f.read().strip()
                if content.isdigit():
                    php_pid = int(content)
                    if psutil.pid_exists(php_pid):
                        return True
        except Exception:
            pass

    # 3. Check if any seeker.py process is alive
    for proc in psutil.process_iter(['pid', 'cmdline']):
        try:
            cmd = " ".join(proc.info['cmdline'] or [])
            if 'seeker.py' in cmd and proc.pid != os.getpid():
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    return False


def get_tracker_status():
    running = is_tracker_running()
    templates = get_templates()
    t_id = current_config.get('template_id', 0)
    t_name = current_config.get('template_name', 'NearYou')
    port = current_config.get('port', 8080)
    
    # Read last few log lines
    last_logs = []
    if os.path.exists(RUNTIME_LOG):
        try:
            with open(RUNTIME_LOG, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()
                last_logs = [line.strip() for line in lines[-15:] if line.strip()]
        except Exception:
            pass

    return {
        "running": running,
        "template_id": t_id,
        "template_name": t_name,
        "port": port,
        "url": f"http://0.0.0.0:{port}",
        "started_at": current_config.get('started_at'),
        "templates": templates,
        "logs": last_logs
    }


def start_tracker(template_id=0, port=8080, custom_env=None):
    global tracker_process, current_config
    
    # Stop existing instance if running
    stop_tracker()
    
    # Ensure log directory exists
    os.makedirs(LOG_DIR, exist_ok=True)
    
    # Clean up stale files
    if os.path.exists(PID_FILE):
        try:
            os.remove(PID_FILE)
        except Exception:
            pass

    templates = get_templates()
    template_name = "NearYou"
    for t in templates:
        if t["id"] == template_id:
            template_name = t["name"]
            break

    # Build environment variables
    env = os.environ.copy()
    env['PORT'] = str(port)
    env['TEMPLATE'] = str(template_id)
    env['DEBUG_HTTP'] = '1'

    # Support template parameters
    if custom_env and isinstance(custom_env, dict):
        for k, v in custom_env.items():
            if v is not None and str(v).strip():
                env[k] = str(v).strip()

    # Open log file
    log_fp = open(RUNTIME_LOG, 'w', encoding='utf-8')
    log_fp.write(f"=== Starting Seeker Template {template_name} (#{template_id}) on port {port} at {datetime.now()} ===\n")
    log_fp.flush()

    cmd = [sys.executable, os.path.join(BASE_DIR, 'seeker.py'), '-t', str(template_id), '-p', str(port)]
    
    tracker_process = subprocess.Popen(
        cmd,
        cwd=BASE_DIR,
        env=env,
        stdout=log_fp,
        stderr=subprocess.STDOUT
    )

    current_config = {
        "template_id": template_id,
        "template_name": template_name,
        "port": port,
        "started_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    # Wait briefly to let seeker and php start
    time.sleep(2)

    return get_tracker_status()


def stop_tracker():
    global tracker_process, current_config

    # 1. Terminate tracker_process if tracked
    if tracker_process is not None:
        try:
            tracker_process.terminate()
            tracker_process.wait(timeout=2)
        except Exception:
            try:
                tracker_process.kill()
            except Exception:
                pass
        tracker_process = None

    # 2. Kill PHP process recorded in PID file
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, 'r') as f:
                content = f.read().strip()
                if content.isdigit():
                    php_pid = int(content)
                    if psutil.pid_exists(php_pid):
                        p = psutil.Process(php_pid)
                        p.terminate()
                        try:
                            p.wait(timeout=2)
                        except psutil.TimeoutExpired:
                            p.kill()
            os.remove(PID_FILE)
        except Exception:
            if os.path.exists(PID_FILE):
                try:
                    os.remove(PID_FILE)
                except Exception:
                    pass

    # 3. Kill any lingering seeker.py or php processes on the port
    port = current_config.get('port', 8080)
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmd = " ".join(proc.info['cmdline'] or [])
            if ('seeker.py' in cmd and proc.pid != os.getpid()) or (f':{port}' in cmd and 'php' in cmd):
                proc.terminate()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    current_config["started_at"] = None
    return get_tracker_status()
