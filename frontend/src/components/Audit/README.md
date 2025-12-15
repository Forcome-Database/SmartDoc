# 审核工作台组件

## 概述

审核工作台是企业级智能文档处理平台的核心功能模块，提供人工审核和修正文档提取结果的完整界面。

## 组件结构

### 主页面 (AuditWorkbench.vue)

审核工作台主页面，实现左右分栏布局（桌面端）和上下布局（移动端）。

**主要功能：**
- 待审核任务列表管理
- 任务切换（上一个/下一个）
- 草稿自动保存（3秒防抖）
- 审核操作（确认通过/驳回）
- 响应式布局支持

**使用示例：**
```vue
<template>
  <AuditWorkbench />
</template>
```

### PDF预览器 (PDFViewer.vue)

多功能PDF预览组件，支持分页、缩放、旋转、OCR高亮和文本选择。

**主要功能：**
- 分页控制（上一页/下一页/跳转）
- 缩放控制（50%-200%）
- 旋转控制（左转/右转）
- OCR区域高亮显示
- 跨页高亮（点击字段跳转）
- 划词回填（框选文本填入字段）
- 懒加载（超过50页）

**Props：**
- `taskId`: 任务ID（必填）
- `totalPages`: 总页数（必填）
- `initialPage`: 初始页码（默认1）
- `ocrResult`: OCR结果对象
- `enableTextSelection`: 是否启用文本选择（默认true）

**Events：**
- `page-change`: 页码变化
- `box-click`: OCR框点击
- `text-selected`: 文本选中

**使用示例：**
```vue
<PDFViewer
  :task-id="taskId"
  :total-pages="10"
  :ocr-result="ocrResult"
  @box-click="handleBoxClick"
  @text-selected="handleTextSelected"
/>
```

### 数据表单 (DataForm.vue)

动态表单组件，根据Schema自动生成表单字段，支持多种数据类型和置信度显示。

**主要功能：**
- 根据Schema动态生成表单
- 支持多种字段类型（string, int, decimal, date, boolean, table, array）
- 显示字段置信度徽章
- 显示数据来源页码
- 支持字段编辑
- 支持表格和数组操作
- 表单验证

**Props：**
- `modelValue`: 表单数据（必填）
- `schema`: 字段配置Schema（必填）
- `confidenceScores`: 置信度数据
- `sourcePages`: 来源页码数据

**Events：**
- `update:modelValue`: 表单数据更新
- `field-focus`: 字段获得焦点
- `jump-to-page`: 跳转到页面
- `change`: 字段值变化

**使用示例：**
```vue
<DataForm
  v-model="formData"
  :schema="schema"
  :confidence-scores="confidenceScores"
  :source-pages="sourcePages"
  @field-focus="handleFieldFocus"
  @jump-to-page="handleJumpToPage"
/>
```

### 表格编辑器 (TableEditor.vue)

表格数据编辑组件，支持行操作（插入、删除、上移、下移）。

**主要功能：**
- 表格数据展示和编辑
- 插入行
- 删除行
- 上移/下移行
- 单元格编辑

**Props：**
- `value`: 表格数据数组（必填）
- `columns`: 列配置数组（必填）

**Events：**
- `update:value`: 表格数据更新
- `change`: 表格数据变化
- `row-focus`: 行获得焦点

### 数组编辑器 (ArrayEditor.vue)

数组数据编辑组件，支持添加和删除数组项。

**主要功能：**
- 数组项展示和编辑
- 添加项目
- 删除项目

**Props：**
- `value`: 数组数据（必填）
- `itemSchema`: 数组项Schema（必填）

**Events：**
- `update:value`: 数组数据更新
- `change`: 数组数据变化

## 工具函数

### 草稿管理 (draftManager.js)

提供草稿的本地存储和自动保存功能。

**主要函数：**
- `saveDraftToLocal(taskId, data)`: 保存草稿到localStorage
- `loadDraftFromLocal(taskId)`: 从localStorage加载草稿
- `removeDraftFromLocal(taskId)`: 删除localStorage中的草稿
- `cleanExpiredDrafts()`: 清理所有过期草稿（24小时）
- `createDebouncedSave(saveFn, delay)`: 创建防抖保存函数（默认3秒）
- `hasDraft(taskId)`: 检查是否有未保存的草稿

**使用示例：**
```javascript
import {
  saveDraftToLocal,
  loadDraftFromLocal,
  createDebouncedSave
} from '@/utils/draftManager'

// 创建防抖保存函数
const debouncedSave = createDebouncedSave(async () => {
  saveDraftToLocal(taskId, formData)
  await api.saveDraft(taskId, formData)
}, 3000)

// 在数据变化时调用
function onDataChange() {
  debouncedSave()
}

// 加载草稿
const draft = loadDraftFromLocal(taskId)
if (draft) {
  formData.value = draft
}
```

## API接口

### 审核API (audit.js)

提供审核工作台相关的API接口。

**接口列表：**
- `getPendingTasks(params)`: 获取待审核任务列表
- `getTaskDetail(taskId)`: 获取审核任务详情
- `getPagePreview(taskId, page)`: 获取PDF页面预览
- `saveDraft(taskId, data)`: 保存草稿
- `submitAudit(taskId, data)`: 提交审核

## 响应式设计

### 桌面端（>768px）
- 左右分栏布局
- 左侧：PDF预览器（占据剩余空间）
- 右侧：数据表单（固定宽度480px）

### 移动端（≤768px）
- 上下布局
- 使用Tab切换PDF预览和数据表单
- 操作按钮改为块级按钮

## 需求映射

本模块实现了以下需求：

- **Requirement 16**: 审核工作台 - 多页PDF预览
  - 左右分栏布局
  - PDF预览和分页器
  - 缩放和旋转功能
  - 懒加载机制（超过50页）
  - 跨页高亮和跳转
  - 划词回填

- **Requirement 17**: 审核工作台 - 数据修正和提交
  - 动态表单生成
  - 字段编辑
  - 表格操作（插入、删除、上移、下移）
  - 确认通过和驳回按钮
  - 审核提交API调用

- **Requirement 30**: 草稿自动保存
  - 防抖保存（3秒）
  - localStorage存储
  - API保存
  - 草稿已保存提示

- **Requirement 33**: OCR结果 - 坐标信息存储
  - OCR区域框绘制
  - 高亮显示
  - 点击跳转

- **Requirement 41**: 置信度分数显示
  - 置信度徽章
  - 颜色标识（高/中/低）
  - 警告图标

- **Requirement 63**: 响应式设计
  - 桌面端左右分栏
  - 移动端上下布局
  - 触摸友好的交互

## 开发注意事项

1. **性能优化**
   - PDF预览使用懒加载
   - 草稿保存使用防抖
   - 大表格使用虚拟滚动

2. **用户体验**
   - 提供清晰的加载状态
   - 操作后给予及时反馈
   - 支持键盘快捷键

3. **数据安全**
   - 草稿定期清理（24小时）
   - 敏感数据不存储在localStorage
   - API调用失败时保留本地草稿

4. **可访问性**
   - 使用语义化HTML
   - 提供键盘导航支持
   - 适当的ARIA标签

## 未来改进

- [ ] 支持批量审核
- [ ] 添加审核历史记录
- [ ] 支持自定义快捷键
- [ ] 添加审核统计面板
- [ ] 支持多人协同审核
- [ ] 添加审核质量评分
