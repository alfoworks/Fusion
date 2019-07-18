import time
import traceback
import os
import math

from os import path, environ
from requests import ReadTimeout
from pyotp import TOTP
from vk_api.bot_longpoll import VkBotEventType, VkBotLongPoll
from vk_api.utils import get_random_id
from FusionBotMODULES import ModuleManager, Logger, Fusion

####################################

vk_token = environ.get("fusion_token")
group_id = environ.get("fusion_id")
totp = TOTP(environ.get("fusion_TOTP_key"))

####################################

start_time = time.time()


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


client: Fusion = Fusion(token=vk_token)
if not path.isdir(client.MODULES_DIR):
    os.mkdir(client.MODULES_DIR)
logger = Logger()
logger.log(2, "Starting")
vk_api = client.get_api()
longpoll = FixedVkBotLongpoll(vk=client, group_id=group_id)
logger.log(2, "Loading modules")
client.load_modules()
logger.log(2, "Loading params")
client.load_params()
logger.log(2, "Running modules...")
client.run_modules(client)
print("")
logger.log(2, "INIT FINISHED! (took %ss)" % math.floor(time.time() - start_time))
logger.log(2, "Loaded Modules: %s" % len(client.module_manager.modules))
logger.log(2, "Loaded Commands: %s" % len(client.module_manager.commands))
logger.log(2, "Loaded Params: %s" % len(client.module_manager.params))
print("")
for event in longpoll.listen():
    for _, mod in list(client.module_manager.modules.items()):
        try:
            mod.on_event(client, event)
        except Exception as e:
            logger.log(4, "Exception in module %s: %s" % (mod.name, ". ".join(list(e.args))))
            logger.log(4, str(e))
    if event.type == VkBotEventType.MESSAGE_NEW:
        if not event.obj.text.startswith(client.cmd_prefix):
            continue
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

        # ARG PARSE #

        keys = []
        for arg in args:
            if arg.startswith("—") and len(arg) > 2 and arg not in keys:  # вк заменяет -- на —. Фикс не повлияет на UX
                keys.append(arg)
        otp_pwd_index = None
        for i, key in enumerate(keys):
            args.remove(key)
            keys[i] = key[1:]
            if "otp" in keys[i]:
                otp_pwd_index = i

        # ========= #

        pass_user = False
        if otp_pwd_index is not None:
            key: str = keys[otp_pwd_index]
            del keys[otp_pwd_index]
            [_key, value] = key.split("=")
            if _key == "otp":
                if totp.verify(value):
                    pass_user = True
        if not client.module_manager.check_guild(command.module, event.obj.peer_id):
            logger.log(1, "Команда недоступна в данном диалоге")
            vk_api.messages.send(
                peer_id=event.obj.peer_id,
                message="Команда не найдена!",
                random_id=get_random_id()
            )
            continue
        if not pass_user:
            if not client.module_manager.has_permissions(command, event.obj.from_id):
                if not command.no_args_pass or args:
                    logger.log(1, "Нет прав.")
                    vk_api.messages.send(
                        peer_id=event.obj.peer_id,
                        message="У вас недостаточно прав для выполнения данной команды.",
                        random_id=get_random_id()
                    )
                    continue
        try:
            ok = command.run(event, args, keys)
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
