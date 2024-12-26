import os
import json
import yandexcloud

class YandexCloudClient:
    def __init__(self, sa_key_file='authorized_key.json'):
        # Загружаем авторизованный ключ
        with open(sa_key_file, 'r') as f:
            self.sa_key_json = json.load(f)
        
        # Инициализируем SDK
        self.sdk = yandexcloud.SDK(service_account_key=self.sa_key_json)
    
    def get_folder_id(self):
        """Получить ID каталога"""
        return os.getenv("YANDEX_FOLDER_ID")
    
    def list_compute_instances(self):
        """Получить список виртуальных машин"""
        compute = self.sdk.client('compute').instances()
        return compute.list(folder_id=self.get_folder_id())
    
    def list_databases(self):
        """Получить список баз данных"""
        ydb = self.sdk.client('managed-ydb').databases()
        return ydb.list(folder_id=self.get_folder_id())
    
    def __del__(self):
        """Закрываем каналы при удалении объекта"""
        try:
            # self.compute_channel.close()
            # self.ydb_channel.close()
            pass
        except:
            pass
