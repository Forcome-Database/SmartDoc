/**
 * 钉钉 OAuth 回调处理
 * 处理钉钉授权回调，获取用户信息并创建会话
 * 
 * Requirements: 12.1, 12.2, 12.3, 12.4, 12.5
 */
import { eq } from 'drizzle-orm'
import { users } from '@shared/schema'

// 钉钉 API 响应类型
interface DingTalkTokenResponse {
  accessToken: string
  refreshToken: string
  expireIn: number
}

interface DingTalkUserInfo {
  nick: string
  avatarUrl: string
  mobile: string
  openId: string
  unionId: string
  email: string
}

// 企业内部应用 access_token 响应
interface CorpAccessTokenResponse {
  errcode: number
  errmsg: string
  access_token: string
  expires_in: number
}

// 根据 unionId 获取 userId 响应
interface GetUserIdByUnionIdResponse {
  errcode: number
  errmsg: string
  result?: {
    contact_type: number
    userid: string
  }
}

// 获取用户详情响应
interface GetUserDetailResponse {
  errcode: number
  errmsg: string
  result?: {
    userid: string
    name: string
    dept_id_list: number[]
    avatar?: string
    mobile?: string
    email?: string
    title?: string
  }
}

// 获取部门详情响应
interface GetDeptDetailResponse {
  errcode: number
  errmsg: string
  result?: {
    dept_id: number
    name: string
    parent_id: number
  }
}

// 缓存企业 access_token（简单内存缓存）
let corpAccessTokenCache: { token: string; expiresAt: number } | null = null

/**
 * 获取企业内部应用的 access_token
 */
async function getCorpAccessToken(appKey: string, appSecret: string): Promise<string> {
  // 检查缓存是否有效（提前5分钟过期）
  if (corpAccessTokenCache && corpAccessTokenCache.expiresAt > Date.now() + 5 * 60 * 1000) {
    return corpAccessTokenCache.token
  }

  const res = await $fetch<CorpAccessTokenResponse>(
    'https://oapi.dingtalk.com/gettoken',
    {
      method: 'GET',
      query: {
        appkey: appKey,
        appsecret: appSecret,
      },
    }
  )

  if (res.errcode !== 0 || !res.access_token) {
    throw new Error(`获取企业 access_token 失败: ${res.errmsg}`)
  }

  // 缓存 token
  corpAccessTokenCache = {
    token: res.access_token,
    expiresAt: Date.now() + res.expires_in * 1000,
  }

  return res.access_token
}

/**
 * 根据 unionId 获取企业内 userId
 */
async function getUserIdByUnionId(accessToken: string, unionId: string): Promise<string | null> {
  try {
    console.log('[钉钉部门] 调用 getbyunionid API, unionId:', unionId)
    const res = await $fetch<GetUserIdByUnionIdResponse>(
      `https://oapi.dingtalk.com/topapi/user/getbyunionid?access_token=${accessToken}`,
      {
        method: 'POST',
        body: { unionid: unionId },
      }
    )
    console.log('[钉钉部门] getbyunionid 响应:', JSON.stringify(res))

    if (res.errcode === 0 && res.result?.userid) {
      return res.result.userid
    }
    console.warn('[钉钉部门] 根据 unionId 获取 userId 失败:', res.errcode, res.errmsg)
    return null
  } catch (error) {
    console.error('[钉钉部门] 获取 userId 异常:', error)
    return null
  }
}

/**
 * 获取用户详情（包含部门信息）
 */
async function getUserDetail(accessToken: string, userId: string): Promise<GetUserDetailResponse['result'] | null> {
  try {
    console.log('[钉钉部门] 调用 user/get API, userId:', userId)
    const res = await $fetch<GetUserDetailResponse>(
      `https://oapi.dingtalk.com/topapi/v2/user/get?access_token=${accessToken}`,
      {
        method: 'POST',
        body: { userid: userId },
      }
    )
    console.log('[钉钉部门] user/get 响应:', JSON.stringify(res))

    if (res.errcode === 0 && res.result) {
      return res.result
    }
    console.warn('[钉钉部门] 获取用户详情失败:', res.errcode, res.errmsg)
    return null
  } catch (error) {
    console.error('[钉钉部门] 获取用户详情异常:', error)
    return null
  }
}

/**
 * 获取部门名称
 */
async function getDeptName(accessToken: string, deptId: number): Promise<string | null> {
  try {
    console.log('[钉钉部门] 调用 department/get API, deptId:', deptId)
    const res = await $fetch<GetDeptDetailResponse>(
      `https://oapi.dingtalk.com/topapi/v2/department/get?access_token=${accessToken}`,
      {
        method: 'POST',
        body: { dept_id: deptId },
      }
    )
    console.log('[钉钉部门] department/get 响应:', JSON.stringify(res))

    if (res.errcode === 0 && res.result?.name) {
      return res.result.name
    }
    console.warn('[钉钉部门] 获取部门详情失败:', res.errcode, res.errmsg)
    return null
  } catch (error) {
    console.error('[钉钉部门] 获取部门详情异常:', error)
    return null
  }
}

/**
 * 获取用户的部门信息
 * 返回第一个部门的名称和ID
 */
