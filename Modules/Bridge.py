import os
import uuid

from vk_api.bot_longpoll import VkBotEvent
from vk_api.utils import get_random_id
from FusionBotMODULES import Fusion, ModuleManager
from TGInterface import TGBot, DotDict


class List(list):
    def __getstate__(self):
        return self.__dict__

    def __setstate__(self, d):
        self.__dict__.update(d)

    def filter(self, **kwargs):
        def filter_function(elem: dict):
            for _key in kwargs:
                no_name = _key.split("__")
                key = no_name[0]
                if key not in elem:
                    return False
                modifier = None if no_name[-1] == no_name[0] else no_name[1]
                if not modifier:
                    if elem[key] != kwargs[_key]:
                        return False
                else:
                    if modifier == "iexact":
                        if type(elem[key]) == str:
                            if elem[key].lower() != kwargs[_key].lower():
                                return False
                        else:
                            return False
            return True

        return List(filter(filter_function, self))


class Module(ModuleManager.Module):
    name = "Telegram Bridge"
    description = "Мост между Telegram и ВКонтакте"
    telegram = None
    bridge_username = None
    queue = []

    async def cycle(self):
        if self.queue:
            text = ""
            for message in self.queue:


    def run(self, client: Fusion):
        self.telegram = TGBot(token=os.getenv("bridge_token"))
        self.bridge_username = self.telegram.get_api().getMe()["username"]
        client.module_manager.add_param("tg_binds", List())

        class BindCommand(ModuleManager.Command):
            name = "tg_bind"
            description = "Привязать чат к чату в Telegram"

            def run(self, event: VkBotEvent, args, keys):
                peer_id = event.obj.peer_id
                if client.module_manager.params["tg_binds"].filter(vk_id=peer_id):
                    client.get_api().messages.send(
                        peer_id=peer_id,
                        message="Данный чат уже имеет привязку к чату Telegram или его необходимо привязать к боту",
                        random_id=get_random_id()
                    )
                    return True
                peer_uuid = uuid.uuid4()
                while client.module_manager.params["tg_binds"].filter(uuid=peer_uuid):
                    peer_uuid = uuid.uuid4()
                client.module_manager.params["tg_binds"].append(DotDict({
                    "vk_id": peer_id,
                    "uuid": peer_uuid,
                    "telegram_id": None,
                }))
                client.module_manager.save_params()
                client.get_api().messages.send(
                    peer_id=peer_id,
                    message="Теперь вам нужно перейти к боту t.me/%s и выполнить команду в необходимом вам "
                            "чате:\n\n/start %s\n\nЛибо перейти по ссылке, что бы бот писал напрямую вам: "
                            "t.me/%s?start=%s" % (
                                self.module.bridge_username,
                                peer_uuid.hex,
                                self.module.bridge_username,
                                peer_uuid.hex
                            ),
                    random_id=get_random_id(),
                )
                return True

        client.module_manager.add_command(BindCommand(), self)


