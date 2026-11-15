# runs slow work in a background thread so the gui never freezes
import threading


# runs func(*args) in a daemon thread, then calls on_done or on_error on the gui thread
def run_in_background(widget, func, *args, on_done=None, on_error=None):
    # worker body; results are handed back through widget.after for thread safety
    def task():
        try:
            result = func(*args)
        except Exception as error:
            if on_error:
                widget.after(0, on_error, error)
            return
        if on_done:
            widget.after(0, on_done, result)

    thread = threading.Thread(target=task, daemon=True)
    thread.start()
    return thread
