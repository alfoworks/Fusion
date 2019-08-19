import json
import os
import pickle
import re
import traceback
import importlib

from termcolor import colored
from datetime import datetime
from vk_api import VkApi
from vk_api.utils import get_random_id
from vk_api.bot_longpoll import VkBotEvent
from schedule import Scheduler

_native_mention_regex_0 = r"\[id(\d+)\|(.+?)\]"
_mention_regex = r"<@(\d+)>"


# noinspection PyUnusedLocal
class Logger:
    thread = "Main"
    app = "Core"
    log_levels = [
        ["Verbose", None, None, None],
        ["Debug", "green", None, None],
        ["Info", "green", None, None],
        ["Warn", "yellow", None, None],
        ["Error", "red", None, None],
        ["FATAL", "grey", "on_red", None],
        ["Silent", None, None, None],
    ]

    @staticmethod
    def get_time():
        iso = datetime.now().isoformat()
        return iso[11:19]

    def __init__(self, thread="Main", app="Core"):
        self.thread = thread
        self.app = app

    def raw_log(self, level: int, text: str):
        log_level = self.log_levels[level]
        _text = "[%s] [%s] [%s]: " % (
            colored(self.get_time(), "magenta"),
            colored(self.thread + " thread/" + log_level[0], log_level[1], log_level[2], log_level[3]),
            self.app)
        if level == 5:
            _text += colored(text, "red")
        else:
            _text += text
        print(_text)

    def log(self, level: int, text: str, *args):
        text = text % tuple(args)
        for line in text.splitlines():
            self.raw_log(level, line)

    def debug(self, msg, *args, **kwargs):
        self.log(1, msg, *args)

    def info(self, msg, *args, **kwargs):
        self.log(2, msg, *args)

    def warn(self, msg, *args, **kwargs):
        self.log(3, msg, *args)

    def error(self, msg, *args, **kwargs):
        self.log(4, msg, *args)

    def fatal(self, msg, *args, **kwargs):
        self.log(5, msg, *args)

    warning = warn
    exception = error
    critical = fatal


class AccessDeniedException(Exception):
    def __init__(self):
        super().__init__("AccessDenied")


class ModuleManager:
    modules = dict()
    params = dict()
    schedulers = dict()
    commands = dict()
    PARAMS_FILE = "botData.pkl"
    native_mention_regex = re.compile(_native_mention_regex_0)
    mention_regex = re.compile(_mention_regex)
    logger = Logger(app="Module Manager")

    class Module:
        name = "Sample module"
        description = "Sample description"
        GUILD_LOCK = {}

        def run(self, client: VkApi):
            pass

        def on_event(self, client: VkApi, event: VkBotEvent):
            pass

        def on_payload(self, client: VkApi, event: VkBotEvent, payload):
            pass

    class Command:
        name = "sample_command"
        description = "Sample description"
        args = ""
        keys = []
        permissions = []
        no_args_pass = False
        module = None

        def run(self, event: VkBotEvent, args, keys):
            pass

    def has_permissions(self, command: Command, user_id) -> bool:
        if command.permissions:
            if str(user_id) in self.params["permissions"]:
                user_perms = self.params["permissions"][str(user_id)]
                req_perms = command.permissions
                for perm in req_perms:
                    if perm not in user_perms:
                        return False
                return True
            return False
        return True

    def has_permission(self, permission, user_id) -> bool:
        if str(user_id) in self.params["permissions"]:
            if permission in self.params["permissions"][str(user_id)]:
                return True
        return False

    @staticmethod
    def check_guild(module: Module, peer_id):
        if module.GUILD_LOCK:
            if peer_id in module.GUILD_LOCK:
                return True
            return False
        return True

    def add_module(self, module: Module):
        if module.name in self.modules:
            raise ValueError("A module with name \"%s\" already exists." % module.name)

        self.modules[module.name] = module

    def unload_module(self, module_name: str):
        if module_name not in self.modules:
            raise ValueError("Can't remove a module that doesn't exist (%s)." % module_name)

        self.logger.log(2, "Unloading module \"%s\"..." % module_name)

        for _, command in list(self.commands.items()):
            if command.module.name == module_name:
                self.remove_command(command.name)
                self.logger.log(1, "Removed command \"%s\" from module \"%s\"." % (command.name, module_name))

        if module_name in self.schedulers:
            del self.schedulers[module_name]
            self.logger.log(1, "Cancelled scheduler from module \"%s\"." % module_name)

        del self.modules[module_name]

    def add_command(self, command: Command, module: Module):
        command.module = module
        self.commands[command.name] = command

    def remove_command(self, command_name: str):
        if command_name not in self.commands:
            raise ValueError("Can't remove a module that doesn't exist (%s)." % command_name)

        del self.commands[command_name]

    def save_params(self):
        self.logger.log(2, "Saving params to %s..." % self.PARAMS_FILE)
        with open(self.PARAMS_FILE, "wb") as f:
            pickle.dump(self.params, f)

    def add_param(self, key, value_default):
        if key not in self.params:
            self.params[key] = value_default
            self.save_params()

    def get_scheduler(self, module) -> Scheduler:
        if module.name not in self.schedulers:
            self.schedulers[module.name] = Scheduler()
        return self.schedulers[module.name]


