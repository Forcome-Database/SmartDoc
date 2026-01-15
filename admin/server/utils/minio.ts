/**
 * MinIO 客户端工具
 * 用于文件上传到对象存储
 */
import { Client } from 'minio'

// MinIO 客户端实例（单例）
let minioClient: Client | null = null

/**
 * 文件类型配置
 */
export const FILE_TYPE_CONFIG = {
  image: {
    mimeTypes: ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/svg+xml'],
    maxSize: 10 * 1024 * 1024, // 10MB
    extensions: ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg'],
  },
  video: {
    mimeTypes: ['video/mp4', 'video/webm', 'video/ogg', 'video/quicktime'],
    maxSize: 100 * 1024 * 1024, // 100MB
    extensions: ['.mp4', '.webm', '.ogg', '.mov'],
  },
  document: {
    mimeTypes: [
      'application/pdf',
      'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'application/vnd.ms-excel',
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      'application/vnd.ms-powerpoint',
      'application/vnd.openxmlformats-officedocument.presentationml.presentation',
      'text/plain',
      'text/markdown',
    ],
    maxSize: 50 * 1024 * 1024, // 50MB
    extensions: ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.md'],
  },
} as const

export type FileType = keyof typeof FILE_TYPE_CONFIG

/**
 * 获取 MinIO 客户端实例
 */
export function useMinioClient(): Client {
  if (minioClient) return minioClient

  const config = useRuntimeConfig()

  // 验证必要的环境变量
  if (!config.minioEndpoint) {
    throw new Error('MINIO_ENDPOINT is not configured')
  }
  if (!config.minioAccessKey) {
    throw new Error('MINIO_ACCESS_KEY is not configured')
  }
  if (!config.minioSecretKey) {
    throw new Error('MINIO_SECRET_KEY is not configured')
  }

  // 创建 MinIO 客户端
  minioClient = new Client({
    endPoint: config.minioEndpoint,
    port: config.minioPort ? parseInt(config.minioPort) : 9000,
    useSSL: config.minioUseSSL === 'true',
    accessKey: config.minioAccessKey,
    secretKey: config.minioSecretKey,
  })

  return minioClient
}

/**
 * 获取 Bucket 名称
 */
export function getMinioBucket(): string {
  const config = useRuntimeConfig()
  return config.minioBucket || 'forcome-docs'
}

/**
 * 获取文件公开访问 URL
 */
export function getFileUrl(objectName: string): string {
  const config = useRuntimeConfig()
  const protocol = config.minioUseSSL === 'true' ? 'https' : 'http'
  const port = config.minioPort ? `:${config.minioPort}` : ''
  const bucket = getMinioBucket()
  
  // 如果配置了公开访问 URL，使用它
  if (config.minioPublicUrl) {
    return `${config.minioPublicUrl}/${bucket}/${objectName}`
  }
  
  return `${protocol}://${config.minioEndpoint}${port}/${bucket}/${objectName}`
}

/**
 * 确保 Bucket 存在
 */
export async function ensureBucketExists(): Promise<void> {
  const client = useMinioClient()
  const bucket = getMinioBucket()

  const exists = await client.bucketExists(bucket)
  if (!exists) {
    await client.makeBucket(bucket)
    console.log(`Created bucket: ${bucket}`)
    
    // 设置 Bucket 策略为公开读取
    const policy = {
      Version: '2012-10-17',
      Statement: [
        {
          Effect: 'Allow',
          Principal: { AWS: ['*'] },
          Action: ['s3:GetObject'],
          Resource: [`arn:aws:s3:::${bucket}/*`],
        },
      ],
    }
    await client.setBucketPolicy(bucket, JSON.stringify(policy))
    console.log(`Set public read policy for bucket: ${bucket}`)
  }
}

/**
 * 根据 MIME 类型获取文件类型
 */
export function getFileTypeByMime(mimeType: string): FileType | null {
  for (const [type, config] of Object.entries(FILE_TYPE_CONFIG)) {
    if (config.mimeTypes.includes(mimeType)) {
      return type as FileType
    }
  }
  return null
}

/**
 * 验证文件类型和大小
 */
export function validateFile(
  mimeType: string,
  size: number,
  allowedTypes?: FileType[]
): { valid: boolean; error?: string; fileType?: FileType } {
  const fileType = getFileTypeByMime(mimeType)

  if (!fileType) {
    return { valid: false, error: `不支持的文件类型: ${mimeType}` }
  }

  if (allowedTypes && !allowedTypes.includes(fileType)) {
    return { valid: false, error: `不允许上传 ${fileType} 类型的文件` }
  }

  const config = FILE_TYPE_CONFIG[fileType]
  if (size > config.maxSize) {
    const maxSizeMB = config.maxSize / (1024 * 1024)
    return { valid: false, error: `文件大小超过限制 (最大 ${maxSizeMB}MB)` }
  }

  return { valid: true, fileType }
}

/**
 * 生成唯一的对象名称
 * 格式: {fileType}/{year}/{month}/{timestamp}-{random}{ext}
 * 示例: image/2025/01/1736123456789-abc123.jpg
 */
export function generateObjectName(originalName: string, fileType: FileType): string {
  const now = new Date()
  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const timestamp = Date.now()
  const random = Math.random().toString(36).substring(2, 8)
  const ext = originalName.substring(originalName.lastIndexOf('.'))
  
  return `${fileType}/${year}/${month}/${timestamp}-${random}${ext}`
}

/**
 * 上传文件到 MinIO
 */
export async function uploadToMinio(
  buffer: Buffer,
  objectName: string,
  mimeType: string,
  metadata?: Record<string, string>
): Promise<string> {
  const client = useMinioClient()
  const bucket = getMinioBucket()

  // 确保 Bucket 存在
  await ensureBucketExists()

  // 上传文件
  await client.putObject(bucket, objectName, buffer, buffer.length, {
    'Content-Type': mimeType,
    ...metadata,
  })

  // 返回访问 URL
  return getFileUrl(objectName)
}

/**
 * 删除 MinIO 中的文件
 */
export async function deleteFromMinio(objectName: string): Promise<void> {
  const client = useMinioClient()
  const bucket = getMinioBucket()

  await client.removeObject(bucket, objectName)
}

/**
 * 获取别名（兼容旧代码）
 */
export const getMinioClient = useMinioClient
