# gunicorn_conf.py
import threading
import os

def post_fork(server, worker):
    try:
        # Import app module and start background warm in this worker process
        import src.app as app_mod
        t = threading.Thread(target=app_mod.warm_worker_once, daemon=True)
        t.start()
        server.log.info("started warm thread for worker %s", worker.pid)
    except Exception as e:
        server.log.warning("failed to start warm thread: %s", e)
