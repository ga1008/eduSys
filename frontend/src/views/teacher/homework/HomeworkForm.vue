<template>
  <div class="homework-form-container">
    <h2>{{ isEdit ? '编辑作业' : '创建作业' }}</h2>

    <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="120px"
        v-loading="loading"
        style="max-width: 800px; margin: 0 auto;"
        label-position="top"
    >
      <el-card shadow="never" style="margin-bottom: 20px;">
        <template #header>
          <div class="card-header">
            <span>基本信息</span>
          </div>
        </template>
        <el-descriptions
            v-if="courseClass"
            :column="1"
            border
            style="margin-bottom: 20px"
        >
          <el-descriptions-item label="课程名称">{{ courseClass.course_name }}</el-descriptions-item>
          <el-descriptions-item label="班级">{{ courseClass.class_name }}</el-descriptions-item>
        </el-descriptions>

        <el-form-item label="作业标题" prop="title">
          <el-input v-model="form.title" placeholder="请输入作业标题"/>
        </el-form-item>

        <el-form-item label="作业描述" prop="description">
          <el-input
              v-model="form.description"
              type="textarea"
              rows="5"
              placeholder="请输入作业描述和要求"
          />
        </el-form-item>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="截止日期" prop="due_date">
              <el-date-picker
                  v-model="form.due_date"
                  type="datetime"
                  placeholder="选择截止日期"
                  style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="满分值" prop="max_score">
              <el-input-number
                  v-model="form.max_score"
                  :min="0"
                  :max="1000"
                  :step="5"
                  :precision="2"
                  style="width: 100%;"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="状态" prop="active">
          <el-switch
              v-model="form.active"
              active-text="启用"
              inactive-text="禁用"
          />
        </el-form-item>
      </el-card>

      <el-card shadow="never">
        <template #header>
          <div class="card-header">
            <span>AI辅助批改设置</span>
          </div>
        </template>
        <el-form-item label="启用AI辅助批改" prop="ai_grading_enabled">
          <el-switch v-model="form.ai_grading_enabled"/>
        </el-form-item>

        <el-form-item v-if="form.ai_grading_enabled" label="AI批改提示词" prop="ai_grading_prompt">
          <el-alert type="info" show-icon :closable="false" style="margin-bottom: 10px;">
            <p>
              提示词将自动包含课程、班级、作业标题和描述信息。您可以在下方编辑器中修改或添加更具体的批改指令和评分标准。</p>
          </el-alert>
          <div class="quill-editor-container">
            <QuillEditor
                v-model:content="form.ai_grading_prompt"
                contentType="html"
                theme="snow"
                placeholder="请在此详细描述您希望AI如何辅助批改，例如评分细则、关注点等..."
                style="min-height: 250px; height: auto;"
            />
          </div>
        </el-form-item>
      </el-card>

      <el-form-item style="margin-top: 20px; text-align: center;">
        <el-button type="primary" @click="submitForm" :loading="loading">保存作业</el-button>
        <el-button @click="goBack">返回列表</el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup>
import {ref, reactive, computed, onMounted, watch} from 'vue'
import {useRouter, useRoute} from 'vue-router'
import {fetchTeacherCourseClass} from '@/api/teachers'
import {fetchHomework, createHomework, updateHomework} from '@/api/homeworks'
import {ElMessage} from 'element-plus'
import {QuillEditor} from '@vueup/vue-quill'
import '@vueup/vue-quill/dist/vue-quill.snow.css';

const router = useRouter()
const route = useRoute()
const formRef = ref(null)
const loading = ref(false)
const courseClass = ref(null) // 用于存储课程和班级信息

const isEdit = computed(() => Boolean(route.params.homeworkId))
const courseClassId = computed(() => route.params.id) // 这是 TeacherCourseClass 的 ID

const form = reactive({
  title: '',
  description: '',
  due_date: '',
  max_score: 100,
  active: true,
  course_class: '', // 将存储 courseClassId.value
  ai_grading_enabled: false,
  ai_grading_prompt: ''
})

