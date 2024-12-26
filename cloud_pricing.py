from typing import Dict, List, Optional
import json

class CloudPricing:
    def __init__(self):
        # Базовые цены на популярные сервисы
        self.prices = {
            "compute": {
                "cpu_hour": 4.75,  # Цена за час CPU
                "ram_gb_hour": 1.58,  # Цена за час ГБ RAM
                "disk_gb_month": 0.93,  # Цена за ГБ диска в месяц
            },
            "storage": {
                "gb_month": 0.15,  # Цена за ГБ в месяц
                "operations": {
                    "read": 0.0000876,  # Цена за 1000 операций чтения
                    "write": 0.0008766,  # Цена за 1000 операций записи
                }
            },
            "database": {
                "postgresql": {
                    "small": 2950,  # Цена в месяц за малый инстанс
                    "medium": 5900,  # Цена в месяц за средний инстанс
                    "large": 11800,  # Цена в месяц за большой инстанс
                }
            }
        }

    def calculate_vm_cost(self, cpu: int, ram: int, disk: int, hours: int = 730) -> Dict:
        """
        Расчет стоимости виртуальной машины
        
        :param cpu: Количество ядер CPU
        :param ram: Объем RAM в ГБ
        :param disk: Объем диска в ГБ
        :param hours: Количество часов работы (по умолчанию месяц)
        :return: Словарь с расчетом стоимости
        """
        cpu_cost = self.prices["compute"]["cpu_hour"] * cpu * hours
        ram_cost = self.prices["compute"]["ram_gb_hour"] * ram * hours
        disk_cost = self.prices["compute"]["disk_gb_month"] * disk
        
        total = cpu_cost + ram_cost + disk_cost
        
        return {
            "total": round(total, 2),
            "details": {
                "cpu": round(cpu_cost, 2),
                "ram": round(ram_cost, 2),
                "disk": round(disk_cost, 2)
            },
            "monthly_estimate": round(total, 2)
        }

    def get_service_recommendation(self, requirements: Dict) -> Dict:
        """
        Получение рекомендаций по выбору сервисов
        
        :param requirements: Словарь с требованиями
        :return: Словарь с рекомендациями
        """
        recommendations = {
            "recommended_services": [],
            "cost_estimate": {},
            "explanation": ""
        }
        
        # Анализ требований
        if requirements.get("type") == "web_app":
            if requirements.get("traffic", 0) < 1000:
                recommendations["recommended_services"].append({
                    "name": "Cloud Functions",
                    "reason": "Для небольших веб-приложений с низким трафиком"
                })
            else:
                recommendations["recommended_services"].append({
                    "name": "Compute Cloud",
                    "reason": "Для веб-приложений с высоким трафиком"
                })
        
        elif requirements.get("type") == "database":
            if requirements.get("data_size", 0) < 100:
                recommendations["recommended_services"].append({
                    "name": "Managed Service for PostgreSQL (small)",
                    "reason": "Для небольших баз данных"
                })
            else:
                recommendations["recommended_services"].append({
                    "name": "Managed Service for PostgreSQL (medium)",
                    "reason": "Для средних и больших баз данных"
                })
        
        return recommendations

    def format_price_message(self, calculation: Dict) -> str:
        """
        Форматирование сообщения с расчетом цены
        
        :param calculation: Словарь с расчетом
        :return: Отформатированное сообщение
        """
        message = "💰 Расчет стоимости:\n\n"
        message += f"Общая стоимость: {calculation['total']} ₽/мес\n\n"
        message += "📊 Детализация:\n"
        message += f"• CPU: {calculation['details']['cpu']} ₽\n"
        message += f"• RAM: {calculation['details']['ram']} ₽\n"
        message += f"• Диск: {calculation['details']['disk']} ₽\n"
        
        return message

    def get_pricing_info(self, service: str) -> str:
        """
        Получение информации о ценах на сервис
        
        :param service: Название сервиса
        :return: Информация о ценах
        """
        if service == "compute":
            return f"""
💻 Цены на Compute Cloud:

• CPU: {self.prices['compute']['cpu_hour']} ₽/час за ядро
• RAM: {self.prices['compute']['ram_gb_hour']} ₽/час за ГБ
• Диск: {self.prices['compute']['disk_gb_month']} ₽/месяц за ГБ

Для расчета стоимости используйте команду:
/calculate_vm [cpu] [ram] [disk]
Например: /calculate_vm 2 4 100
            """
        
        elif service == "storage":
            return f"""
💾 Цены на Object Storage:

• Хранение: {self.prices['storage']['gb_month']} ₽/месяц за ГБ
• Операции чтения: {self.prices['storage']['operations']['read']} ₽ за 1000 операций
• Операции записи: {self.prices['storage']['operations']['write']} ₽ за 1000 операций
            """
        
        return "Информация о ценах на данный сервис недоступна"
