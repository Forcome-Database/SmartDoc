<template>
  <div class="rule-editor-container">
    <!-- 顶部操作栏 -->
    <div class="editor-header bg-white border-b px-6 py-4">
      <div class="flex justify-between items-center">
        <div class="flex items-center space-x-4">
          <a-button @click="handleBack">
            <template #icon><ArrowLeftOutlined /></template>
            返回
          </a-button>
          <div>
            <h1 class="text-xl font-bold text-gray-800">{{ ruleData.name || '新建规则' }}</h1>
            <p class="text-sm text-gray-500">{{ ruleData.code || '' }}</p>
          </div>
        </div>

        <div class="flex items-center space-x-3">
          <!-- 版本选择器 -->
          <a-select
            v-model:value="currentVersion"
            style="width: 150px"
            @change="handleVersionChange"
          >
            <a-select-option
              v-for="version in versions"
              :key="version.version"
              :value="version.version"
            >
              {{ version.version }} ({{ getVersionStatusLabel(version.status) }})
            </a-select-option>
          </a-select>

          <!-- 操作按钮 -->
          <a-button @click="handleSave" :loading="saving">
            <template #icon><SaveOutlined /></template>
            保存
          </a-button>
          <a-button 
            type="primary" 
            @click="handlePublish" 
            :loading="publishing"
            :disabled="!canPublish()"
            :title="canPublish() ? '发布当前草稿版本' : '只有草稿版本可以发布'"
          >
            <template #icon><RocketOutlined /></template>
            发布
          </a-button>
          <a-dropdown>
            <a-button>
              更多 <DownOutlined />
            </a-button>
            <template #overlay>
              <a-menu>
                <a-menu-item @click="handleRollback">
                  <RollbackOutlined /> 回滚版本
                </a-menu-item>
                <a-menu-item @click="handleViewHistory">
                  <HistoryOutlined /> 版本历史
                </a-menu-item>
                <a-menu-divider />
                <a-menu-item @click="handleOpenSandbox">
                  <ExperimentOutlined /> 沙箱测试
                </a-menu-item>
              </a-menu>
            </template>
          </a-dropdown>
        </div>
      </div>
    </div>

    <!-- 主内容区 -->
    <div class="editor-content flex">
      <!-- 左侧标签页 -->
      <div class="flex-1 bg-white">
        <a-tabs v-model:activeKey="activeTab" class="editor-tabs">
          <a-tab-pane key="basic" tab="基础配置">
            <BasicConfig
              v-if="activeTab === 'basic'"
              v-model:config="ruleConfig.basic"
            />
          </a-tab-pane>
          <a-tab-pane key="schema" tab="Schema定义">
            <SchemaEditor
              v-if="activeTab === 'schema'"
              v-model:schema="ruleConfig.schema"
            />
          </a-tab-pane>
          <a-tab-pane key="extraction" tab="提取策略">
            <ExtractionConfig
              v-if="activeTab === 'extraction'"
              v-model:config="ruleConfig.extraction"
              :schema="ruleConfig.schema"
            />
          </a-tab-pane>
          <a-tab-pane key="validation" tab="清洗校验">
            <ValidationConfig
              v-if="activeTab === 'validation'"
              v-model:config="ruleConfig.validation"
              :schema="ruleConfig.schema"
            />
          </a-tab-pane>
          <a-tab-pane key="enhancement" tab="增强风控">
            <EnhancementConfig
              v-if="activeTab === 'enhancement'"
              v-model:config="ruleConfig.enhancement"
            />
          </a-tab-pane>
        </a-tabs>
      </div>

      <!-- 右侧沙箱测试面板（可折叠） -->
      <div
        v-if="sandboxVisible"
        class="sandbox-panel bg-white border-l"
        :style="{ width: sandboxWidth + 'px' }"
      >
        <SandboxPanel
          :rule-id="ruleId"
          :config="ruleConfig"
          @close="sandboxVisible = false"
        />
      </div>
    </div>

    <!-- 版本历史对话框 -->
    <VersionDialog
      v-model:open="versionDialogVisible"
      :rule-id="ruleId"
      :versions="versions"
      @rollback="handleVersionRollback"
    />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message, Modal } from 'ant-design-vue'
