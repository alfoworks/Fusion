from threading import Thread
from time import sleep

from FusionBotMODULES import ModuleManager


class ScheduleThread(Thread):
    module_manager: ModuleManager = None

    def __init__(self, module_manager):
        super().__init__(name="Schedule", daemon=True)
        self.module_manager = module_manager

    def run(self):
        while True:
            for scheduler in list(self.module_manager.schedulers.values()):
                scheduler.run_pending()  # Если кто-нибудь будет трогать планировщики - боту пизда


threads: list[Thread] = []


def deploy(module_manager):
    # Сюда все потоки, которые нужно ЕДИНОРАЗОВО запустить. Они должны быть демонами.
    # Любая модификация приветствуется, кроме модульности этой хуйни. Для этого есть scheduler.timer с delay=0
    threads.append(ScheduleThread(module_manager))
