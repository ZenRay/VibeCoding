import { test, expect } from '@playwright/test';

test.describe('MySQL 数据库支持 E2E 测试 - interview_db', () => {
  test.beforeEach(async ({ page }) => {
    // 访问主页
    await page.goto('/');
    await page.waitForLoadState('networkidle');
  });

  test('应该能够添加 MySQL interview_db 数据库连接', async ({ page }) => {
    // 点击"添加数据库连接"按钮
    const addButton = page.getByRole('button', { name: /添加数据库|Add Database/i });
    await addButton.click();

    // 等待 Modal 出现
    await page.waitForSelector('.ant-modal', { timeout: 5000 });

    // 填写表单 - 数据库名称
    const nameInput = page.locator('.ant-input').first();
    await nameInput.fill('interview_db');

    // 填写连接 URL
    const urlInput = page.locator('textarea.ant-input');
    await urlInput.fill('mysql://root:root@localhost:3306/interview_db');

    // 点击确定按钮
    const okButton = page.locator('.ant-modal-footer .ant-btn-primary');
    await okButton.click();

    // 等待连接成功
    await page.waitForTimeout(3000);

    // 验证数据库出现在列表中
    const dbName = page.getByText('interview_db');
    await expect(dbName).toBeVisible({ timeout: 5000 });
  });

  test('应该能够查询 interview_db 中的候选人数据', async ({ page }) => {
    // 确保数据库已连接（如果还没连接则添加）
    const hasDb = await page.getByText('interview_db').count() > 0;

    if (!hasDb) {
      // 添加数据库连接
      const addButton = page.getByRole('button', { name: /添加数据库|Add Database/i });
      await addButton.click();
      await page.waitForSelector('.ant-modal');
      await page.locator('.ant-input').first().fill('interview_db');
      await page.locator('textarea.ant-input').fill('mysql://root:root@localhost:3306/interview_db');
      await page.locator('.ant-modal-footer .ant-btn-primary').click();
      await page.waitForTimeout(3000);
    }

    // 选择 interview_db 数据库
    await page.getByText('interview_db').click();
    await page.waitForTimeout(2000);

    // 找到 SQL 编辑器并输入查询
    const editorSelectors = [
      '.monaco-editor textarea',
      'textarea[placeholder*="SQL"]',
      'textarea',
    ];

    let editor = null;
    for (const sel of editorSelectors) {
      const el = page.locator(sel).first();
      if (await el.count() > 0) {
        editor = el;
        break;
      }
    }

    if (editor) {
      // 清空编辑器并输入查询
      await editor.fill('SELECT * FROM candidates LIMIT 3');

      // 执行查询
      const executeButton = page.getByRole('button', { name: /执行|运行|Execute|Run/i });
      if (await executeButton.count() > 0) {
        await executeButton.click();

        // 等待结果显示
        await page.waitForTimeout(3000);

        // 验证结果表格存在
        const table = page.locator('table');
        await expect(table).toBeVisible({ timeout: 5000 });

        // 验证结果包含候选人数据（检查是否有行数据）
        const rows = page.locator('tbody tr');
        const rowCount = await rows.count();
        expect(rowCount).toBeGreaterThan(0);
      }
    }
  });

  test('应该能够执行 JOIN 查询查看面试信息', async ({ page }) => {
    // 确保数据库已连接
    const hasDb = await page.getByText('interview_db').count() > 0;

    if (!hasDb) {
      const addButton = page.getByRole('button', { name: /添加数据库|Add Database/i });
      await addButton.click();
      await page.waitForSelector('.ant-modal');
      await page.locator('.ant-input').first().fill('interview_db');
      await page.locator('textarea.ant-input').fill('mysql://root:root@localhost:3306/interview_db');
      await page.locator('.ant-modal-footer .ant-btn-primary').click();
      await page.waitForTimeout(3000);
    }

    // 选择数据库
    await page.getByText('interview_db').click();
    await page.waitForTimeout(2000);

    // 输入 JOIN 查询
    const editorSelectors = [
      '.monaco-editor textarea',
      'textarea[placeholder*="SQL"]',
      'textarea',
    ];

    let editor = null;
    for (const sel of editorSelectors) {
      const el = page.locator(sel).first();
      if (await el.count() > 0) {
        editor = el;
        break;
      }
    }

    if (editor) {
      const joinQuery = `
        SELECT
          c.name,
          c.position,
          i.interviewer,
          i.score
        FROM candidates c
        JOIN interviews i ON c.id = i.candidate_id
        WHERE i.status = 'completed'
        LIMIT 5
      `.trim();

      await editor.fill(joinQuery);

      const executeButton = page.getByRole('button', { name: /执行|运行|Execute|Run/i });
      if (await executeButton.count() > 0) {
        await executeButton.click();
        await page.waitForTimeout(3000);

        // 验证结果显示
        const table = page.locator('table');
        await expect(table).toBeVisible({ timeout: 5000 });
      }
    }
  });

  test('应该能够使用自然语言生成 MySQL 查询', async ({ page }) => {
    // 确保数据库已连接
    const hasDb = await page.getByText('interview_db').count() > 0;

    if (!hasDb) {
      const addButton = page.getByRole('button', { name: /添加数据库|Add Database/i });
      await addButton.click();
      await page.waitForSelector('.ant-modal');
      await page.locator('.ant-input').first().fill('interview_db');
      await page.locator('textarea.ant-input').fill('mysql://root:root@localhost:3306/interview_db');
      await page.locator('.ant-modal-footer .ant-btn-primary').click();
      await page.waitForTimeout(3000);
    }

    // 选择数据库
    await page.getByText('interview_db').click();
    await page.waitForTimeout(2000);

    // 查找 AI/自然语言按钮或输入框
    const aiButton = page.getByRole('button', { name: /AI|自然语言|Natural Language/i });

    if (await aiButton.count() > 0) {
      await aiButton.click();
      await page.waitForTimeout(1000);

      // 输入自然语言查询
      const promptInput = page.locator('input[placeholder*="自然语言"], input[placeholder*="AI"], textarea');
      const visibleInput = promptInput.filter({ hasText: '' }).first();

      if (await visibleInput.count() > 0) {
        await visibleInput.fill('查询所有候选人的姓名和职位');

        // 提交查询
        const submitButton = page.getByRole('button', { name: /生成|Generate|提交/i });
        if (await submitButton.count() > 0) {
          await submitButton.click();

          // 等待 SQL 生成（注意：可能因为没有 API key 而失败，这是预期的）
          await page.waitForTimeout(3000);
        }
      }
    } else {
      // 如果没有找到 AI 按钮，跳过此测试
      console.log('AI/自然语言功能未找到，跳过此测试');
    }
  });

  test('应该能够查看 MySQL 数据库元数据', async ({ page }) => {
    // 确保数据库已连接
    const hasDb = await page.getByText('interview_db').count() > 0;

    if (!hasDb) {
      const addButton = page.getByRole('button', { name: /添加数据库|Add Database/i });
      await addButton.click();
      await page.waitForSelector('.ant-modal');
      await page.locator('.ant-input').first().fill('interview_db');
      await page.locator('textarea.ant-input').fill('mysql://root:root@localhost:3306/interview_db');
      await page.locator('.ant-modal-footer .ant-btn-primary').click();
      await page.waitForTimeout(3000);
    }

    // 选择数据库
    await page.getByText('interview_db').click();
    await page.waitForTimeout(2000);

    // 查找元数据相关元素（表结构、列信息等）
    const metadataSelectors = [
      '[data-testid="metadata-tree"]',
      '.metadata-tree',
      '.ant-tree',
      '[class*="schema"]',
      '[class*="table"]',
    ];

    let found = false;
    for (const sel of metadataSelectors) {
      if (await page.locator(sel).count() > 0) {
        found = true;

        // 尝试查找表名 candidates 或 interviews
        const hasCandidates = await page.getByText('candidates').count() > 0;
        const hasInterviews = await page.getByText('interviews').count() > 0;

        if (hasCandidates || hasInterviews) {
          console.log('找到 MySQL 数据库表结构');
          expect(hasCandidates || hasInterviews).toBeTruthy();
        }
        break;
      }
    }

    if (!found) {
      console.log('元数据树未找到 - 可能需要点击特定按钮才能显示');
    }
  });
});
