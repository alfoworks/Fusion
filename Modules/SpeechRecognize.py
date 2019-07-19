import os
from os import path

import requests
from vk_api.bot_longpoll import VkBotEvent, VkBotEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.utils import get_random_id
from FusionBotMODULES import Fusion, ModuleManager
from wit import Wit


class Module(ModuleManager.Module):
    name = "SpeechRecognize"
    description = "Модуль распознавания голосовых сообщений"
    GUILD_LOCK = []

    def run(self, client: Fusion):
        pass
        # class KeyboardCommand(ModuleManager.Command):
        #     name = "keytest"
        #     description = "¯\_(ツ)_/¯"
        #
        #     def run(self, event: VkBotEvent, args, keys):
        #         keyboard: VkKeyboard = VkKeyboard(one_time=True)
        #         keyboard.add_button(label="Test", color=VkKeyboardColor.PRIMARY)
        #         keyboard.add_button(label="Test2", color=VkKeyboardColor.DEFAULT, payload="1234")
        #         client.get_api().messages.send(keyboard=keyboard.get_keyboard(),
        #                                        peer_id=event.obj.peer_id,
        #                                        random_id=get_random_id(),
        #                                        message="Тест клавиатуры"
        #                                        )
        #         return True
        #
        # client.module_manager.add_command(KeyboardCommand(), self)

    def on_event(self, client: Fusion, event: VkBotEvent):
        print("speechrecognize module")
        if event.type == VkBotEventType.MESSAGE_NEW:
            if event.obj.attachments:
                attachment = event.obj.attachments[0]
                if attachment["type"] == "audio_message":
                    url = attachment["audio_message"]["link_mp3"]
                    res = requests.get(url, allow_redirects=True)
                    file_name = "%s_%s_%s_%s.mp3" % (
                        event.obj.peer_id,
                        event.obj.from_id,
                        event.obj.conversation_message_id,
                        event.obj.date,
                    )
                    if not path.isdir("voice_messages"):
                        os.mkdir("voice_messages")
                    open("voice_messages/" + file_name, 'wb').write(res.content)
