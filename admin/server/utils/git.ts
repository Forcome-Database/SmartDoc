/**
 * Git 发布服务
 * 将文档发布到 VitePress docs 目录
 * 
 * Requirements: 5.1, 5.2, 5.5, 5.7
 * - 5.1: 发布文档到 docs/ 目录
 * - 5.2: 创建 Git commit
 * - 5.5: 显示同步状态
 * - 5.7: 支持批量发布
 */
import simpleGit, { type SimpleGit, type StatusResult } from 'simple-git'
import { promises as fs } from 'fs'
import path from 'path'

// 同步状态类型
export type SyncStatus = 'synced' | 'ahead' | 'behind' | 'diverged' | 'error'

// 发布结果类型
export interface PublishResult {
  success: boolean
  commitHash?: string
  filePath?: string
  error?: string
}

// 批量发布结果类型
export interface BatchPublishResult {
  success: boolean
  commitHash?: string
  publishedCount: number
  failedCount: number
  results: Array<{
    documentId: string
    success: boolean
    filePath?: string
    error?: string
  }>
}

// 文档发布参数
export interface PublishDocumentParams {
  slug: string
  locale: string
  content: string
  title: string
  categoryPath?: string
  authorName: string
  authorEmail: string
}

// 批量发布文档参数
export interface BatchPublishDocumentParams {
  documentId: string
  slug: string
  locale: string
  content: string
  title: string
  categoryPath?: string
}

/**
 * Git 发布服务类
 */
export class GitService {
  private git: SimpleGit
  private docsRoot: string
  private initialized: boolean = false

  constructor() {
    const config = useRuntimeConfig()
    // 解析 docs 目录路径（相对于项目根目录）
    this.docsRoot = path.resolve(process.cwd(), config.docsRoot || '../docs')
    this.git = simpleGit(this.docsRoot)
  }

  /**
   * 初始化 Git 仓库检查
   */
  private async ensureInitialized(): Promise<void> {
    if (this.initialized) return

    try {
      // 检查是否是 Git 仓库
      const isRepo = await this.git.checkIsRepo()
      if (!isRepo) {
        throw new Error('docs 目录不是 Git 仓库')
      }
      this.initialized = true
    } catch (error) {
      console.error('Git 初始化失败:', error)
      throw error
    }
  }

  /**
   * 构建文档文件路径
   * 格式: docs/{locale}/{categoryPath}/{slug}.md
   */
  private buildFilePath(locale: string, slug: string, categoryPath?: string): string {
    if (categoryPath) {
      return path.join(locale, categoryPath, `${slug}.md`)
    }
    return path.join(locale, `${slug}.md`)
  }

  /**
   * 生成 Markdown 文件内容（带 frontmatter）
   * 注意：md-editor-v3 保存的内容已经是 Markdown 格式，无需转换
   */
  private generateMarkdownContent(title: string, content: string): string {
    // 添加 frontmatter
    return `---
title: ${title}
---

${content}`
  }

  /**
   * 发布单个文档
   * 
   * @param params 发布参数
   * @returns 发布结果
   */
  async publishDocument(params: PublishDocumentParams): Promise<PublishResult> {
    const { slug, locale, content, title, categoryPath, authorName, authorEmail } = params

    try {
      await this.ensureInitialized()

      // 构建文件路径
      const relativePath = this.buildFilePath(locale, slug, categoryPath)
      const absolutePath = path.join(this.docsRoot, relativePath)

      // 确保目录存在
      await fs.mkdir(path.dirname(absolutePath), { recursive: true })

      // 生成文件内容
      const fileContent = this.generateMarkdownContent(title, content)

      // 写入文件
      await fs.writeFile(absolutePath, fileContent, 'utf-8')

      // Git 操作
      await this.git.add(relativePath)

      // 检查是否有变更
      const status = await this.git.status()
      const hasChanges = status.staged.length > 0

      if (!hasChanges) {
        return {
          success: true,
          filePath: relativePath,
          commitHash: undefined, // 没有变更，无需提交
        }
      }

      // 创建提交
      const commitMessage = `docs(${locale}): update ${slug}`
      const commit = await this.git.commit(commitMessage, relativePath, {
        '--author': `${authorName} <${authorEmail}>`,
      })

      return {
        success: true,
        commitHash: commit.commit || undefined,
        filePath: relativePath,
      }
    } catch (error) {
      console.error('Git 发布错误:', error)
      return {
        success: false,
        error: error instanceof Error ? error.message : '发布失败',
      }
    }
  }