class Fusion(VkApi):
    module_manager = ModuleManager()
    MODULES_DIR = "Modules"
    cmd_prefix = "/"
    modules_cache = dict()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = Logger(app="VkApi")

    def load_modules(self):
        for file in os.listdir(self.MODULES_DIR):
            if file.endswith(".py"):
                if file in self.modules_cache:
                    importlib.reload(self.modules_cache[file])
                module = __import__("%s.%s" % (self.MODULES_DIR, file[:-3]), globals(), locals(),
                                    fromlist=["Module"])
                self.modules_cache[file] = module
                do_load = True
                if hasattr(module, "load_module"):
                    do_load = module.load_module
                if do_load and hasattr(module, "Module"):
                    instance = module.Module()
                    self.module_manager.add_module(instance)
                    self.module_manager.logger.log(2, "Loaded module \"%s\"" % instance.name)
        self.module_manager.add_module(BaseModule())

    def run_modules(self):
        for key_1 in list(self.module_manager.modules):
            module = self.module_manager.modules[key_1]
            self.module_manager.logger.log(2, "Running module \"%s\"" % module.name)
            try:
                module.run(self)
            except Exception:
                self.module_manager.logger.log(5, traceback.format_exc())
                exit(1)

    def load_params(self):
        if not os.path.isfile(self.module_manager.PARAMS_FILE):
            self.module_manager.save_params()
        else:
            with open(self.module_manager.PARAMS_FILE, "rb") as f:
                self.module_manager.params = pickle.load(f)

    def schedule_init(self):
        for module in self.module_manager.modules:
            self.module_manager.schedulers[module] = Scheduler()

    @staticmethod
    def create_payload(payload, module: ModuleManager.Module):
        return json.dumps({
            "module": module.name,
            "payload": payload,
        })


