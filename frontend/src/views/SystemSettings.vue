<template>
  <div class="system-settings">
    <a-card :bordered="false">
      <template #title>
        <div class="flex items-center justify-between">
          <span class="text-lg font-semibold">系统设置</span>
          <a-tag color="orange">仅管理员可访问</a-tag>
        </div>
      </template>

      <a-tabs v-model:activeKey="activeTab" type="card">
        <!-- 数据生命周期标签页 -->
        <a-tab-pane key="retention" tab="数据生命周期">
          <template #tab>
            <span>
              <ClockCircleOutlined />
              数据生命周期
            </span>
          </template>
          <RetentionConfig />
        </a-tab-pane>

        <!-- 全局配置标签页 -->
        <a-tab-pane key="global" tab="全局配置">
          <template #tab>
            <span>
              <SettingOutlined />
              全局配置
            </span>
          </template>
          <GlobalConfig />
        </a-tab-pane>

        <!-- 审计日志标签页 -->
        <a-tab-pane key="audit" tab="审计日志">
          <template #tab>
            <span>
              <FileTextOutlined />
              审计日志
            </span>
          </template>
          <AuditLogs />
        </a-tab-pane>
      </a-tabs>
    </a-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { 
  ClockCircleOutlined, 
  SettingOutlined, 
  FileTextOutlined 
} from '@ant-design/icons-vue'
import RetentionConfig from '@/components/Settings/RetentionConfig.vue'
import GlobalConfig from '@/components/Settings/GlobalConfig.vue'
import AuditLogs from '@/components/Settings/AuditLogs.vue'

/**
 * 当前激活的标签页
 */
const activeTab = ref('retention')
</script>

<style scoped>
.system-settings {
  padding: 24px;
}

:deep(.ant-tabs-card > .ant-tabs-nav .ant-tabs-tab) {
  padding: 8px 16px;
  background: #fafafa;
  border-color: #d9d9d9;
}

:deep(.ant-tabs-card > .ant-tabs-nav .ant-tabs-tab-active) {
  background: #fff;
  border-bottom-color: #fff;
}

:deep(.ant-tabs-content) {
  padding: 24px 0;
}
</style>
