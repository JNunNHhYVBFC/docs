import logging
import httpx
import json

logger = logging.getLogger(__name__)

class CloudAssistant:
    def __init__(self, api_key: str, folder_id: str):
        """
        Инициализация ассистента Yandex Cloud
        
        :param api_key: API ключ
        :param folder_id: ID каталога в облаке
        """
        self.api_key = api_key
        self.folder_id = folder_id
        self.base_url = "https://llm.api.cloud.yandex.net/foundationModels/v1"
        self.headers = {
            "Authorization": f"Api-Key {api_key}",
            "Content-Type": "application/json"
        }
        
        # Системные промпты для разных задач
        self.system_prompts = {
            "examples": (
                "Ты - эксперт по Yandex Cloud. Предоставь конкретный пример кода для указанного сервиса. "
                "Используй актуальные версии SDK и лучшие практики. Добавь комментарии для объяснения кода."
            ),
            "optimization": (
                "Ты - специалист по оптимизации в Yandex Cloud. Проанализируй описанную ситуацию "
                "и предложи конкретные рекомендации по оптимизации с учетом производительности и стоимости."
            ),
            "diagnostics": (
                "Ты - эксперт по диагностике проблем в Yandex Cloud. Проанализируй описанную проблему, "
                "предложи возможные причины и конкретные шаги для их устранения."
            )
        }
    
    async def get_completion(self, prompt: str, system_prompt: str = None) -> str:
        """
        Получение ответа от модели
        
        :param prompt: Текст запроса
        :param system_prompt: Системный промпт для задания контекста
        :return: Ответ модели
        """
        try:
            messages = []
            if system_prompt:
                messages.append({
                    "role": "system",
                    "text": system_prompt
                })
            
            messages.append({
                "role": "user",
                "text": prompt
            })
            
            data = {
                "modelUri": f"gpt://{self.folder_id}/yandexgpt-lite",
                "completionOptions": {
                    "stream": False,
                    "temperature": 0.6,
                    "maxTokens": 2000
                },
                "messages": messages
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/completion",
                    headers=self.headers,
                    json=data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result["result"]["alternatives"][0]["message"]["text"]
                else:
                    logger.error(f"Error from API: {response.status_code} - {response.text}")
                    return "Извините, произошла ошибка при обработке запроса."
                    
        except Exception as e:
            logger.error(f"Error in get_completion: {str(e)}")
            return "Извините, произошла ошибка при обработке запроса."
    
    async def get_code_example(self, service: str, scenario: str) -> str:
        """
        Получение примера кода для конкретного сервиса и сценария
        
        :param service: Название сервиса
        :param scenario: Описание сценария использования
        :return: Пример кода с объяснениями
        """
        prompt = f"Предоставь пример кода на Python для сервиса {service} в Yandex Cloud. Сценарий: {scenario}"
        return await self.get_completion(prompt, system_prompt=self.system_prompts["examples"])
    
    async def get_optimization_advice(self, resource_type: str, current_setup: str) -> str:
        """
        Получение рекомендаций по оптимизации
        
        :param resource_type: Тип ресурса (VM, storage, etc.)
        :param current_setup: Текущая конфигурация
        :return: Рекомендации по оптимизации
        """
        prompt = f"Проанализируй текущую конфигурацию {resource_type}: {current_setup}. Предложи оптимизации."
        return await self.get_completion(prompt, system_prompt=self.system_prompts["optimization"])
    
    async def get_diagnostic_help(self, problem_description: str) -> str:
        """
        Получение помощи в диагностике проблем
        
        :param problem_description: Описание проблемы
        :return: Диагностика и решение
        """
        prompt = f"Помоги диагностировать и решить проблему: {problem_description}"
        return await self.get_completion(prompt, system_prompt=self.system_prompts["diagnostics"])
    
    async def get_service_info(self, service: str) -> str:
        """
        Получение информации о сервисе
        
        :param service: Название сервиса
        :return: Информация о сервисе
        """
        prompt = f"Расскажи подробно о сервисе Yandex Cloud {service}. Включи основные возможности, варианты использования и преимущества."
        return await self.get_completion(prompt)
    
    async def get_recommendation(self, requirements: str) -> str:
        """
        Получение рекомендаций по выбору сервисов
        
        :param requirements: Требования пользователя
        :return: Рекомендации по сервисам
        """
        prompt = f"На основе следующих требований, порекомендуй подходящие сервисы Yandex Cloud: {requirements}"
        return await self.get_completion(prompt)
