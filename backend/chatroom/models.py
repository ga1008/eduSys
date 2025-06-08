# backend/chatroom/models.py

from django.db import models
from django.conf import settings
from course.models import TeacherCourseClass
import random

# 有趣的中文代号列表，可以自由扩展

places = [
    "马尔代夫", "香格里拉", "布达拉宫", "洱海", "敦煌", "九寨沟", "丽江", "黄山", "张家界", "三亚",
          "西湖", "桂林", "泰山", "峨眉山", "鼓浪屿", "乌镇", "周庄", "凤凰古城", "喀纳斯", "长白山",
          "青海湖", "壶口瀑布", "呼伦贝尔", "稻城亚丁", "泸沽湖", "天山", "华山", "平遥古城", "宏村", "三峡",
            "大理", "阳朔", "漓江", "西双版纳", "张掖丹霞", "黄龙风景区", "千岛湖", "南浔古镇", "婺源", "赤壁",
            "西递", "安吉", "龙脊梯田", "平乐古镇", "南岳衡山", "武夷山", "庐山", "天门山", "崂山",
    # 南宁市地名
    "青秀山", "南湖", "南宁动物园", "广西民族博物馆", "南宁国际会展中心", "南宁火车站", "南宁东站", "西乡塘",
    "江南区", "兴宁区", "良庆区", "邕宁区", "武鸣区", "隆安县", "马山县", "上林县", "宾阳县", "横县",

    # 南宁高校简称
    "南院", "西大", "师大", "民大", "科大", "医科大", "广艺", "广外",
]

adjectives = [
    "伤心的", "快乐的", "焦虑的", "兴奋的", "安静的", "迷茫的", "孤独的", "勇敢的", "疲倦的", "害羞的",
              "骄傲的", "急躁的", "幽默的", "冷静的", "热情的", "犹豫的", "好奇的", "固执的", "浪漫的", "敏感的",
                "自信的", "温柔的", "坚定的", "乐观的", "悲观的", "善良的", "聪明的", "机智的", "慷慨的", "细心的",
]

items = [
    "土豆", "手机", "书包", "云朵", "路灯", "咖啡杯", "吉他", "风筝", "行李箱", "帆船",
         "耳机", "闹钟", "日记本", "篮球", "望远镜", "钥匙", "枕头", "雨伞", "蜡烛", "相机",
         "枫叶", "贝壳", "邮票", "魔方", "围巾", "纸飞机", "沙漏", "蒲公英", "篮球", "闹钟",

    # 餐厅
    "老友粉", "螺蛳粉", "桂林米粉", "烧烤摊", "路边摊", "南宁炒粉", "牛肉粉", "鸭脚煲", "糖水铺", "酸野",

    # 水果
    "荔枝", "龙眼", "芒果", "香蕉", "柚子", "橙子", "苹果", "葡萄", "西瓜", "草莓",

    # 其他
    "吃瓜群众", "潜水冠军", "摸鱼大师", "代码农神", "学习卷王", "BUG捕手",
    "梗文化研究员", "熬夜冠军", "奶茶续命师", "快乐源泉", "人间清醒", "气氛组组长"

]


def generate_random_nickname():
    """生成一个随机的代号"""
    return random.choice(places) + random.choice(adjectives) + random.choice(items)


class ChatRoom(models.Model):
    tcc = models.OneToOneField(TeacherCourseClass, on_delete=models.CASCADE, related_name='chatroom',
                               verbose_name="关联教学班")
    name = models.CharField(max_length=255, verbose_name="聊天室名称")
    is_muted = models.BooleanField(default=False, verbose_name="全员禁言")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class ChatRoomMember(models.Model):
    ROLE_CHOICES = (
        ('member', '普通成员'),
        ('admin', '管理员'),
    )
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='members', verbose_name="聊天室")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chat_memberships',
                             verbose_name="用户")
    nickname = models.CharField(max_length=50, default=generate_random_nickname, verbose_name="群内昵称")
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='member', verbose_name="角色")
    is_active = models.BooleanField(default=True, verbose_name="是否在群内")  # 用于实现“踢出”功能
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('room', 'user')
        ordering = ['joined_at']

    def __str__(self):
        return f"{self.user.username} in {self.room.name} as {self.nickname}"


class ChatMessage(models.Model):
    MESSAGE_TYPE_CHOICES = (
        ('text', '文本'),
        ('image', '图片'),
        ('video', '视频'),
        ('file', '文件'),
        ('system', '系统消息'),  # 如“XXX加入了群聊”
    )
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages', verbose_name="聊天室")
    author = models.ForeignKey(ChatRoomMember, on_delete=models.SET_NULL, null=True, blank=True,
                               related_name='messages', verbose_name="作者")
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPE_CHOICES, default='text')
    content = models.TextField(verbose_name="消息内容")  # 对于富文本，存储HTML；对于文件，存储提示信息

    # 用于文件类消息
    file_path = models.CharField(max_length=512, blank=True, null=True, verbose_name="Minio文件路径")
    file_original_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="原始文件名")
    thumbnail_path = models.CharField(max_length=512, blank=True, null=True, verbose_name="缩略图路径")

    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    is_deleted = models.BooleanField(default=False, verbose_name="是否已删除")  # 软删除

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"Message from {self.author} in {self.room.name} at {self.timestamp}"