class BaseModule(ModuleManager.Module):
    name = "BaseModule"
    description = "Встроенный модуль с базовыми функциями"

    @staticmethod
    def parse_value(value, value_type):
        if value_type == int:
            return int(value)
        elif value_type == float:
            return float(value)
        elif value_type == bool:
            if value.lower() == "true" or value.lower() == "yes":
                return True
            elif value.lower() == "false" or value.lower() == "no":
                return False
        elif value_type == str:
            return value
        else:
            return None

    def run(self, client: Fusion):
        logger = Logger(app="BaseModule")

        class ModulesCommand(ModuleManager.Command):
            name = "modules"
            description = "Информация о модулях и управление ими"
            keys = ["reload"]

            def run(self, event: VkBotEvent, args, keys):
                if "reload" in keys:
                    if not client.module_manager.has_permission("administrator", event.obj.from_id):
                        raise AccessDeniedException()
                    client.get_api().messages.send(
                        peer_id=event.obj.peer_id,
                        message="Перезагрузка модулей..",
                        random_id=get_random_id(),
                    )
                    logger.log(2, "Reloading modules")
                    for name, _ in list(client.module_manager.modules.items()):
                        client.module_manager.unload_module(name)
                    client.load_modules()
                    client.run_modules()  # client)
                    client.get_api().messages.send(
                        peer_id=event.obj.peer_id,
                        message="Модули перезагружены.",
                        random_id=get_random_id(),
                    )
                    return True
                text = ""
                counter = 0
                for _, mod in list(client.module_manager.modules.items()):
                    if client.module_manager.check_guild(mod, event.obj.peer_id):
                        text = text + "%s: %s\n" % (mod.name, mod.description)
                        counter += 1
                text = "Всего модулей: %s\n\n" % counter + text
                client.get_api().messages.send(
                    peer_id=event.obj.peer_id,
                    message=text,
                    random_id=get_random_id()
                )
                return True

        client.module_manager.add_command(ModulesCommand(), self)

        class CmdsCommand(ModuleManager.Command):
            name = "cmds"
            description = "Список команд, их аргументы и описание"

            def run(self, event: VkBotEvent, args, keys):
                text1 = "Список команд:\n\n"
                for _, command in client.module_manager.commands.items():
                    if not client.module_manager.check_guild(command.module, event.obj.peer_id):
                        continue
                    if not client.module_manager.has_permissions(command, event.obj.from_id):
                        continue
                    keys_1 = []
                    for key_1 in command.keys:
                        keys_1.append("[--%s]" % key_1)
                    text1 = text1 + "%s%s %s %s\n" % (client.cmd_prefix, command.name, command.args,
                                                      " ".join(keys_1))
                    text1 = text1 + " - " + command.description + "\n\n"
                client.get_api().messages.send(
                    peer_id=event.obj.peer_id,
                    message=text1,
                    random_id=get_random_id()
                )
                return True

        client.module_manager.add_command(CmdsCommand(), self)

        class ParamsCommand(ModuleManager.Command):
            name = "params"
            description = "Список параметров и управление ими"
            args = "[set] <key> <value>"
            permissions = ["administrator"]

            def run(self, event: VkBotEvent, args, keys):
                if len(args) >= 3 and args[0] == "set":
                    if args[1] not in client.module_manager.params:
                        client.get_api().messages.send(peer_id=event.obj.peer_id,
                                                       message="Параметр с таким именем не найден.",
                                                       random_id=get_random_id()
                                                       )

                        return True

                    param = client.module_manager.params[args[1]]
                    try:
                        val = BaseModule.parse_value(" ".join(args[2:]), type(param))
                    except ValueError:
                        client.get_api().messages.send(
                            peer_id=event.obj.peer_id,
                            message="Неподходящее для типа \"%s\" значение." % type(param).__name__,
                            random_id=get_random_id()
                        )
                        return True
                    if val is None:
                        client.get_api().messages.send(
                            peer_id=event.obj.peer_id,
                            message="Параметр \"%s\" нелья изменить с помощью команды." % args[1],
                            random_id=get_random_id()
                        )
                    client.module_manager.params[args[1]] = val
                    client.module_manager.save_params()
                    client.get_api().messages.send(
                        peer_id=event.obj.peer_id,
                        message="Параметры изменены и сохранены.",
                        random_id=get_random_id()
                    )
                    return True
                text = "Список параметров:\n\n"
                for k, v in client.module_manager.params.items():
                    text = text + "%s [%s]: %s\n" % (k, type(v).__name__, v)
                client.get_api().messages.send(
                    peer_id=event.obj.peer_id,
                    message=text,
                    random_id=get_random_id()
                )
                return True

        client.module_manager.add_command(ParamsCommand(), self)

        class PermissionsCommand(ModuleManager.Command):
            name = "permissions"
            description = "Управление правами доступа"
            args = "[add/remove] <permission> <mention>"
            permissions = ["administrator"]

            def run(self, event: VkBotEvent, args, keys):
                if not event.obj.mentions:
                    return False
                text: str = ""
                if args[0] == "add":
                    for user_id in event.obj.mentions.keys():
                        if user_id not in client.module_manager.params["permissions"]:
                            client.module_manager.params["permissions"][user_id] = []
                        if args[1] not in client.module_manager.params["permissions"][user_id]:
                            client.module_manager.params["permissions"][user_id].append(args[1])
                            text += "Успешно добавлено разрешение %s пользователю с id %s.\n" % (args[1], user_id)
                        else:
                            text += "У пользователя с id %s уже есть разрешение %s.\n" % (user_id, args[1])
                elif args[0] == "remove":
                    for user_id in event.obj.mentions.keys():
                        if user_id in client.module_manager.params["permissions"]:
                            try:
                                client.module_manager.params["permissions"][user_id].remove(args[1])
                            except ValueError:
                                text += "У пользователя %s нет разрешения %s.\n" % (user_id, args[1])
                            else:
                                text += "Успешно удалено разрешение %s у пользователя с id %s.\n" % (args[1], user_id)
                        else:
                            text += "У пользователя %s нет ни одного разрешения.\n" % user_id
                else:
                    return False
                client.get_api().messages.send(
                    peer_id=event.obj.peer_id,
                    message=text,
                    random_id=get_random_id(),
                )
                client.module_manager.save_params()
                return True

        client.module_manager.add_param("permissions", {})
        client.module_manager.add_command(PermissionsCommand(), self)
