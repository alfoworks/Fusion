import os
from os import path

import requests
from vk_api.bot_longpoll import VkBotEvent, VkBotEventType, DotDict
from vk_api.utils import get_random_id
from FusionBotMODULES import Fusion, ModuleManager
from wit import Wit, BadRequestError

class Module(ModuleManager.Module):
    name = "SpeechRecognize"
    description = "Модуль распознавания голосовых сообщений"
    GUILD_LOCK = []
    wit = None

    def run(self, client: Fusion):
        self.wit = Wit(os.getenv("fusion_wit_token"))

    def on_event(self, client: Fusion, event: VkBotEvent):
        if event.type == VkBotEventType.MESSAGE_NEW:
            msg = event.obj
            if msg.reply_message:
                msg = DotDict(msg.reply_message)
            elif msg.fwd_messages:
                msg = DotDict(msg.fwd_messages[0])
            if msg.attachments:
                attachment = msg.attachments[0]
                if attachment["type"] == "audio_message":
                    url = attachment["audio_message"]["link_mp3"]
                    res = requests.get(url, allow_redirects=True)
                    try:
                        resp = self.wit.post_speech(res.content, "mpeg")
                        text = "Распознано голосовое сообщение:\n\n%s" % resp["_text"]
                    except BadRequestError as e:
                        text = "Произошла ошибка при распознавании.\n\n%s\n\nЧаще всего это происходит по вине " \
                               "пользователя." % str(e),

                    client.get_api().messages.send(
                        message=text,
                        peer_id=event.obj.peer_id,
                        random_id=get_random_id(),
                        reply_to=event.obj.id,
                    )
