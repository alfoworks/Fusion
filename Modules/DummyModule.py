from vk_api import VkApi
from vk_api.bot_longpoll import VkBotEvent
from vk_api.utils import get_random_id
import FusionBotMODULES


class Module(FusionBotMODULES.ModuleManager.Module):  # Класс должен ОБЯЗАТЕЛЬНО называться Module. В ином случае
    # произойдет ошибка и бот не запустится (а с ним и модуль)
    name = "DummyModule"  # Имя модуля
    description = "Хуйня ебаная"  # Описание модуля

    # Список чатов, где будет РАБОТАТЬ данный модуль. В иных других чатах он будет скрыт полностью
    # за исключением /params, но эта команда закрыта правами и её лучше не вызывать там, где не надо.
    # Если список пуст - белый список не применяется
    GUILD_LOCK = []

    # Основной метод модуля, выполняется в конце инициализации бота (после загрузки параметров и модулей)
    def run(self, api: VkApi, module_manager: FusionBotMODULES.ModuleManager):
        # api - обьект, через который вы будете отправлять сообщения и делать любую другую работу с вк
        # moduleManager - обьект менеджера модулей. Предоставляет регистры

        """
            Система параметров бота
            module_manager.add_param(key, value) - добавляет параметр и устанавливает его начальное значение.
            Если параметр уже создан и в нем есть значение, ничего не делает.

            Изменение параметра -
            module_manager.params[key] = value

            Затем необходимо сохранить
            module_manager.save_params()
            После add_param сохранение не требуется

            ===========

            Проверить наличие разрешения у пользователя -
            module_manager.has_permission(permission: str, user_id)
            Подробнее о системе разрешений в DummyCommand

            Создать фоновую задачу -
            module_manager.add_background_task(module, coroutine)
            module - это обьект модуля (получить можно через self в методе модуля)
            coroutine - awaitable-обьект. Создается через async def с последующим вызовом (без await) и передачей
            результата в данную функцию. Выполняется ОДНОКРАТНО. Может заблокировать главный поток бота.


            Создание команды:
        """
        class DummyCommand(FusionBotMODULES.ModuleManager.Command):
            name = "dummy"  # название команды.
            description = "Хуйня ебаная"  # описание
            args = "аргумент1 аргумент2"  # влияет только на вывод в /cmds (для пользователя)
            keys = []  # так же влияет только на вывод в /cmds. Здесь вводится без двойного тире.
            permissions = []  # права, необходимые для запуска команды.
            """ О системе прав доступа
            Система прав предоставляется не ВК, а ботом.
            Наследования прав нет. Если вам нужно создать команду, которая будет доступна одному праву и выше - просто 
            вбейте самое низшее право и выдайте его всем, кто выше.
            По умолчанию поддерживается право administrator.
            Для регулирования прав - /permissions. Подробности в /cmds
            """
            no_args_pass = False  # Если True, пропустит человека без прав, если он не передавал аргументов в команду

            # главный метод команды. Вызывается при вызове команды.
            def run(self, event: VkBotEvent, args, keys):
                api.get_api().messages.send(
                    peer_id=event.obj.peer_id,
                    message="Пощел нахуй!",
                    random_id=get_random_id()
                )
                """
                    args - это все, что введено после команды, поделенное пробелами. Представляет собой список строк.
                    keys - все, что было в args и введено с двойным тире в начале. Удаляется из списка args.
                """
                return True  # если вернуть False, пользователю покажет синтаксис команды

        module_manager.add_command(DummyCommand(), self)  # Регистрация команды

    # Данный метод вызывается при ЛЮБОМ событии, которое получает бот через LongPoll.
    def on_event(self, api: VkApi, event: VkBotEvent):
        pass