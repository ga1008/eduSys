from django.core.management.base import BaseCommand
from django.db import transaction
from course.models import TeacherCourseClass
from education.models import User
from chatroom.models import ChatRoom, ChatRoomMember, generate_random_nickname


class Command(BaseCommand):
    help = '为数据库中已存在的 TeacherCourseClass 记录创建对应的聊天室和成员'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('开始为已有课程班级同步聊天室...'))

        # 找到所有还没有对应聊天室的课程班级
        tccs_without_chatroom = TeacherCourseClass.objects.filter(chatroom__isnull=True)

        if not tccs_without_chatroom.exists():
            self.stdout.write(self.style.SUCCESS('所有课程班级均已有聊天室，无需操作。'))
            return

        created_count = 0
        for tcc in tccs_without_chatroom:
            self.stdout.write(f'  -> 正在为 "{tcc.course.name} - {tcc.class_obj.name}" 创建聊天室...')

            # 1. 创建聊天室
            room_name = f"{tcc.course.name} - {tcc.class_obj.name} 交流群"
            room = ChatRoom.objects.create(tcc=tcc, name=room_name)

            # 2. 添加教师为管理员
            ChatRoomMember.objects.create(
                room=room,
                user=tcc.teacher,
                role='admin',
                nickname=tcc.teacher.name or f"{tcc.teacher.username}(老师)"
            )

            # 3. 添加班级所有学生为成员
            students = User.objects.filter(class_enrolled=tcc.class_obj, role='student')
            members_to_create = [
                ChatRoomMember(
                    room=room,
                    user=student,
                    role='member',
                    nickname=generate_random_nickname()
                )
                for student in students
            ]
            ChatRoomMember.objects.bulk_create(members_to_create)

            created_count += 1
            self.stdout.write(self.style.SUCCESS(f'     创建成功，添加了 1 位教师和 {len(students)} 位学生。'))

        self.stdout.write(self.style.SUCCESS(f'\n操作完成！共为 {created_count} 个课程班级创建了新的聊天室。'))
