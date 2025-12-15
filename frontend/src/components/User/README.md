# 用户管理组件

## 组件说明

用户管理模块包含用户列表页面和用户编辑对话框，实现了完整的用户CRUD功能。

## 组件列表

### UserDialog.vue

用户编辑对话框组件，支持创建和编辑用户。

**功能特性：**
- 创建新用户（用户名、邮箱、角色、密码）
- 编辑现有用户（邮箱、角色、可选修改密码）
- 表单验证（用户名格式、邮箱格式、密码强度、密码确认）
- 角色选择（Admin、Architect、Auditor、Visitor）

**Props：**
- `visible` (Boolean): 对话框显示状态
- `user` (Object): 编辑的用户对象，null表示创建新用户

**Events：**
- `update:visible`: 更新对话框显示状态
- `success`: 操作成功后触发

**使用示例：**
```vue
<UserDialog
  v-model:visible="dialogVisible"
  :user="currentUser"
  @success="handleSuccess"
/>
```

## 页面说明

### UserManagement.vue

用户管理主页面，展示用户列表和管理功能。

**功能特性：**
- 用户列表展示（用户名、邮箱、角色、状态、创建时间、最后登录时间）
- 搜索和筛选（按用户名、邮箱、角色筛选）
- 分页显示
- 新建用户
- 编辑用户
- 启用/禁用用户
- 删除用户（不能删除自己）
- 角色标签颜色区分
- 响应式设计

**权限要求：**
- 仅Admin角色可访问

## API接口

### getUserList(params)
获取用户列表

**参数：**
- `page`: 页码
- `page_size`: 每页数量
- `username`: 用户名筛选（可选）
- `email`: 邮箱筛选（可选）
- `role`: 角色筛选（可选）

### createUser(data)
创建用户

**参数：**
- `username`: 用户名
- `email`: 邮箱
- `role`: 角色
- `password`: 密码

### updateUser(userId, data)
更新用户信息

**参数：**
- `userId`: 用户ID
- `data`: 更新数据（email、role、password可选）

### updateUserStatus(userId, isActive)
更新用户状态

**参数：**
- `userId`: 用户ID
- `isActive`: 是否激活

### deleteUser(userId)
删除用户

**参数：**
- `userId`: 用户ID

## 角色说明

- **Admin（超级管理员）**：全部功能权限
- **Architect（规则架构师）**：规则管理权限
- **Auditor（业务审核员）**：审核工作台权限
- **Visitor（API访客）**：API Key生成和查看权限

## 样式说明

- 使用Ant Design Vue组件库
- 响应式设计，支持移动端
- 角色标签颜色区分：
  - Admin: 红色
  - Architect: 蓝色
  - Auditor: 绿色
  - Visitor: 灰色

## 注意事项

1. 用户名创建后不可修改
2. 编辑用户时，密码字段为可选，留空则不修改密码
3. 不能删除当前登录的用户
4. 禁用用户后，该用户将无法登录系统
5. 删除用户前会进行二次确认
6. 所有操作都会记录到审计日志

## 相关需求

- Requirement 49: Account Management - User CRUD Operations
- Requirement 5: Role-Based Access Control
