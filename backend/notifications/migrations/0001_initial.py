# Generated by Django 4.2 on 2025-06-05 19:16

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UserNotificationSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('receive_private_messages', models.BooleanField(default=True, verbose_name='接收私信')),
                ('receive_assignment_notifications', models.BooleanField(default=True, verbose_name='接收作业相关通知')),
                ('receive_grading_notifications', models.BooleanField(default=True, verbose_name='接收批改相关通知')),
                ('receive_forum_notifications', models.BooleanField(default=True, verbose_name='接收论坛相关通知')),
                ('receive_course_class_change_notifications', models.BooleanField(default=True, verbose_name='接收课程/班级变动通知')),
                ('private_message_policy', models.CharField(choices=[('everyone', '任何人'), ('contacts_only', '仅限指定联系人'), ('teachers_staff_only', '仅限教师和管理员'), ('staff_only', '仅限管理员'), ('superadmin_only', '仅限超级管理员'), ('none', '不接收任何人私信 (超级管理员除外)')], default='everyone', max_length=30, verbose_name='私信接收策略')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='notification_settings', to=settings.AUTH_USER_MODEL, verbose_name='用户')),
            ],
            options={
                'verbose_name': '用户通知设置',
                'verbose_name_plural': '用户通知设置',
            },
        ),
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[('private_message', '私信'), ('assignment_new', '新作业发布'), ('assignment_graded', '作业已批改'), ('course_change', '课程信息更新'), ('class_change', '班级信息更新'), ('forum_reply', '论坛新回复'), ('forum_like_summary', '论坛收到点赞'), ('submission_new', '学生提交新作业'), ('system_announcement', '系统公告'), ('user_mention', '用户提及'), ('other', '其他通知')], max_length=50, verbose_name='通知类型')),
                ('title', models.CharField(blank=True, max_length=255, null=True, verbose_name='通知标题')),
                ('content', models.TextField(verbose_name='通知内容')),
                ('timestamp', models.DateTimeField(auto_now_add=True, verbose_name='时间戳')),
                ('is_read', models.BooleanField(default=False, verbose_name='是否已读')),
                ('read_at', models.DateTimeField(blank=True, null=True, verbose_name='阅读时间')),
                ('object_id', models.PositiveIntegerField(blank=True, null=True)),
                ('can_recipient_delete', models.BooleanField(default=True, verbose_name='接收者可删除')),
                ('can_recipient_reply', models.BooleanField(default=False, verbose_name='接收者可回复')),
                ('data', models.JSONField(blank=True, null=True, verbose_name='附加数据')),
                ('content_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype')),
                ('parent_notification', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='replies', to='notifications.notification', verbose_name='父通知ID')),
                ('recipient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to=settings.AUTH_USER_MODEL, verbose_name='接收者')),
                ('sender', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sent_notifications', to=settings.AUTH_USER_MODEL, verbose_name='发送者')),
            ],
            options={
                'verbose_name': '通知',
                'verbose_name_plural': '通知',
                'ordering': ['-timestamp'],
            },
        ),
        migrations.CreateModel(
            name='BlockedContact',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timestamp', models.DateTimeField(auto_now_add=True, verbose_name='屏蔽时间')),
                ('blocked_user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='blocked_by_contacts', to=settings.AUTH_USER_MODEL, verbose_name='被屏蔽者')),
                ('blocker', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='blocking_contacts', to=settings.AUTH_USER_MODEL, verbose_name='屏蔽发起者')),
            ],
            options={
                'verbose_name': '黑名单联系人',
                'verbose_name_plural': '黑名单联系人',
                'ordering': ['-timestamp'],
            },
        ),
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(fields=['recipient', 'is_read', '-timestamp'], name='notificatio_recipie_b032c9_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='blockedcontact',
            unique_together={('blocker', 'blocked_user')},
        ),
    ]
