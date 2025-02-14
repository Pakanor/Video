import os
from celery import Celery

# Ustaw zmienną środowiskową na plik settings.py
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mysite.settings")

app = Celery("mysite")

# Odczyt ustawień Celery z Django settings.py
app.config_from_object("django.conf:settings", namespace="CELERY")

# Automatyczne ładowanie zadań z aplikacji Django
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
