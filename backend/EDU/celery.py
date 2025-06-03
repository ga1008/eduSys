import os
from celery import Celery

# 设置 Django 的 settings 模块环境变量
# 将 'EDU.settings' 替换为你的实际项目 settings 模块路径
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'EDU.settings')

# 创建 Celery 应用实例
# 将 'EDU' 替换为你的项目名称
app = Celery('EDU')

# 使用 Django settings.py 中的配置，CELERY_ 为前缀
app.config_from_object('django.conf:settings', namespace='CELERY')

# 自动发现所有 Django app 下的 tasks.py 文件
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
