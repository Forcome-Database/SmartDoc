/**
 * 文件上传 API
 * 支持图片、视频、文档上传到 MinIO
 */
import { z } from 'zod'
import {
  validateFile,
  generateObjectName,
  uploadToMinio,
  type FileType,
} from '../utils/minio'

// 请求参数验证
const querySchema = z.object({
  type: z.enum(['image', 'video', 'document']).optional(),
})

export default defineEventHandler(async (event) => {
  // 验证用户登录
  const session = await getUserSession(event)
  if (!session?.user) {
    throw createError({
      statusCode: 401,
      message: '请先登录',
    })
  }

  // 解析查询参数
  const query = getQuery(event)
  const { type: allowedType } = querySchema.parse(query)
  const allowedTypes: FileType[] | undefined = allowedType ? [allowedType] : undefined

  // 读取上传的文件
  const formData = await readMultipartFormData(event)
  if (!formData || formData.length === 0) {
    throw createError({
      statusCode: 400,
      message: '请选择要上传的文件',
    })
  }

  // 获取文件数据
  const fileField = formData.find((field) => field.name === 'file')
  if (!fileField || !fileField.data || !fileField.filename) {
    throw createError({
      statusCode: 400,
      message: '无效的文件数据',
    })
  }

  const { data: buffer, filename, type: mimeType } = fileField

  // 验证文件类型和大小
  const validation = validateFile(mimeType || 'application/octet-stream', buffer.length, allowedTypes)
  if (!validation.valid) {
    throw createError({
      statusCode: 400,
      message: validation.error,
    })
  }

  const fileType = validation.fileType!

  try {
    // 生成对象名称
    const objectName = generateObjectName(filename, fileType)

    // 上传到 MinIO
    const url = await uploadToMinio(buffer, objectName, mimeType || 'application/octet-stream', {
      'x-amz-meta-original-name': encodeURIComponent(filename),
      'x-amz-meta-uploaded-by': session.user.id as string,
      'x-amz-meta-uploaded-at': new Date().toISOString(),
    })

    return {
      success: true,
      data: {
        url,
        objectName,
        filename,
        mimeType: mimeType || 'application/octet-stream',
        size: buffer.length,
        fileType,
      },
    }
  } catch (error) {
    console.error('Upload error:', error)
    throw createError({
      statusCode: 500,
      message: '文件上传失败，请稍后重试',
    })
  }
})
