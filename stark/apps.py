from django.apps import AppConfig
from django.utils.module_loading import autodiscover_modules

class StarkConfig(AppConfig):
    name = 'stark'

    def ready(self):  # 该方法默认去加载所有APP下的stark.py文件
        autodiscover_modules("stark")
