/**
 * 标题翻译 API（非流式）
 * POST /api/translate-title
 * 
 * 用于翻译短文本如标题，返回纯文本结果
 */
import { generateText } from 'ai'
import { createOpenAI } from '@ai-sdk/openai'

// 语言名称映射
const languageNames: Record<string, string> = {
  zh: '中文',
  en: 'English',
  vi: 'Tiếng Việt',
}

export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig()
  
  if (!config.openaiApiKey) {
    throw createError({
      statusCode: 500,
      message: 'OpenAI API Key 未配置',
    })
  }

  const body = await readBody(event)
  const { text, sourceLocale, targetLocale } = body

  if (!text || !sourceLocale || !targetLocale) {
    throw createError({
      statusCode: 400,
      message: '缺少必要参数',
    })
  }

  const sourceLang = languageNames[sourceLocale] || sourceLocale
  const targetLang = languageNames[targetLocale] || targetLocale

  try {
    const openai = createOpenAI({
      apiKey: config.openaiApiKey,
      baseURL: config.openaiBaseUrl || undefined,
    })

    const { text: translatedText } = await generateText({
      model: openai('gpt-4o'),
      system: `You are a translator. Translate the following text from ${sourceLang} to ${targetLang}. Output ONLY the translated text, nothing else.`,
      prompt: text,
      maxTokens: 200,
      temperature: 0.3,
    })

    return { translatedText: translatedText.trim() }
  } catch (error: any) {
    console.error('Title translation error:', error)
    throw createError({
      statusCode: 500,
      message: error.message || '翻译失败',
    })
  }
})
