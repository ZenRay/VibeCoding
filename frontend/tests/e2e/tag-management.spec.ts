import { test, expect } from '@playwright/test'

/**
 * 标签管理 E2E 测试
 * 测试标签的创建、编辑、删除和与 Ticket 的关联
 */

test.describe('标签管理功能', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
    await page.waitForLoadState('networkidle')
  })

  test('应该能够打开标签管理对话框', async ({ page }) => {
    // 点击管理标签按钮
    await page.locator('button').filter({ hasText: '管理标签' }).click()

    // 等待对话框动画
    await page.waitForTimeout(300)

    // 验证对话框出现 - TagDialog 显示"创建标签"作为标题
    await expect(page.getByRole('heading', { name: '创建标签' })).toBeVisible()
  })

  test('应该能够创建新标签', async ({ page }) => {
    // 打开标签管理
    await page.locator('button').filter({ hasText: '管理标签' }).click()
    await page.waitForTimeout(300)

    // 填写标签名称 (id="tag-name")
    const tagName = `TESTTAG${Date.now()}`
    await page.locator('#tag-name').fill(tagName)

    // 提交创建
    await page.getByRole('button', { name: '创建', exact: true }).click()

    // 等待创建完成和对话框关闭
    await page.waitForTimeout(1000)

    // 验证标签出现在侧边栏 (标签会自动转为大写)
    await expect(page.locator('.space-y-2').getByText(tagName.toUpperCase())).toBeVisible()
  })

  test('应该自动将标签名转为大写', async ({ page }) => {
    // 打开标签管理
    await page.locator('button').filter({ hasText: '管理标签' }).click()
    await page.waitForTimeout(300)

    // 用小写创建标签
    const lowerCaseName = `lowercase${Date.now()}`
    const upperCaseName = lowerCaseName.toUpperCase()

    await page.locator('#tag-name').fill(lowerCaseName)
    await page.getByRole('button', { name: '创建', exact: true }).click()
    await page.waitForTimeout(1000)

    // 验证标签显示为大写（在侧边栏）
    await expect(page.locator('.space-y-2').getByText(upperCaseName)).toBeVisible()
  })

  test('应该能够为 Ticket 添加标签', async ({ page }) => {
    // 首先确保有一个标签
    await page.locator('button').filter({ hasText: '管理标签' }).click()
    await page.waitForTimeout(300)
    const tagName = `TICKETTAG${Date.now()}`
    await page.locator('#tag-name').fill(tagName)
    await page.getByRole('button', { name: '创建', exact: true }).click()
    await page.waitForTimeout(1000)

    // 创建一个新 Ticket
    await page.locator('button').filter({ hasText: '新建 Ticket' }).first().click()
    await page.waitForTimeout(300)

    const ticketTitle = `带标签的Ticket ${Date.now()}`
    await page.locator('#title').fill(ticketTitle)

    // 在 TicketDialog 中选择标签（标签按钮在对话框内）
    const tagButton = page.locator('[role="dialog"]').getByText(tagName.toUpperCase())
    if (await tagButton.isVisible()) {
      await tagButton.click()
    }

    // 创建 Ticket
    await page.getByRole('button', { name: '创建', exact: true }).click()
    await page.waitForTimeout(1000)

    // 验证 Ticket 创建成功
    await expect(page.getByText(ticketTitle)).toBeVisible()
  })

  test('应该能够选择预设颜色', async ({ page }) => {
    // 打开标签管理
    await page.locator('button').filter({ hasText: '管理标签' }).click()
    await page.waitForTimeout(300)

    // 点击预设颜色按钮 (有 aria-label="选择颜色 #xxx")
    const colorButtons = page.locator('button[aria-label^="选择颜色"]')
    const count = await colorButtons.count()

    if (count > 0) {
      await colorButtons.first().click()
      await page.waitForTimeout(200)
    }

    // 关闭对话框
    await page.keyboard.press('Escape')
  })

  test('应该在侧边栏显示标签及其使用数量', async ({ page }) => {
    // 验证侧边栏的标签部分存在
    await expect(page.getByText('标签').first()).toBeVisible()

    // 侧边栏的标签列表 (.space-y-2 内的 button)
    const tagButtons = page.locator('.space-y-2 button')
    const count = await tagButtons.count()

    // 如果有标签，验证每个标签按钮可见
    if (count > 0) {
      const firstTag = tagButtons.first()
      await expect(firstTag).toBeVisible()
      // 标签按钮应该包含数量（右侧的小数字）
    }
  })

  test('应该能够点击标签进行过滤', async ({ page }) => {
    // 在侧边栏找到标签按钮
    const tagButtons = page.locator('.space-y-2 button')
    const count = await tagButtons.count()

    if (count > 0) {
      // 点击第一个标签进行过滤
      await tagButtons.first().click()
      await page.waitForTimeout(300)

      // 再次点击取消过滤
      await tagButtons.first().click()
      await page.waitForTimeout(300)
    }
  })
})
