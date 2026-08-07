"""
VELES Monitoring Scheduler

Background scheduler for automatic health checks.
"""

import threading
import time


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

        self.interval = interval

        self.running = False

        self.thread = None



    def start(
        self,
        resources_provider
    ):
        """
        Start monitoring loop.
        """

        if self.running:
            return


        self.running = True


        self.thread = threading.Thread(
            target=self._worker,
            args=(
                resources_provider,
            ),
            daemon=True
        )


        self.thread.start()



    def stop(self):

        self.running = False



    def _worker(
        self,
        resources_provider
    ):

        while self.running:

            try:

                resources = resources_provider()


                self.service.check_resources(
                    resources
                )


            except Exception as e:

                print(
                    "[MONITORING ERROR]",
                    e
                )


            time.sleep(
                self.interval
            )