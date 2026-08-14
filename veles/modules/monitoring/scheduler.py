"""
VELES Monitoring Scheduler

Background scheduler for automatic health checks.
"""

import threading

from datetime import datetime, timedelta


class MonitoringScheduler:
    """
    Simple background monitoring scheduler.
    """

    def __init__(
        self,
        service,
        interval=60
    ):

        self.service = service

        self.interval = max(
            1,
            int(interval)
        )

        self.running = False

        self.thread = None

        self._stop_event = threading.Event()

        self._lock = threading.RLock()

        self.last_check_at = None

        self.next_check_at = None

        self.check_count = 0

        self.last_resource_count = 0

        self.last_healthy = 0

        self.last_warning = 0

        self.last_critical = 0

        self.last_unknown = 0


    def start(
        self,
        resources_provider
    ):
        """
        Start monitoring loop.
        """

        if self.running:

            return False


        if not callable(
            resources_provider
        ):

            raise TypeError(
                "resources_provider must be callable"
            )


        self.running = True

        self._stop_event.clear()


        with self._lock:

            self.last_check_at = None

            self.next_check_at = (
                datetime.now()
                + timedelta(
                    seconds=self.interval
                )
            )

            self.check_count = 0

            self.last_resource_count = 0

            self.last_healthy = 0

            self.last_warning = 0

            self.last_critical = 0

            self.last_unknown = 0


        self.thread = threading.Thread(

            target=self._worker,

            args=(
                resources_provider,
            ),

            daemon=True,

            name="veles-monitoring"

        )


        self.thread.start()


        return True


    def stop(self):
        """
        Stop monitoring loop.
        """

        self.running = False

        self._stop_event.set()


        with self._lock:

            self.next_check_at = None


        thread = self.thread


        if (
            thread
            and thread.is_alive()
            and thread is not threading.current_thread()
        ):

            thread.join(
                timeout=2
            )


        self.thread = None


    def is_running(self):

        return (
            self.running
            and self.thread is not None
            and self.thread.is_alive()
        )


    def get_status(self):
        """
        Return scheduler state for the web UI.
        """

        with self._lock:

            return {

                "running":
                    self.is_running(),

                "interval":
                    self.interval,

                "last_check_at":
                    self.last_check_at,

                "next_check_at":
                    self.next_check_at,

                "check_count":
                    self.check_count,

                "resource_count":
                    self.last_resource_count,

                "healthy":
                    self.last_healthy,

                "warning":
                    self.last_warning,

                "critical":
                    self.last_critical,

                "unknown":
                    self.last_unknown

            }


    def _set_next_check(self):

        with self._lock:

            self.next_check_at = (
                datetime.now()
                + timedelta(
                    seconds=self.interval
                )
            )


    def _worker(
        self,
        resources_provider
    ):

        print(
            "[MONITORING] Worker started",
            flush=True
        )


        while self.running:

            with self._lock:

                self.next_check_at = (
                    datetime.now()
                )


            print(
                "[MONITORING] Calling resources provider...",
                flush=True
            )


            try:

                resources = resources_provider()


                print(
                    "[MONITORING] Resources provider returned",
                    flush=True
                )


                resource_count = len(
                    resources or []
                )


                print(
                    "[MONITORING] Check cycle:",
                    resource_count,
                    "resources",
                    flush=True
                )


                results = self.service.check_resources(
                    resources or []
                )


                print(
                    "[MONITORING] check_resources() returned",
                    flush=True
                )


                healthy = 0

                warning = 0

                critical = 0

                unknown = 0


                for result in results:

                    status = getattr(
                        result,
                        "status",
                        "unknown"
                    )


                    status = str(
                        status
                    ).strip().lower()


                    if status == "healthy":

                        healthy += 1

                    elif status == "warning":

                        warning += 1

                    elif status == "critical":

                        critical += 1

                    else:

                        unknown += 1


                with self._lock:

                    self.last_check_at = (
                        datetime.now().isoformat()
                    )

                    self.check_count += 1

                    self.last_resource_count = (
                        resource_count
                    )

                    self.last_healthy = healthy

                    self.last_warning = warning

                    self.last_critical = critical

                    self.last_unknown = unknown


                print(
                    "[MONITORING] Check cycle complete:",
                    "healthy=",
                    healthy,
                    "warning=",
                    warning,
                    "critical=",
                    critical,
                    "unknown=",
                    unknown,
                    flush=True
                )


            except Exception as exc:

                print(
                    "[MONITORING ERROR]",
                    repr(exc),
                    flush=True
                )


                with self._lock:

                    self.last_check_at = (
                        datetime.now().isoformat()
                    )

                    self.check_count += 1


            self._set_next_check()


            print(
                "[MONITORING] Waiting",
                self.interval,
                "seconds...",
                flush=True
            )


            if self._stop_event.wait(
                self.interval
            ):

                break


        self.running = False


        with self._lock:

            self.next_check_at = None


        print(
            "[MONITORING] Worker stopped",
            flush=True
        )