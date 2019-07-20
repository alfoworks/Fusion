import os
from os import path

import requests
from vk_api.bot_longpoll import VkBotEvent, VkBotEventType
from vk_api.utils import get_random_id
from FusionBotMODULES import Fusion, ModuleManager
from wit import Wit


class Module(ModuleManager.Module):
    name = "SpeechRecognize"
    description = "Модуль распознавания голосовых сообщений"
    GUILD_LOCK = []
    wit = None

    def run(self, client: Fusion):
        self.wit = Wit(os.getenv("fusion_wit_token"))

    def on_event(self, client: Fusion, event: VkBotEvent):
        if event.type == VkBotEventType.MESSAGE_NEW:
            if event.obj.attachments:
                attachment = event.obj.attachments[0]
                if attachment["type"] == "audio_message":
                    url = attachment["audio_message"]["link_mp3"]
                    res = requests.get(url, allow_redirects=True)
                    file_name = "voice_messages/%s_%s_%s_%s.mp3" % (
                        event.obj.peer_id,
                        event.obj.from_id,
                        event.obj.conversation_message_id,
                        event.obj.date,
                    )
                    if not path.isdir("voice_messages"):
                        os.mkdir("voice_messages")
                    open(file_name, 'wb').write(res.content)
                    resp = None
                    with open(file_name, "rb") as f:
                        resp = self.wit.post_speech(f.read(), "mpeg")
                    os.remove(file_name)
                    client.get_api().messages.send(
                        message="Распознано голосовое сообщение:\n\n%s" % resp["_text"],
                        peer_id=event.obj.peer_id,
                        random_id=get_random_id(),
                        reply_to=event.obj.id,
                    )
