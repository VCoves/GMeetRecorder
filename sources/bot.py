from xvfbwrapper import Xvfb
from upc_backend import UPCBackend
from gmail_backend import GmailBackend
import threading
import subprocess
from queue import Queue
import os
import sys


def backend_factory(backend, email, user, passwd, w, h):
    b = ["gmail", "upc"]
    if backend == b[0]:
        return GmailBackend(email, passwd, resolution=(w, h))
    elif backend == b[1]:
        return UPCBackend(email, user, passwd, resolution=(w, h))
    print(f"Invalid Backend. Choose one of: {b}")
    sys.exit(1)


def start_bot(q, backend, meet_url, email, user, passwd, w, h, min_time, max_time, frac_to_exit):
    with Xvfb(width=w, height=h, colordepth=24) as xvfb:
        q.put(xvfb.new_display)
        m = backend_factory(backend, email, user, passwd, w, h)
        m.meet_while(meet_url, min_time, max_time, frac_to_exit)


def main():
    backend = os.getenv("BACKEND")
    user = os.getenv("ORG_USER")
    if backend != "gmail" and not user:
        print("Non gmail backends require ORG_USER")
        sys.exit(1)
    email = os.getenv("EMAIL")
    passwd = os.getenv("PASSWORD")
    meet_url = os.getenv("MEET_URL")
    if not (email and passwd and meet_url):
        print("EMAIL, PASSWORD and MEET_URL are always required.")
        sys.exit(1)
    filename = os.getenv("VIDEO_NAME")
    max_duration = int(os.getenv("MAX_DURATION"))
    min_duration = int(os.getenv("MIN_DURATION"))
    frac_to_exit = float(os.getenv("FRAC_TO_EXIT"))
    fps = os.getenv("FPS")
    width, height = os.getenv("RESOLUTION").split("x")
    width, height = int(width), int(height)

    q = Queue()
    bot_thread = threading.Thread(target=start_bot, args=(q, backend, meet_url, email, user, passwd, width, height,
                                                          min_duration, max_duration, frac_to_exit))
    bot_thread.start()
    display = q.get(block=True, timeout=10)
    ffmpeg_p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "x11grab", "-r", fps, "-video_size",
                                 f"{width}x{height}", "-draw_mouse", "0", "-i", f":{display}",
                                 "-f", "pulse", "-ac", "2", "-i", "default", f"/output/{filename}.webm"])
    bot_thread.join()
    ffmpeg_p.kill()


if __name__ == "__main__":
    main()
