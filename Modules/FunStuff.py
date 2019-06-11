from vk_api import VkApi
from vk_api.bot_longpoll import VkBotEvent
from vk_api.utils import get_random_id
import FusionBotMODULES


class Module(FusionBotMODULES.ModuleManager.Module):
    name = "FunStuff"
    description = "Модуль, который добавляет бесполезные, но интересные вещи."
    GUILD_LOCK = []

    def run(self, client: VkApi, module_manager: FusionBotMODULES.ModuleManager):
        class ShrugCommand(FusionBotMODULES.ModuleManager.Command):
            name = "shrug"
            description = "¯\_(ツ)_/¯"

            def run(self, event: VkBotEvent, args, keys):
                client.get_api().messages.send(
                    message="¯\_(ツ)_/¯",
                    peer_id=event.obj.peer_id,
                    random_id=get_random_id()
                )
                return True

        module_manager.add_command(ShrugCommand(), self)
