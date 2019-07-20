import re
import time
import traceback
import os
import math

from os import path, environ
from requests import ReadTimeout
from pyotp import TOTP
from vk_api.bot_longpoll import VkBotEventType, VkBotLongPoll, VkBotEvent, DotDict
from vk_api.utils import get_random_id
from FusionBotMODULES import ModuleManager, Logger, Fusion, AccessDeniedException
from termcolor import colored

####################################

vk_token = environ.get("fusion_token")
group_id = environ.get("fusion_id")
totp = TOTP(environ.get("fusion_TOTP_key"))
args_regex = re.compile(r"(.*?)=(.+)")
start_time = time.time()
api_version = "5.101"


####################################


def process_mentions(_event_0: VkBotEvent):
    if _event_0.type in [VkBotEventType.MESSAGE_NEW, VkBotEventType.MESSAGE_EDIT, VkBotEventType.MESSAGE_REPLY]:
        _event_0.obj.mentions = {}
        _event_0.obj.raw_text = _event_0.obj.text
        for (user_id, mention_name) in client.module_manager.mention_regex.findall(_event_0.obj.text):
            _event_0.obj.mentions[user_id] = mention_name
        _event_0.obj.text = client.module_manager.mention_regex.sub(r"<@\1>", _event_0.obj.text)


def parse(raw):
    _args_0 = []
    _keys_0 = DotDict({})
    for elem in raw:
        if elem.startswith("—"):
            elem = elem[1:]
            _key_0, _value_0 = elem, True
            if ~elem.find("="):
                res = args_regex.search(elem)
                _key_0 = res.group(1)
                _value_0 = res.group(2)
            _keys_0[_key_0] = _value_0
        elif elem.startswith("-"):
            for char in elem[1:]:
                _keys_0[char] = True
        else:
            _args_0.append(elem)
    return _args_0, _keys_0


class FixedVkBotLongpoll(VkBotLongPoll):  # fix ReadTimeout exception
    logger = Logger(thread="Longpoll")

    def listen(self):
        while True:
            try:
                for _event in self.check():
                    yield _event
            except ReadTimeout:
                pass
            except Exception as err:
                self.logger.log(3, str(err))


client: Fusion = Fusion(token=vk_token, api_version=api_version)
if not path.isdir(client.MODULES_DIR):
    os.mkdir(client.MODULES_DIR)
logger = Logger()
logger.log(2, "Starting %s bot with %s %s" % (colored("Fusion", "magenta"),
                                              colored("VK Bot API", "blue"),
                                              colored("v" + api_version, "green")))
vk_api = client.get_api()
longpoll = FixedVkBotLongpoll(vk=client, group_id=group_id)
logger.log(2, "Loading modules")
client.load_modules()
logger.log(2, "Loading params")
client.load_params()
logger.log(2, "Running modules...")
client.run_modules()  # client)
print("")
logger.log(2, "INIT FINISHED! (took %ss)" % math.floor(time.time() - start_time))
logger.log(2, "Loaded Modules: %s" % len(client.module_manager.modules))
logger.log(2, "Loaded Commands: %s" % len(client.module_manager.commands))
logger.log(2, "Loaded Params: %s" % len(client.module_manager.params))
print("")

for event in longpoll.listen():
    process_mentions(event)
    for _, mod in list(client.module_manager.modules.items()):
        try:
            mod.on_event(client, event)
        except Exception as e:
            logger.log(4, "Exception in module %s: %s" % (mod.name, type(e).__name__))
            logger.log(4, traceback.format_exc())
    if event.type == VkBotEventType.MESSAGE_NEW:
        if event.obj.text.startswith(client.cmd_prefix):
            logger.log(1, "Обрабатываю команду %s из %s от %s" % (event.obj.text, event.obj.peer_id, event.obj.from_id))
            args = event.obj.text.split()
            cmd = args.pop(0)[len(client.cmd_prefix):].lower()
            if cmd not in client.module_manager.commands:
                logger.log(1, "Команда не найдена.")
                vk_api.messages.send(
                    peer_id=event.obj.peer_id,
                    message="Команда не найдена!",
                    random_id=get_random_id()
                )
                continue
            command: ModuleManager.Command = client.module_manager.commands[cmd]

            if not client.module_manager.check_guild(command.module, event.obj.peer_id):
                logger.log(1, "Команда недоступна в данном диалоге")
                vk_api.messages.send(
                    peer_id=event.obj.peer_id,
                    message="Команда не найдена!",
                    random_id=get_random_id()
                )
                continue

            args, keys = parse(args)

            pass_user = False
            try:
                otp_key = str(keys["otp"])
            except KeyError:
                pass
            else:
                if totp.verify(otp_key):
                    pass_user = True

            if not pass_user and not client.module_manager.has_permissions(command, event.obj.from_id) and \
                    (not command.no_args_pass or args):
                logger.log(1, "Нет прав.")
                vk_api.messages.send(
                    peer_id=event.obj.peer_id,
                    message="У вас недостаточно прав для выполнения данной команды.",
                    random_id=get_random_id()
                )
                continue
            try:
                ok = command.run(event, args, keys)
            except AccessDeniedException:
                vk_api.messages.send(
                    peer_id=event.obj.peer_id,
                    message="У вас недостаточно прав для выполнения данной команды.",
                    random_id=get_random_id()
                )
            except Exception as e:
                vk_api.messages.send(
                    peer_id=event.obj.peer_id,
                    message="⚠️ Криворукий уебан, у тебя ошибка! ⚠️\n\n%s" % traceback.format_exc(),
                    random_id=get_random_id()
                )
                logger.log(4, str(e))
            else:
                if not ok:
                    keys_user = []
                    for key in command.keys:
                        keys_user.append("[--%s]" % key)
                    text = "Недостаточно аргументов!\n %s%s %s %s" % (client.cmd_prefix, command.name,
                                                                      command.args, " ".join(keys_user))
                    vk_api.messages.send(peer_id=event.obj.peer_id, message=text, random_id=get_random_id())
                    logger.log(1, "Недостаточно аргументов.")
