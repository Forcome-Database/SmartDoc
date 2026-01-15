/**
 * AI 翻译 API
 * POST /api/translate
 * 
 * Requirements: 6.2, 6.3, 6.6, 6.7
 * 使用 AI SDK 实现流式翻译，保持 Markdown 格式
 */
import { streamText } from 'ai'
import { createOpenAI } from '@ai-sdk/openai'

// 语言名称映射
const languageNames: Record<string, string> = {
  zh: '中文',
  en: 'English',
  vi: 'Tiếng Việt',
}

// 翻译系统提示词
const getSystemPrompt = (sourceLanguage: string, targetLanguage: string) => `You are a professional translator specializing in technical documentation.

Your task is to translate the following content from ${sourceLanguage} to ${targetLanguage}.

IMPORTANT RULES:
1. Preserve ALL Markdown formatting exactly as-is (headings, lists, code blocks, links, images, tables, etc.)
2. DO NOT translate content inside code blocks (\`\`\` or \`inline code\`)
3. DO NOT translate URLs, file paths, or technical identifiers
4. DO NOT translate HTML tags or their attributes
5. DO NOT translate component names like <Quiz>, <Mermaid>, <Callout>, etc.
6. Preserve the original structure and line breaks
7. Translate naturally and fluently, not word-by-word
8. Keep technical terms accurate and consistent
9. If a term has a well-known translation in the target language, use it
10. For terms without standard translations, keep the original with a translation in parentheses on first occurrence

Output ONLY the translated content, without any explanations or notes.`

export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig()
  
  // 验证 API Key
  if (!config.openaiApiKey) {
    throw createError({
      statusCode: 500,
      statusMessage: 'Internal Server Error',
      message: 'OpenAI API Key 未配置',
    })
  }

  // 获取可选的 baseURL
  const baseURL = config.openaiBaseUrl || undefined

  // 读取请求体
  const body = await readBody(event)
  const { content, sourceLocale, targetLocale } = body

  // 验证参数
  if (!content || typeof content !== 'string') {
    throw createError({
      statusCode: 400,
      statusMessage: 'Bad Request',
      message: '缺少翻译内容',
    })
  }

  if (!sourceLocale || !targetLocale) {
    throw createError({
      statusCode: 400,
      statusMessage: 'Bad Request',
      message: '缺少源语言或目标语言',
    })
  }

  if (sourceLocale === targetLocale) {
    throw createError({
      statusCode: 400,
      statusMessage: 'Bad Request',
      message: '源语言和目标语言不能相同',
    })
  }

  // 获取语言名称
  const sourceLang = languageNames[sourceLocale] || sourceLocale
  const targetLang = languageNames[targetLocale] || targetLocale

  try {
    // 创建 OpenAI 客户端
    const openai = createOpenAI({
      apiKey: config.openaiApiKey,
      baseURL,
    })

    // 流式翻译
    const result = streamText({
      model: openai('gpt-4o'),
      system: getSystemPrompt(sourceLang, targetLang),
      prompt: content,
      maxTokens: 8192,
      temperature: 0.3, // 较低温度以保持翻译一致性
    })

    // 返回流式响应
    return result.toDataStreamResponse()
  } catch (error: any) {
    console.error('Translation error:', error)
    throw createError({
      statusCode: 500,
      statusMessage: 'Internal Server Error',
      message: error.message || '翻译失败',
    })
  }
})
