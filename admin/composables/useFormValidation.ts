/**
 * 表单验证 Composable
 * 基于 Zod 提供表单验证功能
 * 
 * @requirements 11.4
 */
import { z, type ZodSchema, type ZodError } from 'zod'

export interface FormError {
  /** 字段名称 */
  name: string
  /** 错误消息 */
  message: string
}

export interface FormValidationReturn<T> {
  /** 表单状态 */
  state: T
  /** 错误列表 */
  errors: Ref<FormError[]>
  /** 是否有错误 */
  hasErrors: ComputedRef<boolean>
  /** 获取字段错误 */
  getFieldError: (name: string) => string | undefined
  /** 验证整个表单 */
  validate: () => Promise<boolean>
  /** 验证单个字段 */
  validateField: (name: string) => Promise<boolean>
  /** 清除所有错误 */
  clearErrors: () => void
  /** 清除单个字段错误 */
  clearFieldError: (name: string) => void
  /** 设置字段错误 */
  setFieldError: (name: string, message: string) => void
  /** 重置表单 */
  reset: (newState?: Partial<T>) => void
}

/**
 * 表单验证 Composable
 * 
 * @param schema Zod schema
 * @param initialState 初始状态
 */
export function useFormValidation<T extends Record<string, any>>(
  schema: ZodSchema<T>,
  initialState: T
): FormValidationReturn<T> {
  // 表单状态
  const state = reactive({ ...initialState }) as T
  
  // 错误列表
  const errors = ref<FormError[]>([])

  // 是否有错误
  const hasErrors = computed(() => errors.value.length > 0)

  /**
   * 获取字段错误
   */
  const getFieldError = (name: string): string | undefined => {
    return errors.value.find(e => e.name === name)?.message
  }

  /**
   * 解析 Zod 错误
   */
  const parseZodError = (error: ZodError): FormError[] => {
    return error.errors.map(err => ({
      name: err.path.join('.'),
      message: err.message,
    }))
  }

  /**
   * 验证整个表单
   */
  const validate = async (): Promise<boolean> => {
    try {
      await schema.parseAsync(state)
      errors.value = []
      return true
    } catch (e) {
      if (e instanceof z.ZodError) {
        errors.value = parseZodError(e)
      }
      return false
    }
  }

  /**
   * 验证单个字段
   */
  const validateField = async (name: string): Promise<boolean> => {
    try {
      // 获取字段的 schema
      const fieldSchema = (schema as any).shape?.[name]
      if (fieldSchema) {
        await fieldSchema.parseAsync((state as any)[name])
        // 清除该字段的错误
        errors.value = errors.value.filter(e => e.name !== name)
        return true
      }
      return true
    } catch (e) {
      if (e instanceof z.ZodError) {
        // 更新该字段的错误
        const fieldErrors = parseZodError(e).map(err => ({
          ...err,
          name, // 确保使用正确的字段名
        }))
        errors.value = [
          ...errors.value.filter(e => e.name !== name),
          ...fieldErrors,
        ]
      }
      return false
    }
  }

  /**
   * 清除所有错误
   */
  const clearErrors = () => {
    errors.value = []
  }

  /**
   * 清除单个字段错误
   */
  const clearFieldError = (name: string) => {
    errors.value = errors.value.filter(e => e.name !== name)
  }

  /**
   * 设置字段错误
   */
  const setFieldError = (name: string, message: string) => {
    const existingIndex = errors.value.findIndex(e => e.name === name)
    if (existingIndex >= 0) {
      errors.value[existingIndex].message = message
    } else {
      errors.value.push({ name, message })
    }
  }

  /**
   * 重置表单
   */
  const reset = (newState?: Partial<T>) => {
    Object.assign(state, { ...initialState, ...newState })
    errors.value = []
  }

  return {
    state,
    errors,
    hasErrors,
    getFieldError,
    validate,
    validateField,
    clearErrors,
    clearFieldError,
    setFieldError,
    reset,
  }
}

// ============ 常用验证 Schema ============

/**
 * 常用的 Zod 验证规则
 */
