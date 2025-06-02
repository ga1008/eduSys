from django.core.management.base import BaseCommand
from models import User

class Command(BaseCommand):
    help = '创建超级管理员账号'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, help='用户名')
        parser.add_argument('--email', type=str, help='邮箱')
        parser.add_argument('--password', type=str, help='密码')

    def handle(self, *args, **options):
        username = options['username'] or 'superadmin'
        email = options['email'] or 'superadmin@example.com'
        password = options['password'] or 'admin123'

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f'用户 {username} 已存在'))
            return

        User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
            role='superadmin'
        )
        self.stdout.write(self.style.SUCCESS(f'成功创建超级管理员: {username}'))