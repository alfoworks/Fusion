import json

from vk_api.bot_longpoll import VkBotEvent
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.utils import get_random_id

from FusionBotMODULES import Fusion, ModuleManager


def render_keyboard(key_list, defined_keys, page=0):
    if defined_keys is None:
        defined_keys = []
    keys_len = len(key_list)
    start_index = (page - 1) * 36
    end_index = start_index + 35
    if keys_len < start_index:
        return "[]"
    elif keys_len < end_index:
        end_index = keys_len - 1
    keyboard: VkKeyboard = VkKeyboard(one_time=True)
    keyboard.lines.pop()
    for index, button in enumerate(key_list):
        if start_index <= index <= end_index:
            if index % 4 == 0:
                keyboard.add_line()
            keyboard.add_button(**button)
    keyboard.add_line()
    for button in defined_keys:
        keyboard.add_button(**button)
    return json.dumps(keyboard.keyboard)


def send_keyboard(client, module, event, page=1):
    keys = []
    for item in range(70):
        keys.append({
            "label": "Кнопка %s" % item,
            "payload": client.create_payload("button%s" % item, module),
        })
    defined_keys = [
        {
            "label": "Отмена",
        },
        {
            "label": "Следующая страница",
            "payload": client.create_payload({
                "act": "next_page",
                "page": page+1
            }, module)
        }
    ]
    rendered = render_keyboard(keys, defined_keys=defined_keys, page=page)
    client.get_api().messages.send(keyboard=rendered,
                                   peer_id=event.obj.peer_id,
                                   random_id=get_random_id(),
                                   message="Тест клавиатуры"
                                   )

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
                send_keyboard(client, self.module, event)
                return True

        client.module_manager.add_command(KeyboardCommand(), self)

    def on_payload(self, client: Fusion, event: VkBotEvent, payload):
        client.get_api().messages.send(peer_id=event.obj.peer_id,
                                       random_id=get_random_id(),
                                       message="Получен payload: %s" % json.dumps(payload)
                                       )
        if "act" in payload:
            act = payload["act"]
            if act == "next_page":
                send_keyboard(client, self, event, page=payload["page"])