  /**
   * 批量发布文档
   * 
   * @param documents 文档列表
   * @param author 作者信息
   * @returns 批量发布结果
   */
  async publishBatch(
    documents: BatchPublishDocumentParams[],
    author: { name: string; email: string }
  ): Promise<BatchPublishResult> {
    const results: BatchPublishResult['results'] = []
    const filesToCommit: string[] = []

    try {
      await this.ensureInitialized()

      // 处理每个文档
      for (const doc of documents) {
        try {
          const relativePath = this.buildFilePath(doc.locale, doc.slug, doc.categoryPath)
          const absolutePath = path.join(this.docsRoot, relativePath)

          // 确保目录存在
          await fs.mkdir(path.dirname(absolutePath), { recursive: true })

          // 生成文件内容
          const fileContent = this.generateMarkdownContent(doc.title, doc.content)

          // 写入文件
          await fs.writeFile(absolutePath, fileContent, 'utf-8')

          filesToCommit.push(relativePath)
          results.push({
            documentId: doc.documentId,
            success: true,
            filePath: relativePath,
          })
        } catch (error) {
          results.push({
            documentId: doc.documentId,
            success: false,
            error: error instanceof Error ? error.message : '写入文件失败',
          })
        }
      }

      // 如果没有成功的文件，直接返回
      if (filesToCommit.length === 0) {
        return {
          success: false,
          publishedCount: 0,
          failedCount: results.length,
          results,
        }
      }

      // Git 添加所有文件
      await this.git.add(filesToCommit)

      // 检查是否有变更
      const status = await this.git.status()
      const hasChanges = status.staged.length > 0

      if (!hasChanges) {
        return {
          success: true,
          publishedCount: filesToCommit.length,
          failedCount: results.filter(r => !r.success).length,
          results,
        }
      }

      // 创建提交
      const commitMessage = `docs: batch update ${filesToCommit.length} documents`
      const commit = await this.git.commit(commitMessage, filesToCommit, {
        '--author': `${author.name} <${author.email}>`,
      })

      return {
        success: true,
        commitHash: commit.commit || undefined,
        publishedCount: filesToCommit.length,
        failedCount: results.filter(r => !r.success).length,
        results,
      }
    } catch (error) {
      console.error('Git 批量发布错误:', error)
      return {
        success: false,
        publishedCount: 0,
        failedCount: documents.length,
        results: results.length > 0 ? results : documents.map(d => ({
          documentId: d.documentId,
          success: false,
          error: error instanceof Error ? error.message : '批量发布失败',
        })),
      }
    }
  }

  /**
   * 获取同步状态
   * 
   * @returns 同步状态
   */
  async getSyncStatus(): Promise<SyncStatus> {
    try {
      await this.ensureInitialized()

      // 获取远程更新
      await this.git.fetch()

      // 获取状态
      const status = await this.git.status()

      if (status.ahead > 0 && status.behind > 0) {
        return 'diverged'
      }
      if (status.ahead > 0) {
        return 'ahead'
      }
      if (status.behind > 0) {
        return 'behind'
      }
      return 'synced'
    } catch (error) {
      console.error('获取同步状态失败:', error)
      return 'error'
    }
  }

  /**
   * 获取详细状态信息
   */
  async getDetailedStatus(): Promise<{
    syncStatus: SyncStatus
    ahead: number
    behind: number
    modified: string[]
    staged: string[]
    untracked: string[]
  }> {
    try {
      await this.ensureInitialized()

      // 获取远程更新
      await this.git.fetch()

      // 获取状态
      const status = await this.git.status()

      let syncStatus: SyncStatus = 'synced'
      if (status.ahead > 0 && status.behind > 0) {
        syncStatus = 'diverged'
      } else if (status.ahead > 0) {
        syncStatus = 'ahead'
      } else if (status.behind > 0) {
        syncStatus = 'behind'
      }

      return {
        syncStatus,
        ahead: status.ahead,
        behind: status.behind,
        modified: status.modified,
        staged: status.staged,
        untracked: status.not_added,
      }
    } catch (error) {
      console.error('获取详细状态失败:', error)
      return {
        syncStatus: 'error',
        ahead: 0,
        behind: 0,
        modified: [],
        staged: [],
        untracked: [],
      }
    }
  }

