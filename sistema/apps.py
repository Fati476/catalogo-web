from django.apps import AppConfig


class SistemaConfig(AppConfig):
    name = 'sistema'

    def ready(self):
        import sistema.signals
