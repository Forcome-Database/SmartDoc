# 系统设置组件

系统设置模块包含三个主要功能组件，用于管理系统的全局配置、数据生命周期和审计日志。

## 组件列表

### 1. RetentionConfig.vue - 数据生命周期配置

**功能说明：**
- 配置原始文件（PDF/图片）的留存期限
- 配置提取数据（JSON结果）的留存期限
- 显示下次自动清理时间（每日凌晨02:00）
- 显示最近一次清理的统计信息

**主要特性：**
- 支持1-365天的文件留存期配置
- 支持永久保留或自定义天数的数据留存期
- 实时显示下次清理时间
- 展示清理历史记录（删除文件数、释放空间）

**API依赖：**
- `GET /v1/system/retention` - 获取留存期配置
- `PUT /v1/system/retention` - 更新留存期配置

### 2. GlobalConfig.vue - 全局配置

**功能说明：**
- 配置OCR处理相关参数（超时时间、并行数）
- 配置LLM服务相关参数（超时时间、Token单价）
- 配置任务队列参数（最大长度、Worker并发数）
- 配置性能参数（数据库连接池、Redis缓存TTL）

**配置项说明：**

**OCR配置：**
- OCR超时时间：30-600秒，默认300秒
- 最大并行OCR任务数：1-16个，默认4个

**LLM配置：**
- LLM超时时间：10-300秒，默认60秒
- LLM Token单价：用于成本估算，默认0.002元/Token

**任务队列配置：**
- 消息队列最大长度：100-100000条，默认10000条
- Worker并发数：1-50个，默认5个

**性能配置：**
- 数据库连接池大小：5-100个，默认20个
- Redis缓存过期时间：60-86400秒，默认3600秒

**主要特性：**
- 所有配置修改后立即生效，无需重启服务
- 支持恢复默认值功能
- 显示最后更新时间和更新人
- 表单验证确保配置值在合理范围内

**API依赖：**
- `GET /v1/system/config` - 获取所有系统配置
- `PUT /v1/system/config/{key}` - 更新单个配置项

### 3. AuditLogs.vue - 审计日志查询

**功能说明：**
- 查询和展示系统操作审计日志
- 支持多维度筛选（时间、操作类型、资源类型、用户）
- 支持导出审计日志为CSV文件
- 查看详细的变更内容

**筛选条件：**
- 时间范围：支持日期范围选择
- 操作类型：登录、登出、创建、更新、删除、发布、审核
- 资源类型：用户、规则、任务、Webhook、系统配置
- 用户：支持按用户ID或用户名搜索

**日志信息：**
- 操作类型和资源类型（带颜色标签）
- 资源ID
- 操作人信息
- IP地址
- 变更内容（可查看详情）
- 操作时间

**主要特性：**
- 默认显示最近7天的日志
- 支持分页查询
- 点击查看详细的变更内容（JSON格式）
- 支持导出筛选后的日志为CSV文件
- 显示User Agent等详细信息

**API依赖：**
- `GET /v1/audit-logs` - 获取审计日志列表
- `GET /v1/audit-logs/export` - 导出审计日志

## 使用方式

### 在SystemSettings.vue中使用

```vue
<template>
  <a-tabs v-model:activeKey="activeTab">
    <a-tab-pane key="retention" tab="数据生命周期">
      <RetentionConfig />
    </a-tab-pane>
    
    <a-tab-pane key="global" tab="全局配置">
      <GlobalConfig />
    </a-tab-pane>
    
    <a-tab-pane key="audit" tab="审计日志">
      <AuditLogs />
    </a-tab-pane>
  </a-tabs>
</template>

<script setup>
import RetentionConfig from '@/components/Settings/RetentionConfig.vue'
import GlobalConfig from '@/components/Settings/GlobalConfig.vue'
import AuditLogs from '@/components/Settings/AuditLogs.vue'
</script>
```

## 权限要求

所有系统设置功能仅限**Admin（超级管理员）**角色访问。

路由配置：
```javascript
{
  path: 'settings',
  name: 'SystemSettings',
  component: () => import('@/views/SystemSettings.vue'),
  meta: { 
    title: '系统设置',
    icon: 'SettingOutlined',
    roles: ['admin']
  }
}
```

## 依赖项

### API模块
- `@/api/system` - 系统配置API
- `@/api/auditLog` - 审计日志API

### UI组件
- Ant Design Vue 4.2+
- dayjs - 日期处理

### 图标
- `@ant-design/icons-vue`

## 注意事项

1. **配置修改影响**：全局配置的修改会立即影响系统行为，请谨慎操作
2. **数据清理**：文件留存期配置会影响自动清理任务，请根据实际需求设置
3. **审计日志**：审计日志不可修改或删除，确保操作可追溯
4. **导出限制**：大量日志导出可能需要较长时间，建议使用筛选条件缩小范围

## 后续优化建议

1. 添加配置变更的二次确认
2. 支持配置模板和快速切换
3. 审计日志支持更多导出格式（Excel、JSON）
4. 添加配置变更的影响评估提示
5. 支持审计日志的高级搜索（正则表达式）