export const zodRules = {
  /** 必填字符串 */
  required: (message = '此字段为必填项') => 
    z.string().min(1, message),

  /** 邮箱 */
  email: (message = '请输入有效的邮箱地址') => 
    z.string().email(message),

  /** 手机号（中国大陆） */
  mobile: (message = '请输入有效的手机号') => 
    z.string().regex(/^1[3-9]\d{9}$/, message),

  /** URL */
  url: (message = '请输入有效的 URL') => 
    z.string().url(message),

  /** 最小长度 */
  minLength: (min: number, message?: string) => 
    z.string().min(min, message || `最少需要 ${min} 个字符`),

  /** 最大长度 */
  maxLength: (max: number, message?: string) => 
    z.string().max(max, message || `最多允许 ${max} 个字符`),

  /** 长度范围 */
  lengthRange: (min: number, max: number, message?: string) => 
    z.string()
      .min(min, message || `最少需要 ${min} 个字符`)
      .max(max, message || `最多允许 ${max} 个字符`),

  /** 正整数 */
  positiveInt: (message = '请输入正整数') => 
    z.number().int().positive(message),

  /** 非负整数 */
  nonNegativeInt: (message = '请输入非负整数') => 
    z.number().int().nonnegative(message),

  /** 数字范围 */
  numberRange: (min: number, max: number, message?: string) => 
    z.number()
      .min(min, message || `最小值为 ${min}`)
      .max(max, message || `最大值为 ${max}`),

  /** Slug（URL 友好的字符串） */
  slug: (message = '只能包含小写字母、数字和连字符') => 
    z.string().regex(/^[a-z0-9]+(?:-[a-z0-9]+)*$/, message),

  /** 可选字符串（空字符串转为 undefined） */
  optionalString: () => 
    z.string().optional().transform(val => val === '' ? undefined : val),

  /** 可选 URL */
  optionalUrl: (message = '请输入有效的 URL') => 
    z.string().url(message).optional().or(z.literal('')),
}

// ============ 常用表单 Schema ============

/**
 * 语言表单 Schema
 */
export const localeFormSchema = z.object({
  code: zodRules.required('语言代码为必填项')
    .regex(/^[a-z]{2}(-[A-Z]{2})?$/, '语言代码格式不正确（如：zh、en、vi）'),
  name: zodRules.required('语言名称为必填项'),
  nativeName: zodRules.required('本地名称为必填项'),
  isDefault: z.boolean().default(false),
  isEnabled: z.boolean().default(true),
})

export type LocaleFormData = z.infer<typeof localeFormSchema>

/**
 * 栏目表单 Schema
 */
export const categoryFormSchema = z.object({
  slug: zodRules.slug('Slug 只能包含小写字母、数字和连字符'),
  parentId: z.string().nullable().optional(),
  titles: z.record(z.string(), z.string()).refine(
    (titles) => Object.values(titles).some(t => t.trim().length > 0),
    { message: '至少需要填写一种语言的标题' }
  ),
})

export type CategoryFormData = z.infer<typeof categoryFormSchema>

/**
 * 文档表单 Schema
 */
export const documentFormSchema = z.object({
  title: zodRules.required('文档标题为必填项'),
  slug: zodRules.slug('Slug 只能包含小写字母、数字和连字符'),
  categoryId: z.string().nullable().optional(),
  localeId: zodRules.required('请选择语言'),
  content: z.string().default(''),
})

export type DocumentFormData = z.infer<typeof documentFormSchema>

/**
 * 导航菜单表单 Schema
 */
export const navMenuFormSchema = z.object({
  type: z.enum(['link', 'dropdown', 'divider']),
  targetType: z.enum(['category', 'document', 'external', 'none']),
  targetId: z.string().nullable().optional(),
  externalUrl: z.string().url('请输入有效的 URL').optional().or(z.literal('')),
  openInNewTab: z.boolean().default(false),
  icon: z.string().optional(),
  isVisible: z.boolean().default(true),
  titles: z.record(z.string(), z.string()),
}).refine(
  (data) => {
    // 如果是外部链接类型，必须填写 URL
    if (data.targetType === 'external') {
      return !!data.externalUrl && data.externalUrl.length > 0
    }
    return true
  },
  { message: '外部链接类型必须填写 URL', path: ['externalUrl'] }
).refine(
  (data) => {
    // 如果是栏目或文档类型，必须选择目标
    if (data.targetType === 'category' || data.targetType === 'document') {
      return !!data.targetId
    }
    return true
  },
  { message: '请选择目标', path: ['targetId'] }
)

export type NavMenuFormData = z.infer<typeof navMenuFormSchema>

/**
 * 用户角色表单 Schema
 */
export const userRoleFormSchema = z.object({
  role: z.enum(['admin', 'editor', 'viewer'], {
    errorMap: () => ({ message: '请选择有效的角色' }),
  }),
})

export type UserRoleFormData = z.infer<typeof userRoleFormSchema>