async function fetchUserDepartment(
  appKey: string,
  appSecret: string,
  unionId: string
): Promise<{ departmentId: string | null; department: string | null }> {
  try {
    console.log('[钉钉部门] 开始获取部门信息, unionId:', unionId)
    
    // 1. 获取企业 access_token
    const corpToken = await getCorpAccessToken(appKey, appSecret)
    console.log('[钉钉部门] 获取企业 access_token 成功')

    // 2. 根据 unionId 获取 userId
    const userId = await getUserIdByUnionId(corpToken, unionId)
    if (!userId) {
      console.warn('[钉钉部门] 未能获取到 userId')
      return { departmentId: null, department: null }
    }
    console.log('[钉钉部门] 获取 userId 成功:', userId)

    // 3. 获取用户详情（包含部门ID列表）
    const userDetail = await getUserDetail(corpToken, userId)
    if (!userDetail?.dept_id_list?.length) {
      console.warn('[钉钉部门] 用户没有部门信息')
      return { departmentId: null, department: null }
    }
    console.log('[钉钉部门] 用户部门ID列表:', userDetail.dept_id_list)

    // 4. 获取第一个部门的名称
    const firstDeptId = userDetail.dept_id_list[0]
    let deptName = await getDeptName(corpToken, firstDeptId)
    
    // 如果无法获取部门名称（权限不足），使用部门ID作为临时显示
    if (!deptName) {
      console.warn('[钉钉部门] 无法获取部门名称，可能需要申请 qyapi_get_department_list 权限')
      // 尝试从用户详情中获取其他可用信息作为部门显示
      // 暂时使用部门ID
      deptName = `部门${firstDeptId}`
    }
    console.log('[钉钉部门] 部门名称:', deptName)

    return {
      departmentId: String(firstDeptId),
      department: deptName,
    }
  } catch (error) {
    console.error('[钉钉部门] 获取用户部门信息失败:', error)
    return { departmentId: null, department: null }
  }
}

export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig()
  const query = getQuery(event)
  const { code, state } = query

  // 验证授权码
  if (!code || typeof code !== 'string') {
    throw createError({
      statusCode: 400,
      statusMessage: 'Bad Request',
      message: '缺少授权码',
    })
  }

  try {
    // 1. 获取 access_token
    const tokenRes = await $fetch<DingTalkTokenResponse>(
      'https://api.dingtalk.com/v1.0/oauth2/userAccessToken',
      {
        method: 'POST',
        body: {
          clientId: config.dingtalkAppKey,
          clientSecret: config.dingtalkAppSecret,
          code,
          grantType: 'authorization_code',
        },
      }
    )

    if (!tokenRes.accessToken) {
      throw new Error('获取 access_token 失败')
    }

    // 2. 获取用户信息
    const userInfo = await $fetch<DingTalkUserInfo>(
      'https://api.dingtalk.com/v1.0/contact/users/me',
      {
        headers: {
          'x-acs-dingtalk-access-token': tokenRes.accessToken,
        },
      }
    )

    if (!userInfo.openId) {
      throw new Error('获取用户信息失败')
    }

    // 3. 获取用户部门信息（通过企业内部应用 API）
    let departmentInfo = { departmentId: null as string | null, department: null as string | null }
    if (userInfo.unionId) {
      console.log('[钉钉登录] 开始获取部门信息...')
      departmentInfo = await fetchUserDepartment(
        config.dingtalkAppKey,
        config.dingtalkAppSecret,
        userInfo.unionId
      )
      console.log('[钉钉登录] 部门信息结果:', departmentInfo)
    } else {
      console.warn('[钉钉登录] 用户没有 unionId，无法获取部门信息')
    }

    // 4. 查找或创建用户
    const db = useDb()
    let user = await db.query.users.findFirst({
      where: eq(users.dingtalkId, userInfo.openId),
    })

    if (!user) {
      // 新用户 - 创建记录
      const [newUser] = await db.insert(users).values({
        dingtalkId: userInfo.openId,
        unionId: userInfo.unionId || null,
        name: userInfo.nick || '未知用户',
        avatar: userInfo.avatarUrl || null,
        email: userInfo.email || null,
        mobile: userInfo.mobile || null,
        department: departmentInfo.department,
        departmentId: departmentInfo.departmentId,
        role: 'editor', // 默认角色
      }).returning()
      user = newUser
    } else {
      // 已有用户 - 更新信息（每次登录都更新部门信息）
      const [updatedUser] = await db.update(users)
        .set({
          name: userInfo.nick || user.name,
          avatar: userInfo.avatarUrl || user.avatar,
          unionId: userInfo.unionId || user.unionId,
          department: departmentInfo.department || user.department,
          departmentId: departmentInfo.departmentId || user.departmentId,
          updatedAt: new Date(),
        })
        .where(eq(users.id, user.id))
        .returning()
      user = updatedUser
    }

    // 5. 设置 session
    await setUserSession(event, {
      user: {
        id: user.id,
        name: user.name,
        avatar: user.avatar,
        role: user.role,
        dingtalkId: user.dingtalkId,
      },
    })

    // 6. 重定向到首页或指定页面
    const redirectTo = typeof state === 'string' ? state : '/'
    return sendRedirect(event, redirectTo)
  } catch (error: any) {
    console.error('DingTalk OAuth error:', error)

    // 根据错误类型返回不同的错误信息
    const errorMessage = error.message || '登录失败，请重试'
    
    // 重定向到登录页并显示错误
    return sendRedirect(event, `/login?error=${encodeURIComponent(errorMessage)}`)
  }
})