const rules = {
  title: [
    {required: true, message: '请输入作业标题', trigger: 'blur'},
    {min: 2, max: 200, message: '长度在 2 到 200 个字符', trigger: 'blur'}
  ],
  due_date: [
    {required: true, message: '请选择截止日期', trigger: 'change'},
    {
      validator: (rule, value, callback) => {
        if (value && new Date(value) < new Date()) {
          callback(new Error('截止日期不能早于当前时间'))
        } else {
          callback()
        }
      },
      trigger: 'change'
    }
  ],
  max_score: [
    {required: true, message: '请设置满分值', trigger: 'blur'}
  ],
  ai_grading_prompt: [ // 当AI批改启用时，提示词可以是必填的，或有默认值
    // { validator: (rule, value, callback) => {
    //     if (form.ai_grading_enabled && !value) {
    //       callback(new Error('启用AI批改时，提示词不能为空'));
    //     } else {
    //       callback();
    //     }
    //   }, trigger: 'change'
    // }
  ]
}

const defaultPromptBase = `您是一位经验丰富、教学严谨的[在此处填写学科，例如：计算机科学与技术]学科教师。
请您根据以下提供的课程信息、班级信息、作业标题及详细描述，对学生的提交内容进行全面而细致的批改。

在批改过程中，请重点关注以下几个方面：
1.  知识点理解与应用：评估学生对相关知识点的掌握程度，以及在作业中实际应用的准确性和灵活性。
2.  内容完整性与准确性：检查学生提交的内容是否完整回答了作业要求，信息是否准确无误。
3.  逻辑与条理性：分析学生答案的逻辑结构是否清晰，论述是否有条理。
4.  创新性与亮点（若适用）：发掘学生在作业中可能展现的独特见解或创新性思维。
5.  规范性：注意书写规范、代码风格（若为编程题）、图表绘制标准等。

请确保您的评价专业、客观、公正，并能有效帮助学生理解自身学习状况，明确努力方向。

以下是本次作业的具体信息：
------------------------------------
`
const generatedDefaultPrompt = computed(() => {
  const courseName = courseClass.value?.course_name || '[未加载课程名称]';
  const className = courseClass.value?.class_name || '[未加载班级名称]';
  const assignmentTitle = form.title || '[请输入作业标题]';
  const assignmentDescription = form.description || '[请输入作业描述]';
  const assignmentMaxScore = form.max_score || '[请输入作业最大分数]';

  return `${defaultPromptBase}
课程名称：${courseName}
班级名称：${className}
作业标题：${assignmentTitle}
作业描述：
${assignmentDescription}
作业满分值：${assignmentMaxScore}
------------------------------------
请基于以上信息和下方学生的实际提交内容进行批改。最后严格按照以下格式返回批改结果，不需要任何其他的多余字符：
{
  "score":XX,
  "comment":"作业批改评语，可以是markdown格式，不超过200字",
  AI生成疑似度:0.xx
}
其中，score 是一个数字，表示学生作业的得分（0-作业满分值），comment 是对作业的评语，AI生成疑似度是一个0-1之间的数字，表示AI生成内容的可信度。请确保返回的 JSON 格式正确且完整。注意：如果作业未完成或提交内容不符合要求，请返回 score 为 0，并在 comment 中说明原因。
`;
});

watch(() => form.ai_grading_enabled, (newValue, oldValue) => {
  if (newValue === true && (oldValue === false || !form.ai_grading_prompt)) {
    // 仅当从关闭变为开启，且提示词为空或之前是关闭状态时，才设置默认值
    // 这样避免了用户已自定义提示词后，不小心关闭再开启导致提示词被重置
    form.ai_grading_prompt = generatedDefaultPrompt.value;
  }
});

// 当作业标题或描述变化时，如果AI批改已启用且提示词是“旧的”默认提示词，可以考虑智能更新这部分
// 这个逻辑相对复杂，需要判断当前提示词是否是基于旧的标题/描述生成的，暂时简化处理
watch([() => form.title, () => form.description], () => {
  if (form.ai_grading_enabled) {
    // 简单的做法是：如果用户还没怎么编辑过默认提示（比如长度和默认的很接近），就更新它
    // 或者提供一个“刷新默认提示”的按钮
    // 为避免覆盖用户修改，这里暂时不自动更新，用户开启时会生成最新的。
    // 如果需要更智能的更新，可以在用户修改后设置一个标志，或者比较提示词与模板的差异。
  }
})

