import os
import requests

from vk_api.bot_longpoll import VkBotEvent, VkBotEventType, DotDict
from vk_api.utils import get_random_id
from FusionBotMODULES import Fusion, ModuleManager


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


def recognize_audio(audio_attachment):
    url = audio_attachment["audio_message"]["link_ogg"]
    file = requests.get(url, allow_redirects=True)
    response = requests.post("https://stt.api.cloud.yandex.net/speech/v1/stt:recognize", data=file.content, headers={
        'Authorization': 'Api-Key ' + os.environ.get("yandex_api_token"),
    })
    code = int(response.status_code)
    if code == 200:
        return response.json()["result"]
    else:
        return response.json()


class Module(ModuleManager.Module):
    name = "SpeechRecognition"
    description = "Модуль распознавания голосовых сообщений"

    def run(self, client: Fusion):
        class RecognizeCommand(ModuleManager.Command):
            name = "recognize"
            description = "Распознать пересланное голосовое сообщение"
            args = "<пересланное голосовое сообщение>"

            def run(self, event: VkBotEvent, args, keys):
                client.get_api().messages.setActivity(type="typing", peer_id=event.obj.peer_id)
                audio_attachment = find_audio_in_fwd_messages(event.obj)
                if not audio_attachment:
                    return False
                res = recognize_audio(audio_attachment)
                text = None
                if type(res) == dict:
                    error = res
                    text = "Произошла неизвестная ошибка.\n\nКод:%s\nОписание:%s" % (
                        error["error_code"], error["error_message"]
                    )
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
                    res = recognize_audio(attachment)
                    text = None
                    if type(res) == dict:
                        error = res
                        text = "Произошла неизвестная ошибка.\n\nКод:%s\nОписание:%s" % (
                            error["error_code"], error["error_message"])
                    elif type(res) == str:
                        text = "Распознано голосовое сообщение:\n\n%s" % res
                    client.get_api().messages.send(
                        message=text,
                        peer_id=event.obj.peer_id,
                        random_id=get_random_id(),
                        reply_to=event.obj.id,
                    )
