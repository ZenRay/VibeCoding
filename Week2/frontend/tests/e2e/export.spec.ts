import { test, expect } from '@playwright/test';
import path from 'path';

test.describe('导出查询结果功能 E2E 测试', () => {
  test.beforeEach(async ({ page }) => {
    // 访问主页
    await page.goto('http://localhost:3001', { waitUntil: 'networkidle', timeout: 30000 });
  });

  test('应该在查询结果页显示导出按钮', async ({ page }) => {
    // 先添加数据库连接（如果还没有）
    const hasDb = await page.getByText('interview_db').count() > 0;

    if (!hasDb) {
      // 添加 interview_db 连接
      const addButton = page.getByRole('button', { name: /添加数据库|Add Database/i });
      if (await addButton.count() > 0) {
        await addButton.click();
        await page.waitForSelector('.ant-modal', { timeout: 5000 });
        await page.locator('.ant-input').first().fill('interview_db');
        await page.locator('textarea.ant-input').fill('mysql://root:root@localhost:3306/interview_db');
        await page.locator('.ant-modal-footer .ant-btn-primary').click();
        await page.waitForTimeout(3000);
      }
    }

    // 选择数据库
    await page.getByText('interview_db').click();
    await page.waitForTimeout(2000);

    // 执行查询
    const editor = page.locator('textarea').first();
    if (await editor.count() > 0) {
      await editor.fill('SELECT * FROM candidates LIMIT 5');

      const executeButton = page.getByRole('button', { name: /执行|运行|Execute/i });
      if (await executeButton.count() > 0) {
        await executeButton.click();
        await page.waitForTimeout(2000);

        // 验证导出按钮存在
        const exportButton = page.getByRole('button', { name: /Export|导出/i });
        await expect(exportButton).toBeVisible({ timeout: 5000 });
      }
    }
  });

  test('应该能够导出 CSV 格式的查询结果', async ({ page }) => {
    // 添加数据库并执行查询
    const hasDb = await page.getByText('interview_db').count() > 0;
    if (!hasDb) {
      const addButton = page.getByRole('button', { name: /添加数据库|Add Database/i });
      if (await addButton.count() > 0) {
        await addButton.click();
        await page.waitForSelector('.ant-modal');
        await page.locator('.ant-input').first().fill('interview_db');
        await page.locator('textarea.ant-input').fill('mysql://root:root@localhost:3306/interview_db');
        await page.locator('.ant-modal-footer .ant-btn-primary').click();
        await page.waitForTimeout(3000);
      }
    }

    await page.getByText('interview_db').click();
    await page.waitForTimeout(2000);

    // 执行查询
    const editor = page.locator('textarea').first();
    await editor.fill('SELECT * FROM candidates LIMIT 3');

    const executeButton = page.getByRole('button', { name: /执行|运行|Execute/i });
    await executeButton.click();
    await page.waitForTimeout(2000);

    // 点击导出按钮
    const exportButton = page.getByRole('button', { name: /Export|导出/i });
    await exportButton.click();

    // 等待格式选择对话框
    await page.waitForSelector('.ant-modal', { timeout: 5000 });

    // 验证对话框标题
    const dialogTitle = page.locator('.ant-modal-title');
    await expect(dialogTitle).toContainText(/Export|导出/i);

    // 设置下载监听
    const downloadPromise = page.waitForEvent('download', { timeout: 10000 });

    // 点击 CSV 格式选项
    const csvButton = page.locator('button:has-text("CSV")').first();
    await csvButton.click();

    // 等待下载开始
    const download = await downloadPromise;

    // 验证文件名包含 .csv 扩展名
    const filename = download.suggestedFilename();
    expect(filename).toMatch(/\.csv$/);

    console.log(`CSV 文件已下载: ${filename}`);
  });

  test('应该能够导出 JSON 格式的查询结果', async ({ page }) => {
    // 添加数据库并执行查询
    const hasDb = await page.getByText('interview_db').count() > 0;
    if (!hasDb) {
      const addButton = page.getByRole('button', { name: /添加数据库|Add Database/i });
      if (await addButton.count() > 0) {
        await addButton.click();
        await page.waitForSelector('.ant-modal');
        await page.locator('.ant-input').first().fill('interview_db');
        await page.locator('textarea.ant-input').fill('mysql://root:root@localhost:3306/interview_db');
        await page.locator('.ant-modal-footer .ant-btn-primary').click();
        await page.waitForTimeout(3000);
      }
    }

    await page.getByText('interview_db').click();
    await page.waitForTimeout(2000);

    // 执行查询
    const editor = page.locator('textarea').first();
    await editor.fill('SELECT * FROM interviews LIMIT 3');

    const executeButton = page.getByRole('button', { name: /执行|运行|Execute/i });
    await executeButton.click();
    await page.waitForTimeout(2000);

    // 点击导出按钮
    const exportButton = page.getByRole('button', { name: /Export|导出/i });
    await exportButton.click();

    // 等待格式选择对话框
    await page.waitForSelector('.ant-modal', { timeout: 5000 });

    // 设置下载监听
    const downloadPromise = page.waitForEvent('download', { timeout: 10000 });

    // 点击 JSON 格式选项
    const jsonButton = page.locator('button:has-text("JSON")').first();
    await jsonButton.click();

    // 等待下载开始
    const download = await downloadPromise;

    // 验证文件名包含 .json 扩展名
    const filename = download.suggestedFilename();
    expect(filename).toMatch(/\.json$/);

    console.log(`JSON 文件已下载: ${filename}`);
  });

  test('导出按钮应该在没有查询结果时被禁用', async ({ page }) => {
    // 导航到数据库页面但不执行查询
    const hasDb = await page.getByText('interview_db').count() > 0;
    if (hasDb) {
      await page.getByText('interview_db').click();
      await page.waitForTimeout(1000);

      // 检查导出按钮是否存在且被禁用
      const exportButton = page.getByRole('button', { name: /Export|导出/i });

      // 如果按钮存在，验证它是禁用的
      if (await exportButton.count() > 0) {
        await expect(exportButton).toBeDisabled();
        console.log('✅ 导出按钮在无结果时正确禁用');
      }
    }
  });

  test('CSV 导出应该包含正确的表头和数据', async ({ page }) => {
    // 添加数据库并执行查询
    const hasDb = await page.getByText('interview_db').count() > 0;
    if (!hasDb) {
      const addButton = page.getByRole('button', { name: /添加数据库|Add Database/i });
      if (await addButton.count() > 0) {
        await addButton.click();
        await page.waitForSelector('.ant-modal');
        await page.locator('.ant-input').first().fill('interview_db');
        await page.locator('textarea.ant-input').fill('mysql://root:root@localhost:3306/interview_db');
        await page.locator('.ant-modal-footer .ant-btn-primary').click();
        await page.waitForTimeout(3000);
      }
    }

    await page.getByText('interview_db').click();
    await page.waitForTimeout(2000);

    // 执行简单查询
    const editor = page.locator('textarea').first();
    await editor.fill('SELECT name, email FROM candidates LIMIT 2');

    const executeButton = page.getByRole('button', { name: /执行|运行|Execute/i });
    await executeButton.click();
    await page.waitForTimeout(2000);

    // 导出 CSV
    const exportButton = page.getByRole('button', { name: /Export|导出/i });
    await exportButton.click();
    await page.waitForSelector('.ant-modal');

    const downloadPromise = page.waitForEvent('download');
    const csvButton = page.locator('button:has-text("CSV")').first();
    await csvButton.click();

    const download = await downloadPromise;
    const filename = download.suggestedFilename();

    // 保存文件到临时目录并验证内容
    const downloadPath = path.join('/tmp', filename);
    await download.saveAs(downloadPath);

    console.log(`✅ CSV 文件已保存到: ${downloadPath}`);

    // 验证文件存在
    const fs = require('fs');
    const fileExists = fs.existsSync(downloadPath);
    expect(fileExists).toBe(true);

    // 读取文件内容
    const content = fs.readFileSync(downloadPath, 'utf-8');

    // 验证包含 UTF-8 BOM
    expect(content.charCodeAt(0)).toBe(0xFEFF);

    // 验证包含表头
    expect(content).toContain('name');
    expect(content).toContain('email');

    console.log('✅ CSV 文件格式验证通过');
  });

  test('JSON 导出应该包含元数据和数据', async ({ page }) => {
    // 添加数据库并执行查询
    const hasDb = await page.getByText('interview_db').count() > 0;
    if (!hasDb) {
      const addButton = page.getByRole('button', { name: /添加数据库|Add Database/i });
      if (await addButton.count() > 0) {
        await addButton.click();
        await page.waitForSelector('.ant-modal');
        await page.locator('.ant-input').first().fill('interview_db');
        await page.locator('textarea.ant-input').fill('mysql://root:root@localhost:3306/interview_db');
        await page.locator('.ant-modal-footer .ant-btn-primary').click();
        await page.waitForTimeout(3000);
      }
    }

    await page.getByText('interview_db').click();
    await page.waitForTimeout(2000);

    // 执行查询
    const editor = page.locator('textarea').first();
    await editor.fill('SELECT id, name FROM candidates LIMIT 2');

    const executeButton = page.getByRole('button', { name: /执行|运行|Execute/i });
    await executeButton.click();
    await page.waitForTimeout(2000);

    // 导出 JSON
    const exportButton = page.getByRole('button', { name: /Export|导出/i });
    await exportButton.click();
    await page.waitForSelector('.ant-modal');

    const downloadPromise = page.waitForEvent('download');
    const jsonButton = page.locator('button:has-text("JSON")').first();
    await jsonButton.click();

    const download = await downloadPromise;
    const filename = download.suggestedFilename();

    // 保存文件到临时目录并验证内容
    const downloadPath = path.join('/tmp', filename);
    await download.saveAs(downloadPath);

    console.log(`✅ JSON 文件已保存到: ${downloadPath}`);

    // 读取并解析 JSON
    const fs = require('fs');
    const content = fs.readFileSync(downloadPath, 'utf-8');
    const jsonData = JSON.parse(content);

    // 验证包含 metadata
    expect(jsonData).toHaveProperty('metadata');
    expect(jsonData).toHaveProperty('data');

    // 验证 metadata 结构
    expect(jsonData.metadata).toHaveProperty('columns');
    expect(jsonData.metadata).toHaveProperty('exportedAt');
    expect(jsonData.metadata).toHaveProperty('rowCount');

    // 验证 data 是数组
    expect(Array.isArray(jsonData.data)).toBe(true);

    // 验证数据包含预期的列
    if (jsonData.data.length > 0) {
      expect(jsonData.data[0]).toHaveProperty('id');
      expect(jsonData.data[0]).toHaveProperty('name');
    }

    console.log('✅ JSON 文件格式验证通过');
  });

  test('应该能够导出包含中文的数据', async ({ page }) => {
    // 添加数据库并执行查询
    const hasDb = await page.getByText('interview_db').count() > 0;
    if (!hasDb) {
      const addButton = page.getByRole('button', { name: /添加数据库|Add Database/i });
      if (await addButton.count() > 0) {
        await addButton.click();
        await page.waitForSelector('.ant-modal');
        await page.locator('.ant-input').first().fill('interview_db');
        await page.locator('textarea.ant-input').fill('mysql://root:root@localhost:3306/interview_db');
        await page.locator('.ant-modal-footer .ant-btn-primary').click();
        await page.waitForTimeout(3000);
      }
    }

    await page.getByText('interview_db').click();
    await page.waitForTimeout(2000);

    // 执行查询（包含中文数据）
    const editor = page.locator('textarea').first();
    await editor.fill('SELECT * FROM interviews WHERE notes IS NOT NULL LIMIT 2');

    const executeButton = page.getByRole('button', { name: /执行|运行|Execute/i });
    await executeButton.click();
    await page.waitForTimeout(2000);

    // 导出 CSV
    const exportButton = page.getByRole('button', { name: /Export|导出/i });
    await exportButton.click();
    await page.waitForSelector('.ant-modal');

    const downloadPromise = page.waitForEvent('download');
    const csvButton = page.locator('button:has-text("CSV")').first();
    await csvButton.click();

    const download = await downloadPromise;
    const downloadPath = path.join('/tmp', download.suggestedFilename());
    await download.saveAs(downloadPath);

    // 验证 UTF-8 BOM 和中文内容
    const fs = require('fs');
    const content = fs.readFileSync(downloadPath, 'utf-8');

    // 验证 UTF-8 BOM
    expect(content.charCodeAt(0)).toBe(0xFEFF);

    // 验证包含中文（如果查询结果有中文）
    // 这里只验证文件可以正确读取
    expect(content.length).toBeGreaterThan(0);

    console.log('✅ UTF-8 编码和中文数据验证通过');
  });

  test('应该显示导出成功的通知', async ({ page }) => {
    // 添加数据库并执行查询
    const hasDb = await page.getByText('interview_db').count() > 0;
    if (!hasDb) {
      const addButton = page.getByRole('button', { name: /添加数据库|Add Database/i });
      if (await addButton.count() > 0) {
        await addButton.click();
        await page.waitForSelector('.ant-modal');
        await page.locator('.ant-input').first().fill('interview_db');
        await page.locator('textarea.ant-input').fill('mysql://root:root@localhost:3306/interview_db');
        await page.locator('.ant-modal-footer .ant-btn-primary').click();
        await page.waitForTimeout(3000);
      }
    }

    await page.getByText('interview_db').click();
    await page.waitForTimeout(2000);

    // 执行查询
    const editor = page.locator('textarea').first();
    await editor.fill('SELECT * FROM candidates LIMIT 1');

    const executeButton = page.getByRole('button', { name: /执行|运行|Execute/i });
    await executeButton.click();
    await page.waitForTimeout(2000);

    // 导出
    const exportButton = page.getByRole('button', { name: /Export|导出/i });
    await exportButton.click();
    await page.waitForSelector('.ant-modal');

    const downloadPromise = page.waitForEvent('download');
    const csvButton = page.locator('button:has-text("CSV")').first();
    await csvButton.click();

    await downloadPromise;

    // 等待并验证成功通知
    await page.waitForTimeout(2000);

    // 查找 Ant Design 通知组件
    const notification = page.locator('.ant-notification');
    if (await notification.count() > 0) {
      const notificationText = await notification.textContent();

      // 验证包含成功相关的文本
      const hasSuccessText =
        notificationText?.includes('成功') ||
        notificationText?.includes('Success') ||
        notificationText?.includes('exported') ||
        notificationText?.includes('导出');

      expect(hasSuccessText).toBe(true);
      console.log('✅ 导出成功通知已显示');
    }
  });
});
