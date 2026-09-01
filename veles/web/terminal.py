"""
veles/web/terminal.py

VELES native terminal PTY backend.

Provides an interactive shell session for the VELES web CLI.
This module is intentionally separate from command_tool.py.

command_tool.py:
    AI planner command execution

terminal.py:
    Interactive browser terminal via PTY
"""

import os
import pty
import select
import signal
import struct
import termios
import fcntl
import subprocess


DEFAULT_ROWS = 24
DEFAULT_COLS = 120


def _set_pty_size(fd, rows, cols):

    rows = max(1, int(rows))
    cols = max(1, int(cols))

    size = struct.pack(
        "HHHH",
        rows,
        cols,
        0,
        0
    )

    fcntl.ioctl(
        fd,
        termios.TIOCSWINSZ,
        size
    )


def create_terminal():

    """
    Create a new interactive VELES shell.

    Returns:

        master_fd
        process
    """

    master_fd, slave_fd = pty.openpty()

    _set_pty_size(
        slave_fd,
        DEFAULT_ROWS,
        DEFAULT_COLS
    )

    env = os.environ.copy()

    env["TERM"] = "xterm-256color"

    env["SHELL"] = "/bin/bash"

    env["VELES_TERMINAL"] = "1"

    process = subprocess.Popen(
        ["/bin/bash", "--login"],
        stdin=slave_fd,
        stdout=slave_fd,
        stderr=slave_fd,
        cwd="/opt/veles",
        env=env,
        start_new_session=True
    )

    os.close(slave_fd)

    return master_fd, process


def read_terminal(master_fd, timeout=0.1):

    """
    Read available PTY output.

    Returns decoded terminal data or an empty string.
    """

    try:

        readable, _, _ = select.select(
            [master_fd],
            [],
            [],
            timeout
        )

    except (OSError, ValueError):

        return ""

    if not readable:

        return ""

    try:

        data = os.read(
            master_fd,
            65536
        )

    except OSError:

        return ""

    if not data:

        return ""

    return data.decode(
        "utf-8",
        errors="replace"
    )


def write_terminal(master_fd, data):

    """
    Write browser input to the PTY.
    """

    if not data:

        return

    if isinstance(
        data,
        str
    ):

        data = data.encode(
            "utf-8"
        )

    os.write(
        master_fd,
        data
    )


def resize_terminal(
    master_fd,
    rows,
    cols
):

    """
    Resize the interactive terminal.
    """

    _set_pty_size(
        master_fd,
        rows,
        cols
    )


def close_terminal(
    master_fd,
    process
):

    """
    Safely terminate the PTY process.
    """

    try:

        if process.poll() is None:

            try:

                os.killpg(
                    process.pid,
                    signal.SIGHUP
                )

            except ProcessLookupError:

                pass

    finally:

        try:

            os.close(
                master_fd
            )

        except OSError:

            pass
