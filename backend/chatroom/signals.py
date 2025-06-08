# backend/chatroom/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from course.models import TeacherCourseClass
from education.models import User
from .models import ChatRoom, ChatRoomMember, generate_random_nickname


@receiver(post_save, sender=TeacherCourseClass)
def create_chat_room_for_tcc(sender, instance, created, **kwargs):
    """
    当一个新的 TeacherCourseClass 创建时，自动创建聊天室并添加成员。
    """
    if created:
        # 1. 创建聊天室
        room_name = f"{instance.course.name} - {instance.class_obj.name} 交流群"
        room = ChatRoom.objects.create(tcc=instance, name=room_name)

        # 2. 添加教师为管理员
        ChatRoomMember.objects.create(
            room=room,
            user=instance.teacher,
            role='admin',
            nickname=instance.teacher.name or f"{instance.teacher.username}(老师)"
        )

        # 3. 添加班级所有学生为成员
        students = User.objects.filter(class_enrolled=instance.class_obj, role='student')
        members_to_create = [
            ChatRoomMember(
                room=room,
                user=student,
                role='member',
                nickname=generate_random_nickname()  # 每个学生一个随机昵称
            )
            for student in students
        ]
        ChatRoomMember.objects.bulk_create(members_to_create)
