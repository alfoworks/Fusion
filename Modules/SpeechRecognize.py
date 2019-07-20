import json
import os
from os import path

import requests
from vk_api.bot_longpoll import VkBotEvent, VkBotEventType, DotDict
from vk_api.utils import get_random_id
from FusionBotMODULES import Fusion, ModuleManager
from wit import Wit, BadRequestError


def find_audio_in_fwd_messages(msg):
    if msg.attachments:
        if msg.attachments[0]["type"] == "audio_message":
            return msg.attachments[0]
    if "reply_message" in msg:
        return find_audio_in_fwd_messages(DotDict(msg.reply_message))
    elif msg.fwd_messages:
        for message in msg.fwd_messages:
            res = find_audio_in_fwd_messages(DotDict(message))
            if res:
                return res


def recognize_audio(audio_attachment, wit_client):
    url = audio_attachment["audio_message"]["link_mp3"]
    res = requests.get(url, allow_redirects=True)
    try:
        resp = wit_client.post_speech(res.content, "mpeg")
        return resp["_text"]
    except BadRequestError as e:
        return json.loads(str(e))


class Module(ModuleManager.Module):
    name = "SpeechRecognize"
    description = "Модуль распознавания голосовых сообщений"
    GUILD_LOCK = []
    wit = None

    def run(self, client: Fusion):
        self.wit = Wit(os.getenv("fusion_wit_token"))
        wit = self.wit

        class RecognizeCommand(ModuleManager.Command):
            name = "recognize"
            description = "Распознать пересланное голосовое сообщение"
            args = "<пересланное голосовое сообщение>"

            def run(self, event: VkBotEvent, args, keys):
                client.get_api().messages.setActivity(type="typing", peer_id=event.obj.peer_id)
                audio_attachment = find_audio_in_fwd_messages(event.obj)
                if not audio_attachment:
                    return False
                res = recognize_audio(audio_attachment, wit)
                text = None
                if type(res) == dict:
                    error = res
                    if error["code"] == "timeout":
                        text = "Сообщение не может быть длиной более 20 секунд."
                    else:
                        text = "Произошла неизвестная ошибка.\n\nКод:%s\nОписание:%s" % (
                            error["code"], error["error"])
                elif type(res) == str:
                    text = "Распознано голосовое сообщение:\n\n%s" % res
                client.get_api().messages.send(
                    message=text,
                    peer_id=event.obj.peer_id,
                    random_id=get_random_id(),
                )
                return True
        client.module_manager.add_command(RecognizeCommand(), self)

    def on_event(self, client: Fusion, event: VkBotEvent):
        if event.type == VkBotEventType.MESSAGE_NEW:
            if event.obj.attachments:
                attachment = event.obj.attachments[0]
                if attachment["type"] == "audio_message":
                    client.get_api().messages.setActivity(type="typing", peer_id=event.obj.peer_id)
                    res = recognize_audio(attachment, self.wit)
                    text = None
                    if type(res) == dict:
                        error = res
                        if error["code"] == "timeout":
                            text = "Сообщение не может быть длиной более 20 секунд."
                        else:
                            text = "Произошла неизвестная ошибка.\n\nКод:%s\nОписание:%s" % (
                                error["code"], error["error"])
                    elif type(res) == str:
                        text = "Распознано голосовое сообщение:\n\n%s" % res
                    client.get_api().messages.send(
                        message=text,
                        peer_id=event.obj.peer_id,
                        random_id=get_random_id(),
                        reply_to=event.obj.id,
                    )
