import os
import FusionBotMODULES

from vk_api.bot_longpoll import VkBotEvent
from vk_api.utils import get_random_id
from vk_api.vk_api import VkApi
from textgenrnn import textgenrnn

logger = FusionBotMODULES.Logger(app="Adisman")

model_files = {
    "weights_path": "NeuroNetworks/Adisman/adisman_weights.hdf5",
    "vocab_path": "NeuroNetworks/Adisman/adisman_vocab.json",
    "config_path": "NeuroNetworks/Adisman/adisman_config.json"
}


class Module(FusionBotMODULES.ModuleManager.Module):
    name = "Adisman"
    description = "Текстовая рекуррентная генерацивная нейронная сеть."

    def run(self, client: VkApi, module_manager: FusionBotMODULES.ModuleManager):
        module_manager.add_param("aiTemp", 0.9)
        for k in model_files:
            v = model_files[k]
            if not os.path.isfile(v):
                logger.log(1, "No file %s" % v)
                logger.log(3, "No model files found. Module will not be loaded.")
                module_manager.unload_module(self.name)
                return
        textgen = textgenrnn(weights_path=model_files["weights_path"], vocab_path=model_files["vocab_path"],
                             config_path=model_files["config_path"])

        class CommandAI(FusionBotMODULES.ModuleManager.Command):
            name = "ai"
            description = "Обратиться к Adisman"
            keys = ["prefix"]

            def run(self, event: VkBotEvent, args, keys):
                prefix = ""
                if "prefix" in keys:
                    prefix = " ".join(args)
                ai_text = "".join(textgen.generate(temperature=module_manager.params["aiTemp"], return_as_list=True,
                                                   prefix=prefix))
                client.get_api().messages.send(
                    peer_id=event.obj.peer_id,
                    message=ai_text,
                    random_id=get_random_id()
                )
                return True
        module_manager.add_command(CommandAI(), self)
