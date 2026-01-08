import { test, expect } from '@playwright/test'

/**
 * 搜索和过滤 E2E 测试
 * 测试搜索、状态过滤、标签过滤等功能
 */

test.describe('搜索和过滤功能', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
    await page.waitForLoadState('networkidle')
  })

  test('应该能够搜索 Ticket', async ({ page }) => {
    // 先创建一个有特定关键词的 Ticket
    await page.locator('button').filter({ hasText: '新建 Ticket' }).first().click()
    const uniqueKeyword = `搜索关键词${Date.now()}`
    await page.locator('#title').fill(uniqueKeyword)
    await page.getByRole('button', { name: '创建', exact: true }).click()
    await page.waitForTimeout(1000)

    // 在搜索框输入关键词 (AdvancedSearch 组件的输入框)
    const searchInput = page.locator('input[placeholder*="搜索"]')
    await searchInput.fill(uniqueKeyword)

    // 等待防抖搜索生效
    await page.waitForTimeout(500)

    // 验证搜索结果 - 在 Ticket 列表中找到匹配的标题
    const ticketList = page.locator('.flex-1.overflow-y-auto')
    await expect(ticketList.getByText(uniqueKeyword)).toBeVisible()
  })

  test('应该能够按状态过滤', async ({ page }) => {
    // 先创建一个 Ticket 并标记为完成
    await page.locator('button').filter({ hasText: '新建 Ticket' }).first().click()
    const completedTitle = `已完成任务 ${Date.now()}`
    await page.locator('#title').fill(completedTitle)
    await page.getByRole('button', { name: '创建', exact: true }).click()
    await page.waitForTimeout(1000)

    // 找到 Ticket，标记为完成
    const ticketRow = page.locator('.flex.items-start.gap-4').filter({ hasText: completedTitle })
    await ticketRow.locator('button').first().click()  // 点击状态图标
    await page.waitForTimeout(1000)

    // 点击"待完成"过滤（在侧边栏 RadioGroup 中，id="status-pending"）
    await page.locator('#status-pending').click()
    await page.waitForTimeout(500)

    // 已完成的 Ticket 应该不可见
    await expect(page.getByText(completedTitle)).not.toBeVisible()

    // 点击"已完成"过滤（id="status-completed"）
    await page.locator('#status-completed').click()
    await page.waitForTimeout(500)

    // 已完成的 Ticket 应该可见
    await expect(page.getByText(completedTitle)).toBeVisible()

    // 点击"全部"恢复（id="status-all"）
    await page.locator('#status-all').click()
  })

  test('应该能够切换显示已删除的 Ticket', async ({ page }) => {
    // 找到"显示已删除的 Ticket"复选框 (id="include-deleted")
    const includeDeletedCheckbox = page.locator('#include-deleted')

    // 勾选
    await includeDeletedCheckbox.check()
    await page.waitForTimeout(300)
    await expect(includeDeletedCheckbox).toBeChecked()

    // 取消勾选
    await includeDeletedCheckbox.uncheck()
    await expect(includeDeletedCheckbox).not.toBeChecked()
  })

  test('应该支持键盘快捷键聚焦搜索框', async ({ page }) => {
    // 先点击页面空白处确保没有元素聚焦
    await page.locator('h1').click()
    await page.waitForTimeout(100)

    // 使用 Ctrl+K 聚焦搜索框
    await page.keyboard.press('Control+k')
    await page.waitForTimeout(300)

    // 验证搜索框获得焦点
    const searchInput = page.locator('input[placeholder*="搜索"]')
    await expect(searchInput).toBeFocused()
  })

  test('应该支持 N 键创建新 Ticket', async ({ page }) => {
    // 先点击页面空白处确保没有输入框聚焦
    await page.locator('h1').click()
    await page.waitForTimeout(100)

    // 按 N 键
    await page.keyboard.press('n')

    // 等待对话框动画
    await page.waitForTimeout(300)

    // 验证创建对话框出现
    await expect(page.getByRole('heading', { name: '创建 Ticket' })).toBeVisible()

    // 关闭对话框
    await page.keyboard.press('Escape')
  })

  test('应该支持 Esc 键关闭对话框', async ({ page }) => {
    // 打开创建对话框
    await page.locator('button').filter({ hasText: '新建 Ticket' }).first().click()
    await expect(page.getByRole('heading', { name: '创建 Ticket' })).toBeVisible()

    // 按 Esc 关闭
    await page.keyboard.press('Escape')

    // 等待动画完成
    await page.waitForTimeout(500)

    // 验证对话框关闭
    await expect(page.getByRole('heading', { name: '创建 Ticket' })).not.toBeVisible()
  })

  test('应该能够排序 Ticket', async ({ page }) => {
    // 找到排序下拉框（工具栏中的第一个 select，用于排序字段选择）
    const sortSelect = page.locator('select').first()

    // 切换到按标题排序
    await sortSelect.selectOption('title')
    await page.waitForTimeout(300)

    // 切换回按创建时间排序
    await sortSelect.selectOption('created_at')
  })
})
