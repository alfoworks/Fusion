import random
import string

from vk_api.keyboard import VkKeyboard, VkKeyboardColor
from vk_api.bot_longpoll import VkBotEvent
from vk_api.utils import get_random_id

from FusionBotMODULES import ModuleManager, Logger, Fusion
import datetime

load_module = False


def distance(a, b):
    n, m = len(a), len(b)
    if n > m:
        a, b, n, m = b, a, m, n
    current_row = range(n + 1)
    for i in range(1, m + 1):
        previous_row, current_row = current_row, [i] + [0] * n
        for j in range(1, n + 1):
            add, delete, change = previous_row[j] + 1, current_row[j - 1] + 1, previous_row[j - 1]
            if a[j - 1] != b[i - 1]:
                change += 1
            current_row[j] = min(add, delete, change)

    return current_row[n]


weekdaysForParse = {
    'compact': ["пн", "вт", "ср", "чт", "пт", "сб", "вс"],
    'full': ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье"],
    'relative': {'завтра': 1, 'послезавтра': 2, 'сегодня': 0, 'вчера': -1, 'позавчера': -2}
}


def select_most_suitable(source, pattern: list):
    distances = list()
    for elem in pattern:
        dist = distance(source, elem)
        distances.append(dist)
    return pattern[distances.index(min(distances))]


def parse_date(datestring: str):
    try:
        datetime_1 = datetime.datetime.strptime(datestring, "%d.%m.%Y").date()
    except ValueError:
        pass
    else:
        return datetime_1.weekday(), datetime_1
    mix = weekdaysForParse["compact"] + weekdaysForParse["full"] + weekdaysForParse["relative"]
    datestring = datestring.lower()
    weekday_str = select_most_suitable(datestring, mix)
    if weekday_str in weekdaysForParse["relative"]:
        now = datetime.datetime.now().date()
        now = now + datetime.timedelta(weekdaysForParse["relative"][weekday_str])
        return now.weekday(), now
    weekday = None
    if weekday_str in weekdaysForParse["compact"]:
        weekday = weekdaysForParse["compact"].index(weekday_str)
    elif weekday_str in weekdaysForParse["full"]:
        weekday = weekdaysForParse["full"].index(weekday_str)
    now = datetime.datetime.now().date()
    now = now + datetime.timedelta((weekday - now.weekday()) % 7)
    return now.weekday(), now


def send_keyboard(key_list, module, page=0, rows=9, columns=4, one_time=True, submit=True):
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


def random_str(stringLength=16):
    password_characters = string.ascii_letters + string.digits + string.punctuation
    # noinspection PyUnusedLocal
    return ''.join(random.choice(password_characters) for i in range(stringLength))


class Module(ModuleManager.Module):
    name = "HWModule"
    description = "А вот этого тебе лучше не знать.."
    GUILD_LOCK = [2000000001, 168958515]
    logger = Logger(app="HWModule")

    def update_guild_lock(self, client: Fusion):
        # noinspection SpellCheckingInspection
        new_glock = set(self.GUILD_LOCK)
        new_glock.update(list(client.module_manager.params["hw_chatids"].keys()))
        self.GUILD_LOCK = list(new_glock)

    def run(self, client: Fusion):
        client.module_manager.add_param("hw_chatids", {})
        client.module_manager.add_param("hw_data", {})

        class RegisterChatCommand(ModuleManager.Command):
            name = "hw_reg"
            description = "Регистрация нового чата"
            permissions = ["administrator"]
            args = "<chat_id>"

            def run(self, event: VkBotEvent, args, keys):
                try:
                    chat_id = int(args[0])
                except Exception:  # вот как бля в этом питоне перехватить один из двух эксепшнов блядь?
                    return False
                identificator = random_str()
                while identificator in client.module_manager.params["hw_data"]:
                    identificator = random_str()
                client.module_manager.params["hw_chatids"][chat_id] = {"id": identificator, "active": True}
                client.module_manager.params["hw_data"][identificator] = {
                    'subjects': [],
                    'homework': [],
                    "schedule": []
                }
                client.module_manager.save_params()

                return True

        client.module_manager.add_command(RegisterChatCommand(), self)

        class BindCommand(ModuleManager.Command):
            name = "hw_bind"
            description = "Привязать другой чат к текущему чату"
            args = "<chat_id>"

            def run(self, event: VkBotEvent, args, keys):
                this_peer_id = event.obj.peer_id
                try:
                    chat_id = int(args[0])
                except Exception:  # вот как бля в этом питоне перехватить один из двух эксепшнов блядь?
                    return False
                hw_chatids = client.module_manager.params["hw_chatids"]
                if this_peer_id not in hw_chatids:
                    client.get_api().messages.send(
                        message="Данная возможность недоступна для этого чата",
                        peer_id=this_peer_id,
                        random_id=get_random_id()
                    )
                    return True
                if chat_id in client.module_manager.params["hw_chatids"]:
                    text = "Данный чат невозможно привязать к другому чату."
                    if hw_chatids[chat_id]["id"] == hw_chatids[this_peer_id]["id"]:
                        text = "Данный чат уже привязан к этому чату"
                    client.get_api().messages.send(
                        message=text,
                        peer_id=this_peer_id,
                        random_id=get_random_id()
                    )
                identif = client.module_manager.params["hw_chatids"][this_peer_id]
                client.module_manager.params["hw_chatids"][chat_id] = {"id": identif, "active": True,
                                                                       "referer": this_peer_id}
                client.module_manager.save_params()

        client.module_manager.add_command(BindCommand(), self)

        class UnbindCommand(ModuleManager.Command):
            name = "hw_unbind"
            description = "Отвязать привязанный чат"
            args = "<chat_id>"

            def run(self, event: VkBotEvent, args, keys):
                try:
                    chat_id = int(args[0])
                except Exception:  # вот как бля в этом питоне перехватить один из двух эксепшнов блядь?
                    return False
                peer_id = event.obj.peer_id
                text = "Чат успешно отвязан"
                try:
                    chat = client.module_manager.params["hw_chatids"][chat_id]
                    try:
                        ref = chat["referer"]
                        if ref == peer_id:
                            del client.module_manager.params["hw_chatids"][chat_id]
                    except KeyError:
                        text = "Данный чат не привязан к этому чату"
                except KeyError:
                    text = "Данный чат не существует в базе данных"
                client.get_api().messages.send(
                    message=text,
                    peer_id=peer_id,
                    random_id=get_random_id()
                )


