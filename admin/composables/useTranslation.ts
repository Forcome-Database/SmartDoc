/**
 * AI 翻译 Composable
 * 使用 @ai-sdk/vue 的 useCompletion 实现流式翻译
 * 
 * Requirements: 6.2, 6.3
 */
import { useCompletion } from '@ai-sdk/vue'
import { ref, computed } from 'vue'

export interface TranslationOptions {
  onFinish?: (result: string) => void
  onError?: (error: Error) => void
}

export interface TranslationState {
  /** 翻译结果 */
  result: Ref<string>
  /** 是否正在翻译 */
  isTranslating: Ref<boolean>
  /** 翻译进度（0-100） */
  progress: Ref<number>
  /** 错误信息 */
  error: Ref<Error | null>
  /** 源语言 */
  sourceLocale: Ref<string>
  /** 目标语言 */
  targetLocale: Ref<string>
}

export function useTranslation(options: TranslationOptions = {}) {
  // 翻译状态
  const sourceLocale = ref('')
  const targetLocale = ref('')
  const sourceContent = ref('')
  const translationError = ref<Error | null>(null)
  const estimatedLength = ref(0)

  // 使用 useCompletion 实现流式翻译
  const {
    completion,
    isLoading,
    error: completionError,
    complete,
    stop,
  } = useCompletion({
    api: '/api/translate',
    streamProtocol: 'data',
    onFinish: (_prompt, result) => {
      options.onFinish?.(result)
    },
    onError: (err) => {
      translationError.value = err
      options.onError?.(err)
    },
  })

  // 计算翻译进度（基于字符数估算）
  const progress = computed(() => {
    if (!isLoading.value || estimatedLength.value === 0) {
      return isLoading.value ? 0 : 100
    }
    // 翻译后的文本长度通常与源文本相近
    const currentLength = completion.value?.length || 0
    const estimated = Math.min(100, Math.round((currentLength / estimatedLength.value) * 100))
    return estimated
  })

  // 合并错误
  const error = computed(() => translationError.value || completionError.value)

  /**
   * 开始翻译
   * @param content 要翻译的内容
   * @param source 源语言代码
   * @param target 目标语言代码
   */
  async function translate(content: string, source: string, target: string) {
    // 重置状态
    translationError.value = null
    sourceLocale.value = source
    targetLocale.value = target
    sourceContent.value = content
    estimatedLength.value = content.length

    try {
      // 发起翻译请求
      await complete(content, {
        body: {
          content,
          sourceLocale: source,
          targetLocale: target,
        },
      })
    } catch (err: any) {
      translationError.value = err
      throw err
    }
  }

  /**
   * 停止翻译
   */
  function stopTranslation() {
    stop()
  }

  /**
   * 重置状态
   */
  function reset() {
    translationError.value = null
    sourceLocale.value = ''
    targetLocale.value = ''
    sourceContent.value = ''
    estimatedLength.value = 0
  }

  return {
    // 状态
    result: completion,
    isTranslating: isLoading,
    progress,
    error,
    sourceLocale: readonly(sourceLocale),
    targetLocale: readonly(targetLocale),
    sourceContent: readonly(sourceContent),
    
    // 方法
    translate,
    stop: stopTranslation,
    reset,
  }
}