import {
  ArrowLeftOutlined,
  SaveOutlined,
  RocketOutlined,
  DownOutlined,
  RollbackOutlined,
  HistoryOutlined,
  ExperimentOutlined
} from '@ant-design/icons-vue'
import { ruleAPI } from '@/api/rule'
import BasicConfig from '@/components/RuleEditor/BasicConfig.vue'
import SchemaEditor from '@/components/RuleEditor/SchemaEditor.vue'
import ExtractionConfig from '@/components/RuleEditor/ExtractionConfig.vue'
import ValidationConfig from '@/components/RuleEditor/ValidationConfig.vue'
import EnhancementConfig from '@/components/RuleEditor/EnhancementConfig.vue'
import SandboxPanel from '@/components/RuleEditor/SandboxPanel.vue'
import VersionDialog from '@/components/RuleEditor/VersionDialog.vue'

const route = useRoute()
const router = useRouter()

// 路由参数
const ruleId = ref(route.params.id)

// 数据状态
const loading = ref(false)
const saving = ref(false)
const publishing = ref(false)
const ruleData = ref({
  name: '',
  code: '',
  document_type: '',
  current_version: null
})
const versions = ref([])
const currentVersion = ref('')
const activeTab = ref('basic')

// 沙箱面板
const sandboxVisible = ref(false)
const sandboxWidth = ref(400)

// 版本对话框
const versionDialogVisible = ref(false)

// 规则配置
const ruleConfig = reactive({
  basic: {
    ocrEngine: 'paddleocr',
    language: 'zh',
    pageStrategy: 'multi_page',
    pageSeparator: '\n'
  },
  schema: {},
  extraction: {},
  validation: {},
  enhancement: {}
})

