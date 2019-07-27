import json

from vk_api.bot_longpoll import VkBotEvent
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.utils import get_random_id

from FusionBotMODULES import Fusion, ModuleManager


def render_keyboard(key_list, module, page=0, rows=9, columns=4, one_time=True, submit=True):
    start_index = page * (rows * columns)
    end_index = start_index + (rows * columns)
    if len(key_list) < start_index:
        return "[]"
    elif len(key_list) < end_index:
        end_index = len(key_list)
    keyboard: VkKeyboard = VkKeyboard(one_time=one_time)
    keyboard.lines.pop()
    for index in range(start_index, end_index):
        if index % 4 == 0:
            keyboard.add_line()
        keyboard.add_button(**key_list[index])
    keyboard.add_line()
    if page != 0:
        keyboard.add_button("<< Пред.", payload=Fusion.create_payload({
            "act": "next_page",
            "page": page - 1,
        }, module))
    keyboard.add_button("Отмена", color=VkKeyboardColor.NEGATIVE, payload=Fusion.create_payload({
        "act": "cancel",
    }, module))
    if submit:
        keyboard.add_button("Отправить", color=VkKeyboardColor.POSITIVE, payload=Fusion.create_payload({
            "act": "submit",
        }, module))
    if len(key_list) > end_index:
        keyboard.add_button("След. >>", payload=Fusion.create_payload({
            "act": "next_page",
            "page": page + 1,
        }, module))
    return keyboard.get_keyboard()


class Module(ModuleManager.Module):
    name = "TestModule"
    description = "Тестовый модуль"
    GUILD_LOCK = []
    keys = []

    def run(self, client: Fusion):
        # self.wit = Wit(os.getenv("fusion_wit_token"))

        self.keys = []
        for elem in range(72):
            self.keys.append({
                "label": "Кнопка%s" % elem,
                "payload": client.create_payload("button%s" % elem, self)
            })

        class KeyboardCommand(ModuleManager.Command):
            name = "keytest"
            description = "Тестирование клавиатуры вк"

            def run(self, event: VkBotEvent, args, keys):
                client.get_api().messages.send(
                    keyboard=render_keyboard(
                        self.module.keys, self.module,
                    ),
                    peer_id=event.obj.peer_id,
                    random_id=get_random_id(),
                    message="Тест клавиатуры"
                )

                return True

        client.module_manager.add_command(KeyboardCommand(), self)

        class ReplyTestCommand(ModuleManager.Command):
            name = "replytest"
            description = "Тестирование ответа на сообщение"

            def run(self, event: VkBotEvent, args, keys):
                client.get_api().messages.send(
                    message="1234",
                    reply_to=event.obj.conversation_message_id,
                    random_id=get_random_id(),
                    peer_id=event.obj.peer_id
                )
                return True

        client.module_manager.add_command(ReplyTestCommand(), self)

        class TestCommand(ModuleManager.Command):
            name = "test"
            description = "Тесты-хуесты"

            def run(self, event: VkBotEvent, args, keys):
                a = client.get_api().messages.send(
                    message="1234",
                    random_id=get_random_id(),
                    peer_id=event.obj.peer_id
                )
                return True

        client.module_manager.add_command(TestCommand(), self)

    def on_payload(self, client: Fusion, event: VkBotEvent, payload):
        client.get_api().messages.send(peer_id=event.obj.peer_id,
                                       random_id=get_random_id(),
                                       message="Получен payload: %s" % json.dumps(payload)
                                       )
