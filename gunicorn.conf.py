"""OpenClaw Memory Web UI — Gunicorn configuration"""
import os

bind = os.environ.get("BIND", "127.0.0.1:5000")
workers = int(os.environ.get("WORKERS", "2"))
timeout = 30
accesslog = os.environ.get("ACCESS_LOG", "-")
errorlog = os.environ.get("ERROR_LOG", "-")
loglevel = "info"
