import json
import os
import requests

from vk_api.bot_longpoll import VkBotEvent
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.utils import get_random_id
from FusionBotMODULES import Fusion, ModuleManager


def process_natural_language(req, token):
    json_req = {
        "query": req,
        "lang": "ru",
        "session_id": "fusion",
        "v": "20170712",
    }
    headers = {'Authorization': 'Bearer {0}'.format(token)}
    body = json.dumps(json_req)
    url = "https://api.dialogflow.com/v1/query"
    resp = requests.post(url, data=body, headers=headers)
    return resp.json()


class Module(ModuleManager.Module):
    name = "TestModule"
    description = "Тестовый модуль"
    GUILD_LOCK = []
    # wit = None
    dialogflow_token = None

    def run(self, client: Fusion):
        # self.wit = Wit(os.getenv("fusion_wit_token"))

        class KeyboardCommand(ModuleManager.Command):
            name = "keytest"
            description = "Тестирование клавиатуры вк"

            def run(self, event: VkBotEvent, args, keys):
                keyboard: VkKeyboard = VkKeyboard(one_time=True)
                keyboard.add_button(label="Test", color=VkKeyboardColor.PRIMARY)
                keyboard.add_button(label="Test2", color=VkKeyboardColor.DEFAULT,
                                    payload=client.create_payload("test2", self.module)
                                    )
                client.get_api().messages.send(keyboard=keyboard.get_keyboard(),
                                               peer_id=event.obj.peer_id,
                                               random_id=get_random_id(),
                                               message="Тест клавиатуры"
                                               )
                return True

        client.module_manager.add_command(KeyboardCommand(), self)

    def on_payload(self, client: Fusion, event: VkBotEvent, payload):
        client.get_api().messages.send(peer_id=event.obj.peer_id,
                                       random_id=get_random_id(),
                                       message="Получен payload: %s" % json.dumps(payload)
                                       )