// 加载规则数据
const loadRuleData = async () => {
  if (!ruleId.value) return
  
  loading.value = true
  try {
    const response = await ruleAPI.get(ruleId.value)
    ruleData.value = response
    
    // 加载版本列表
    await loadVersions()
  } catch (error) {
    message.error('加载规则数据失败：' + (error.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

// 加载版本列表
const loadVersions = async () => {
  try {
    const response = await ruleAPI.getVersions(ruleId.value)
    versions.value = response.items || []
    
    // 设置当前版本
    if (versions.value.length > 0) {
      const draftVersion = versions.value.find(v => v.status === 'draft')
      currentVersion.value = draftVersion ? draftVersion.version : versions.value[0].version
      
      // 加载版本配置
      await loadVersionConfig(currentVersion.value)
    }
  } catch (error) {
    message.error('加载版本列表失败：' + (error.message || '未知错误'))
  }
}

// 加载版本配置
const loadVersionConfig = async (version) => {
  try {
    // 从服务器重新获取版本列表以确保数据最新
    const response = await ruleAPI.getVersions(ruleId.value)
    versions.value = response.items || []
    
    const versionData = versions.value.find(v => v.version === version)
    if (versionData && versionData.config) {
      console.log('Loading config from version:', version, versionData.config)
      
      // 深度合并配置，确保每个子对象都被正确更新
      // 使用深拷贝避免引用问题
      if (versionData.config.basic) {
        // 完全替换basic配置
        Object.keys(ruleConfig.basic).forEach(key => {
          if (versionData.config.basic[key] !== undefined) {
            ruleConfig.basic[key] = versionData.config.basic[key]
          }
        })
      }
      if (versionData.config.schema !== undefined) {
        ruleConfig.schema = JSON.parse(JSON.stringify(versionData.config.schema))
      }
      if (versionData.config.extraction !== undefined) {
        ruleConfig.extraction = JSON.parse(JSON.stringify(versionData.config.extraction))
      }
      if (versionData.config.validation !== undefined) {
        ruleConfig.validation = JSON.parse(JSON.stringify(versionData.config.validation))
      }
      if (versionData.config.enhancement !== undefined) {
        ruleConfig.enhancement = JSON.parse(JSON.stringify(versionData.config.enhancement))
      }
      
      console.log('Loaded config:', JSON.parse(JSON.stringify(ruleConfig)))
    }
  } catch (error) {
    console.error('加载版本配置失败:', error)
    message.error('加载版本配置失败：' + (error.message || '未知错误'))
  }
}

// 版本切换
const handleVersionChange = async (version) => {
  await loadVersionConfig(version)
  message.success(`已切换到版本 ${version}`)
}

// 保存配置
const handleSave = async () => {
  saving.value = true
  try {
    // 找到当前版本的ID
    const currentVersionObj = versions.value.find(v => v.version === currentVersion.value)
    if (!currentVersionObj) {
      message.error('未找到当前版本')
      return
    }
    
    console.log('RuleEditor: Saving config:', ruleConfig)
    
    // 调用API更新配置
    await ruleAPI.updateVersion(ruleId.value, currentVersionObj.id, { config: ruleConfig })
    message.success('保存成功')
  } catch (error) {
    message.error('保存失败：' + (error.message || '未知错误'))
  } finally {
    saving.value = false
  }
}

// 发布版本
const handlePublish = () => {
  Modal.confirm({
    title: '确认发布',
    content: '发布后将创建新版本并应用到生产环境，确定要发布吗？',
    okText: '确认发布',
    cancelText: '取消',
    onOk: async () => {
      publishing.value = true
      try {
        // 找到当前版本的ID
        const currentVersionObj = versions.value.find(v => v.version === currentVersion.value)
        if (!currentVersionObj) {
          message.error('未找到当前版本')
          return
        }
        
        await ruleAPI.publish(ruleId.value, { version_id: currentVersionObj.id })
        message.success('发布成功')
        await loadVersions()
      } catch (error) {
        message.error('发布失败：' + (error.message || '未知错误'))
      } finally {
        publishing.value = false
      }
    }
  })
}

// 回滚版本
const handleRollback = () => {
  versionDialogVisible.value = true
}

// 执行版本回滚
const handleVersionRollback = async (versionId) => {
  try {
    await ruleAPI.rollback(ruleId.value, { version_id: versionId })
    message.success('回滚成功')
    await loadVersions()
    versionDialogVisible.value = false
  } catch (error) {
    message.error('回滚失败：' + (error.message || '未知错误'))
  }
}

// 查看版本历史
const handleViewHistory = () => {
  versionDialogVisible.value = true
}

// 打开沙箱测试
const handleOpenSandbox = () => {
  Modal.confirm({
    title: '提示',
    content: '沙箱测试将使用当前保存的配置。如果您修改了配置但未保存，请先点击"保存"按钮。',
    okText: '继续测试',
    cancelText: '先保存配置',
    onOk: () => {
      sandboxVisible.value = true
    },
    onCancel: async () => {
      await handleSave()
      sandboxVisible.value = true
    }
  })
}

// 返回列表
const handleBack = () => {
  router.push('/rules')
}

// 获取版本状态标签
const getVersionStatusLabel = (status) => {
  const labels = {
    draft: '草稿',
    published: '已发布',
    archived: '已归档'
  }
  return labels[status] || status
}

// 判断当前版本是否可发布（只有草稿版本可以发布）
const canPublish = () => {
  const currentVersionObj = versions.value.find(v => v.version === currentVersion.value)
  return currentVersionObj && currentVersionObj.status === 'draft'
}

// 页面加载
onMounted(() => {
  loadRuleData()
})

// 监听路由变化
watch(() => route.params.id, (newId) => {
  if (newId) {
    ruleId.value = newId
    loadRuleData()
  }
})
</script>

<style scoped>
.rule-editor-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: #f5f5f5;
}

.editor-header {
  flex-shrink: 0;
}

.editor-content {
  flex: 1;
  overflow: hidden;
  min-height: 0; /* 修复 flex 子元素高度计算问题 */
}

.editor-tabs {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.editor-tabs :deep(.ant-tabs-nav) {
  flex-shrink: 0;
}

.editor-tabs :deep(.ant-tabs-content-holder) {
  flex: 1;
  overflow: hidden;
}

.editor-tabs :deep(.ant-tabs-content) {
  height: 100%;
}

.editor-tabs :deep(.ant-tabs-tabpane) {
  height: 100%;
  overflow-y: auto;
  padding: 24px;
}

.sandbox-panel {
  flex-shrink: 0;
  overflow-y: auto;
}
</style>
