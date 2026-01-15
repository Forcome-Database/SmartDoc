<script setup lang="ts">
/**
 * 统一内容管理页面
 * 左侧文件树 + 右侧复用原有文档编辑页面
 */
import ContentTree from '~/components/content-tree/ContentTree.vue'
import DocumentEditorPanel from '~/components/content/DocumentEditor.vue'
import type { ContentNode } from '~/components/content-tree/ContentTree.vue'

definePageMeta({
  middleware: ['auth'],
  layout: 'default',
})

const route = useRoute()
const router = useRouter()
const toast = useToast()

// 内容树数据
const { 
  tree, isLoading, fetchTree, createCategory, createDocument,
  renameItem, deleteItem, moveItem, reorderItems, updateDocumentTitle,
} = useContentTree()

// 当前选中的节点
const selectedNode = ref<ContentNode | null>(null)

// 当前编辑的文档 ID
const editingDocumentId = ref<string | null>(null)

// 编辑器刷新 key（用于强制刷新编辑器）
const editorKey = ref(0)

// 内容树组件引用
const contentTreeRef = ref<InstanceType<typeof ContentTree> | null>(null)

// 当前文档信息（用于语言切换时查找对应语言版本）
const currentDocumentInfo = ref<{ slug: string; categoryId: string | null } | null>(null)

// 处理节点选择
const handleSelect = async (node: ContentNode) => {
  selectedNode.value = node
  
  if (node.type === 'document') {
    editingDocumentId.value = node.id
    // 保存当前文档信息，用于语言切换
    currentDocumentInfo.value = {
      slug: node.slug,
      categoryId: node.parentId,
    }
    router.replace({ query: { doc: node.id } })
  }
}

// 处理语言切换 - 自动切换到对应语言的文档
const handleLocaleChange = async (localeCode: string) => {
  if (!editingDocumentId.value || !currentDocumentInfo.value) return
  
  try {
    // 查找对应语言的文档
    const relatedDocs = await $fetch<Array<{
      id: string
      localeCode: string
    }>>(`/api/documents/${editingDocumentId.value}/related`)
    
    const targetDoc = relatedDocs.find(doc => doc.localeCode === localeCode)
    
    if (targetDoc && targetDoc.id !== editingDocumentId.value) {
      // 切换到对应语言的文档
      editingDocumentId.value = targetDoc.id
      router.replace({ query: { doc: targetDoc.id } })
    }
  } catch (e) {
    // 如果查找失败，保持当前文档
    console.error('Failed to find related document:', e)
  }
}

// 处理标题变化 - 实时更新内容树中的标题
const handleTitleChange = (documentId: string, newTitle: string) => {
  updateDocumentTitle(documentId, newTitle)
}

// 处理创建栏目
const handleCreateCategory = async (parentId: string | null, name: string) => {
  try {
    await createCategory(parentId, name)
    toast.add({ title: '栏目创建成功', color: 'success' })
  } catch (e: any) {
    toast.add({ title: '创建失败', description: e.data?.message, color: 'error' })
  }
}

// 处理创建文档
const handleCreateDocument = async (categoryId: string, name: string, localeCode?: string) => {
  try {
    const doc = await createDocument(categoryId, name, localeCode)
    toast.add({ title: '文档创建成功', color: 'success' })
    editingDocumentId.value = doc.id
    router.replace({ query: { doc: doc.id } })
  } catch (e: any) {
    toast.add({ title: '创建失败', description: e.data?.message, color: 'error' })
  }
}

// 处理重命名
const handleRename = async (node: ContentNode, newName: string) => {
  try {
    await renameItem(node, newName)
    toast.add({ title: '重命名成功', color: 'success' })
    // 如果重命名的是当前编辑的文档，刷新编辑器
    if (node.type === 'document' && node.id === editingDocumentId.value) {
      editorKey.value++
    }
  } catch (e: any) {
    toast.add({ title: '重命名失败', description: e.data?.message, color: 'error' })
  }
}

// 处理删除
const handleDelete = async (node: ContentNode) => {
  try {
    await deleteItem(node)
    toast.add({ title: '删除成功', color: 'success' })
    if (node.type === 'document' && node.id === editingDocumentId.value) {
      editingDocumentId.value = null
      selectedNode.value = null
      router.replace({ query: {} })
    }
  } catch (e: any) {
    toast.add({ title: '删除失败', description: e.data?.message, color: 'error' })
  }
}

// 处理移动
const handleMove = async (node: ContentNode, newParentId: string | null, position?: 'before' | 'after' | 'inside', targetNode?: ContentNode) => {
  try {
    await moveItem(node, newParentId, position, targetNode)
    toast.add({ title: '移动成功', color: 'success' })
  } catch (e: any) {
    toast.add({ title: '移动失败', description: e.data?.message, color: 'error' })
  }
}

// 处理排序
const handleReorder = async (items: Array<{ id: string; parentId: string | null; sortOrder: number; type: 'category' | 'document' }>) => {
  try { await reorderItems(items) } catch (e: any) {
    toast.add({ title: '排序失败', description: e.data?.message, color: 'error' })
  }
}

// 初始化
onMounted(async () => {
  await fetchTree()
  const docId = route.query.doc as string
  if (docId) {
    editingDocumentId.value = docId
    // 等待内容树渲染完成后展开到文档
    nextTick(() => {
      contentTreeRef.value?.expandToDocument(docId)
    })
  }
})
</script>

<template>
  <div class="flex h-full">
    <!-- 左侧内容树 -->
    <div class="w-72 border-r border-gray-200 dark:border-gray-800 bg-white/50 dark:bg-gray-900/50 flex flex-col shrink-0">
      <ContentTree
        ref="contentTreeRef"
        :tree="tree"
        :selected-id="editingDocumentId ? `doc-${editingDocumentId}` : null"
        :is-loading="isLoading"
        @select="handleSelect"
        @create-category="handleCreateCategory"
        @create-document="handleCreateDocument"
        @rename="handleRename"
        @delete="handleDelete"
        @move="handleMove"
        @reorder="handleReorder"
        @refresh="fetchTree"
        @locale-change="handleLocaleChange"
      />
    </div>

    <!-- 右侧：复用文档编辑器组件 -->
    <div class="flex-1 flex flex-col min-w-0 overflow-hidden">
      <template v-if="editingDocumentId">
        <!-- 使用 ClientOnly 避免 Hydration 错误 -->
        <ClientOnly>
          <DocumentEditorPanel 
            :key="`${editingDocumentId}-${editorKey}`"
            :document-id="editingDocumentId"
            @title-change="handleTitleChange"
          />
          <template #fallback>
            <div class="flex-1 flex items-center justify-center">
              <UIcon name="i-lucide-loader-2" class="w-8 h-8 animate-spin text-primary-500" />
            </div>
          </template>
        </ClientOnly>
      </template>

      <!-- 空状态 -->
      <div v-else class="flex-1 flex items-center justify-center bg-gray-50 dark:bg-gray-900/50">
        <div class="text-center max-w-md px-6">
          <div class="w-16 h-16 mx-auto mb-4 rounded-2xl bg-gray-100 dark:bg-gray-800 flex items-center justify-center">
            <UIcon name="i-lucide-file-text" class="w-8 h-8 text-gray-400" />
          </div>
          <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-2">选择或创建文档</h3>
          <p class="text-gray-500 dark:text-gray-400 text-sm">在左侧文件树中选择一个文档进行编辑，或右键点击栏目创建新文档</p>
        </div>
      </div>
    </div>
  </div>
</template>
