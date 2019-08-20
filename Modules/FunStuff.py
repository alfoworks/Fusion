from vk_api.bot_longpoll import VkBotEvent
from vk_api.utils import get_random_id
from FusionBotMODULES import Fusion, ModuleManager


class Module(ModuleManager.Module):
    name = "FunStuff"
    description = "Модуль, который добавляет бесполезные, но интересные вещи."

    def run(self, client: Fusion, registry):
        class ShrugCommand(ModuleManager.Command):
            name = "shrug"
            description = "¯\_(ツ)_/¯"

            def run(self, event: VkBotEvent, args, keys):
                client.get_api().messages.send(
                    message="¯\_(ツ)_/¯",
                    peer_id=event.obj.peer_id,
                    random_id=get_random_id()
                )
                return True

        client.module_manager.add_command(ShrugCommand(), self)