const loadCourseClassInfo = async () => {
  if (!courseClassId.value) {
    ElMessage.error('未找到课程班级ID');
    return;
  }
  loading.value = true;
  try {
    const response = await fetchTeacherCourseClass(courseClassId.value);
    courseClass.value = response.data;
    form.course_class = courseClassId.value; // 设置表单中的 course_class ID
  } catch (error) {
    ElMessage.error('加载课程班级信息失败');
    console.error("Error loading course class info:", error);
  } finally {
    loading.value = false;
  }
};

const loadHomeworkData = async () => {
  if (!isEdit.value) return;

  loading.value = true;
  try {
    const response = await fetchHomework(route.params.homeworkId);
    const data = response.data;

    form.title = data.title;
    form.description = data.description || '';
    form.due_date = data.due_date ? new Date(data.due_date) : '';
    form.max_score = data.max_score;
    form.active = data.active;
    form.course_class = data.course_class; // 后端返回的应该是 TeacherCourseClass 的 ID
    form.ai_grading_enabled = data.ai_grading_enabled || false;
    // 如果加载时启用了AI批改且提示词为空，则填充默认值
    if (form.ai_grading_enabled && !data.ai_grading_prompt) {
      form.ai_grading_prompt = generatedDefaultPrompt.value;
    } else {
      form.ai_grading_prompt = data.ai_grading_prompt || '';
    }

  } catch (error) {
    ElMessage.error('加载作业数据失败：' + (error.response?.data?.detail || error.message || '未知错误'));
  } finally {
    loading.value = false;
  }
};

const submitForm = async () => {
  if (!formRef.value) return;

  await formRef.value.validate(async (valid) => {
    if (!valid) {
      ElMessage.error('请检查表单填写是否完整且正确');
      return;
    }

    // 确保 course_class ID 已设置
    if (!form.course_class) {
      ElMessage.error('课程班级信息未正确关联，无法保存作业。');
      return;
    }

    loading.value = true;
    // 准备提交的数据，确保 QuillEditor 的 HTML 内容被正确传递
    const dataToSubmit = {...form};
    // 如果AI批改未启用，则不提交提示词或提交空字符串
    if (!form.ai_grading_enabled) {
      dataToSubmit.ai_grading_prompt = ''; // 或者后端处理 null/空字符串
    }

    try {
      if (isEdit.value) {
        await updateHomework(route.params.homeworkId, dataToSubmit);
        ElMessage.success('作业更新成功');
      } else {
        await createHomework(dataToSubmit);
        ElMessage.success('作业创建成功');
      }
      goBack();
    } catch (error) {
      ElMessage.error('作业保存失败：' + (error.response?.data?.detail || error.message || '网络错误'));
      console.error("Submit error:", error.response || error);
    } finally {
      loading.value = false;
    }
  });
};

const goBack = () => {
  router.push({name: 'TeacherCourseHomeworks', params: {id: courseClassId.value}});
};

onMounted(async () => {
  await loadCourseClassInfo(); // 先加载课程班级信息
  if (isEdit.value) {
    await loadHomeworkData(); // 如果是编辑模式，再加载作业数据
  } else {
    // 创建新作业时，如果课程信息已加载，可以预填充 course_class ID
    if (courseClass.value) {
      form.course_class = courseClassId.value;
      // 如果需要，此时也可以根据是否默认开启AI批改来初始化提示词
      if (form.ai_grading_enabled && !form.ai_grading_prompt) {
        form.ai_grading_prompt = generatedDefaultPrompt.value;
      }
    }
  }
});

</script>

<style scoped>
.homework-form-container {
  padding: 24px;
  background-color: #f7f8fa;
}

h2 {
  text-align: center;
  margin-bottom: 25px;
  color: #303133;
}

.el-form {
  background-color: #fff;
  padding: 30px;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.el-form-item__label {
  font-weight: bold;
}

.quill-editor-container {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  overflow: hidden; /* 确保圆角生效 */
}

.quill-editor-container .ql-toolbar {
  border-top-left-radius: 4px;
  border-top-right-radius: 4px;
}

.quill-editor-container .ql-container {
  border-bottom-left-radius: 4px;
  border-bottom-right-radius: 4px;
}

.card-header {
  font-size: 16px;
  font-weight: bold;
}
</style>