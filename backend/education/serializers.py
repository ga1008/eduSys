from rest_framework import serializers

from .models import Class, Course, User


class ClassSerializer(serializers.ModelSerializer):
    # 课程多对多字段：提交时使用课程ID列表；读取时默认返回课程ID列表
    courses = serializers.PrimaryKeyRelatedField(queryset=Course.objects.all(), many=True, required=False)
    student_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Class
        fields = ['id', 'name', 'major', 'department', 'year', 'description', 'courses', 'student_count']


class StudentSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, help_text="初始密码")

    class Meta:
        model = User  # 使用自定义的User模型
        fields = ['id', 'username', 'student_number', 'name', 'email',
                  'gender', 'phone', 'qq', 'class_enrolled', 'password', 'role']
        read_only_fields = ['username']
        extra_kwargs = {
            'email': {'required': True},
            'student_number': {'required': True},
            'class_enrolled': {'required': True, 'allow_null': False}
        }

    def create(self, validated_data):
        # 从验证后的数据中取出密码字段
        password = validated_data.pop('password', None)
        # 创建User对象，但暂不保存（便于先设置密码）
        user = User(**validated_data)
        if password:
            user.set_password(password)  # 设置初始密码（哈希处理）
        else:
            # 如果未提供密码，可设置一个默认密码或者处理为错误
            user.set_password('123456')
        user.role = 'student'  # 确保角色为学生
        user.save()
        return user

    def update(self, instance, validated_data):
        # 更新学生信息时，如提供了新密码则一并处理
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class TeacherSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, help_text="教师密码")

    class Meta:
        model = User
        fields = ['id', 'teacher_number', 'name', 'gender', 'email', 'password', 'role', 'phone']
        read_only_fields = ['id', 'role']
        extra_kwargs = {
            'email': {'required': True},
            'teacher_number': {'required': True}
        }

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        # 使用工号作为用户名
        teacher_number = validated_data.get('teacher_number')
        validated_data['username'] = teacher_number

        user = User(**validated_data)
        if password:
            user.set_password(password)
        else:
            user.set_password('123456')
        user.role = 'teacher'
        user.save()
        return user

    def update(self, instance, validated_data):
        # 更新教师信息，如提供了新密码则一并处理
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class SuperAdminSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, help_text="管理员密码")

    class Meta:
        model = User
        # 使用 username 作为唯一标识，而非 teacher_number
        fields = ['id', 'username', 'name', 'gender', 'email', 'password', 'role', 'phone']
        read_only_fields = ['id', 'role']
        extra_kwargs = {
            'email': {'required': True},
            'username': {'required': True}  # username 是必填项
        }

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        # 确保 username 不为空
        if not validated_data.get('username'):
            raise serializers.ValidationError({"username": "用户名不能为空。"})

        user = User(**validated_data)
        if password:
            user.set_password(password)
        else:
            # 新建管理员时，密码是必需的
            raise serializers.ValidationError({"password": "创建管理员时必须设置初始密码。"})

        user.role = 'superadmin'  # 核心：确保角色正确
        user.is_staff = True  # 超级管理员通常也是 staff
        user.is_superuser = True  # 确保 Django 的超级管理员权限
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)

        # Superadmin 不能被降级
        if 'role' in validated_data and validated_data['role'] != 'superadmin':
            raise serializers.ValidationError({"role": "不能修改超级管理员的角色。"})

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)

        instance.save()
        return instance
