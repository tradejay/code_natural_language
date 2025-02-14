import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'code_natural_language.settings')  # 실제 Django 프로젝트의 settings 모듈 이름으로 변경

application = get_wsgi_application()
