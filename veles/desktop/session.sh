#!/bin/sh
set -e

cd /opt/veles

if [ -f /etc/veles/veles.env ]; then
    set -a
    . /etc/veles/veles.env
    set +a
fi

/opt/veles/venv/bin/python -m veles.web.app &

/opt/veles/venv/bin/python /opt/veles/veles/desktop/shell.py &

exec dbus-run-session /usr/bin/labwc
