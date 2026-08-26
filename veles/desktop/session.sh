#!/bin/sh
set -e

cd /home/zeljko/veles

if [ -f /etc/veles/veles.env ]; then
    set -a
    . /etc/veles/veles.env
    set +a
fi

/home/zeljko/veles/venv/bin/python -m veles.web.app &

/usr/bin/python3 /home/zeljko/veles/veles/desktop/shell.py &

exec dbus-run-session /usr/bin/labwc