  /**
   * 推送到远程仓库
   * 
   * @returns 是否成功
   */
  async push(): Promise<boolean> {
    try {
      await this.ensureInitialized()
      await this.git.push()
      return true
    } catch (error) {
      console.error('Git 推送失败:', error)
      return false
    }
  }

  /**
   * 拉取远程更新
   * 
   * @returns 是否成功
   */
  async pull(): Promise<boolean> {
    try {
      await this.ensureInitialized()
      await this.git.pull()
      return true
    } catch (error) {
      console.error('Git 拉取失败:', error)
      return false
    }
  }

  /**
   * 检查文档是否已发布（文件是否存在）
   */
  async isDocumentPublished(locale: string, slug: string, categoryPath?: string): Promise<boolean> {
    try {
      const relativePath = this.buildFilePath(locale, slug, categoryPath)
      const absolutePath = path.join(this.docsRoot, relativePath)
      await fs.access(absolutePath)
      return true
    } catch {
      return false
    }
  }

  /**
   * 删除已发布的文档
   */
  async deleteDocument(
    locale: string,
    slug: string,
    categoryPath: string | undefined,
    author: { name: string; email: string }
  ): Promise<PublishResult> {
    try {
      await this.ensureInitialized()

      const relativePath = this.buildFilePath(locale, slug, categoryPath)
      const absolutePath = path.join(this.docsRoot, relativePath)

      // 检查文件是否存在
      try {
        await fs.access(absolutePath)
      } catch {
        return {
          success: true,
          filePath: relativePath,
        }
      }

      // 删除文件
      await fs.unlink(absolutePath)

      // Git 操作
      await this.git.add(relativePath)

      // 创建提交
      const commitMessage = `docs(${locale}): delete ${slug}`
      const commit = await this.git.commit(commitMessage, relativePath, {
        '--author': `${author.name} <${author.email}>`,
      })

      return {
        success: true,
        commitHash: commit.commit || undefined,
        filePath: relativePath,
      }
    } catch (error) {
      console.error('Git 删除文档错误:', error)
      return {
        success: false,
        error: error instanceof Error ? error.message : '删除失败',
      }
    }
  }

  /**
   * 删除栏目目录（所有语言版本）
   * 当栏目被删除时，清理 docs 目录下对应的空目录
   * 
   * @param categoryPath 栏目路径（如 "parent-slug/child-slug"）
   * @param locales 所有语言代码列表
   * @param author 作者信息
   */
  async deleteDirectory(
    categoryPath: string,
    locales: string[],
    author: { name: string; email: string }
  ): Promise<PublishResult> {
    try {
      await this.ensureInitialized()

      const deletedPaths: string[] = []

      // 遍历所有语言，删除对应目录
      for (const locale of locales) {
        const relativePath = path.join(locale, categoryPath)
        const absolutePath = path.join(this.docsRoot, relativePath)

        try {
          // 检查目录是否存在
          const stat = await fs.stat(absolutePath)
          if (!stat.isDirectory()) continue

          // 检查目录是否为空
          const files = await fs.readdir(absolutePath)
          if (files.length > 0) {
            console.warn(`目录不为空，跳过删除: ${relativePath}`)
            continue
          }

          // 删除空目录
          await fs.rmdir(absolutePath)
          deletedPaths.push(relativePath)
        } catch (error) {
          // 目录不存在，跳过
          continue
        }
      }

      // 如果没有删除任何目录，直接返回
      if (deletedPaths.length === 0) {
        return {
          success: true,
        }
      }

      // Git 操作 - 添加删除的目录
      for (const deletedPath of deletedPaths) {
        await this.git.add(deletedPath)
      }

      // 检查是否有变更
      const status = await this.git.status()
      if (status.staged.length === 0 && status.deleted.length === 0) {
        return {
          success: true,
        }
      }

      // 创建提交
      const commitMessage = `docs: delete category directory ${categoryPath}`
      const commit = await this.git.commit(commitMessage, deletedPaths, {
        '--author': `${author.name} <${author.email}>`,
      })

      return {
        success: true,
        commitHash: commit.commit || undefined,
        filePath: deletedPaths.join(', '),
      }
    } catch (error) {
      console.error('Git 删除目录错误:', error)
      return {
        success: false,
        error: error instanceof Error ? error.message : '删除目录失败',
      }
    }
  }
}

// 单例实例
let gitService: GitService | null = null

/**
 * 获取 Git 服务实例（单例）
 */
export function useGitService(): GitService {
  if (!gitService) {
    gitService = new GitService()
  }
  return gitService
}
