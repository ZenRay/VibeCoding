import { test, expect } from '@playwright/test'

/**
 * Ticket CRUD E2E 测试
 * 测试 Ticket 的创建、编辑、删除、恢复等核心功能
 */

test.describe('Ticket CRUD 操作', () => {
  test.beforeEach(async ({ page }) => {
    // 访问首页
    await page.goto('/')
    // 等待页面加载完成
    await page.waitForLoadState('networkidle')
  })

  test('应该显示首页标题和基本布局', async ({ page }) => {
    // 验证标题 - 使用 h1 标签
    await expect(page.locator('h1').filter({ hasText: 'Project Alpha' })).toBeVisible()

    // 验证侧边栏存在 - 状态和标签部分
    await expect(page.getByText('状态').first()).toBeVisible()
    await expect(page.getByText('标签').first()).toBeVisible()

    // 验证新建按钮存在（顶部栏的按钮）
    await expect(page.locator('header button, .border-b button').filter({ hasText: '新建 Ticket' }).first()).toBeVisible()
  })

  test('应该能够创建新 Ticket', async ({ page }) => {
    // 点击新建按钮（顶部栏）
    await page.locator('button').filter({ hasText: '新建 Ticket' }).first().click()

    // 等待对话框出现
    await expect(page.getByRole('heading', { name: '创建 Ticket' })).toBeVisible()

    // 填写表单
    const testTitle = `测试 Ticket ${Date.now()}`
    await page.locator('#title').fill(testTitle)
    await page.locator('#description').fill('这是一个测试描述')

    // 提交表单 - 点击创建按钮
    await page.getByRole('button', { name: '创建', exact: true }).click()

    // 等待对话框关闭和列表刷新
    await page.waitForTimeout(1000)

    // 验证 Ticket 出现在列表中
    await expect(page.getByText(testTitle)).toBeVisible()
  })

  test('应该能够编辑 Ticket', async ({ page }) => {
    // 先创建一个 Ticket
    await page.locator('button').filter({ hasText: '新建 Ticket' }).first().click()
    const originalTitle = `原始标题 ${Date.now()}`
    await page.locator('#title').fill(originalTitle)
    await page.getByRole('button', { name: '创建', exact: true }).click()
    await page.waitForTimeout(1000)

    // 找到刚创建的 Ticket，点击编辑按钮 (Edit2 图标，title="编辑")
    const ticketRow = page.locator('.flex.items-start.gap-4').filter({ hasText: originalTitle })
    await ticketRow.locator('button[title="编辑"]').click()

    // 等待编辑对话框
    await expect(page.getByRole('heading', { name: '编辑 Ticket' })).toBeVisible()

    // 修改标题
    const newTitle = `修改后标题 ${Date.now()}`
    await page.locator('#title').fill(newTitle)

    // 保存
    await page.getByRole('button', { name: '更新' }).click()

    // 等待更新完成
    await page.waitForTimeout(1000)

    // 验证更新成功
    await expect(page.getByText(newTitle)).toBeVisible()
  })

  test('应该能够删除 Ticket（软删除）', async ({ page }) => {
    // 先创建一个 Ticket
    await page.locator('button').filter({ hasText: '新建 Ticket' }).first().click()
    const testTitle = `待删除 ${Date.now()}`
    await page.locator('#title').fill(testTitle)
    await page.getByRole('button', { name: '创建', exact: true }).click()
    await page.waitForTimeout(1000)

    // 处理 confirm 对话框
    page.on('dialog', dialog => dialog.accept())

    // 找到 Ticket，点击删除按钮 (Trash2 图标，title="删除")
    const ticketRow = page.locator('.flex.items-start.gap-4').filter({ hasText: testTitle })
    await ticketRow.locator('button[title="删除"]').click()

    // 等待删除完成
    await page.waitForTimeout(1000)

    // 默认不显示已删除的，验证 Ticket 消失
    await expect(page.getByText(testTitle)).not.toBeVisible()
  })

  test('应该能够切换 Ticket 完成状态', async ({ page }) => {
    // 先创建一个 Ticket
    await page.locator('button').filter({ hasText: '新建 Ticket' }).first().click()
    const testTitle = `状态切换测试 ${Date.now()}`
    await page.locator('#title').fill(testTitle)
    await page.getByRole('button', { name: '创建', exact: true }).click()
    await page.waitForTimeout(1000)

    // 找到 Ticket
    const ticketRow = page.locator('.flex.items-start.gap-4').filter({ hasText: testTitle })

    // 验证初始状态是"未完成"
    await expect(ticketRow.getByText('未完成')).toBeVisible()

    // 点击状态图标（Circle）切换状态
    await ticketRow.locator('button').first().click()

    // 等待状态更新
    await page.waitForTimeout(1000)

    // 验证状态变为"已完成"
    await expect(ticketRow.getByText('已完成')).toBeVisible()
  })

  test('应该能够恢复已删除的 Ticket', async ({ page }) => {
    // 先创建并删除一个 Ticket
    await page.locator('button').filter({ hasText: '新建 Ticket' }).first().click()
    const testTitle = `待恢复 ${Date.now()}`
    await page.locator('#title').fill(testTitle)
    await page.getByRole('button', { name: '创建', exact: true }).click()
    await page.waitForTimeout(1000)

    // 处理 confirm 对话框
    page.on('dialog', dialog => dialog.accept())

    // 删除
    const ticketRow = page.locator('.flex.items-start.gap-4').filter({ hasText: testTitle })
    await ticketRow.locator('button[title="删除"]').click()
    await page.waitForTimeout(1000)

    // 勾选"显示已删除的 Ticket"
    await page.locator('#include-deleted').check()
    await page.waitForTimeout(1000)

    // 验证已删除的 Ticket 显示出来
    await expect(page.getByText(testTitle)).toBeVisible()

    // 找到恢复按钮 (RotateCcw 图标，title="恢复") 并点击
    const deletedRow = page.locator('.flex.items-start.gap-4').filter({ hasText: testTitle })
    await deletedRow.locator('button[title="恢复"]').click()

    // 等待恢复完成
    await page.waitForTimeout(1000)

    // 取消勾选"显示已删除"
    await page.locator('#include-deleted').uncheck()
    await page.waitForTimeout(500)

    // 恢复后应该能在正常列表中看到
    await expect(page.getByText(testTitle)).toBeVisible()
  })

  test('应该能够批量删除 Ticket', async ({ page }) => {
    // 创建两个 Ticket
    const timestamp = Date.now()
    for (let i = 1; i <= 2; i++) {
      await page.locator('button').filter({ hasText: '新建 Ticket' }).first().click()
      await page.locator('#title').fill(`批量删除测试 ${i} - ${timestamp}`)
      await page.getByRole('button', { name: '创建', exact: true }).click()
      await page.waitForTimeout(800)
    }

    // 处理 confirm 对话框
    page.on('dialog', dialog => dialog.accept())

    // 选择两个 Ticket（通过复选框）
    const checkboxes = page.locator('.flex.items-start.gap-4 input[type="checkbox"]')
    await checkboxes.first().check()
    await checkboxes.nth(1).check()

    // 应该显示"已选择 2 项"
    await expect(page.getByText('已选择 2 项')).toBeVisible()

    // 点击批量删除按钮（工具栏中的）
    await page.locator('button').filter({ hasText: '批量删除' }).first().click()
    await page.waitForTimeout(1000)

    // 验证删除成功
    await expect(page.getByText(`批量删除测试 1 - ${timestamp}`)).not.toBeVisible()
    await expect(page.getByText(`批量删除测试 2 - ${timestamp}`)).not.toBeVisible()
  })
})
