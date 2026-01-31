#!/bin/bash

# AI Slide Generator - 快速验证测试脚本
# 自动打开浏览器并提供测试指引

echo "🎯 AI Slide Generator - 快速验证测试"
echo "======================================"
echo ""

# 检查服务状态
echo "📡 1. 检查服务状态..."
echo ""

# 检查后端
if curl -s http://localhost:8000/docs > /dev/null 2>&1; then
    echo "✅ 后端服务正常 (http://localhost:8000)"
else
    echo "❌ 后端服务未运行，请先启动: ./start-backend.sh"
    exit 1
fi

# 检查前端
if curl -s http://localhost:5173 > /dev/null 2>&1; then
    echo "✅ 前端服务正常 (http://localhost:5173)"
else
    echo "❌ 前端服务未运行，请启动: cd frontend && npm run dev"
    exit 1
fi

echo ""
echo "======================================"
echo "🧪 开始快速验证测试"
echo "======================================"
echo ""

echo "📋 测试清单 (请在浏览器中手动验证):"
echo ""

echo "Phase 1: 风格初始化 (US1)"
echo "  1. [ ] 打开 http://localhost:5173"
echo "  2. [ ] 看到风格初始化模态框"
echo "  3. [ ] 输入描述并生成 2 张候选图"
echo "  4. [ ] 选择一张图片保存"
echo "  5. [ ] 模态框关闭，看到 Toast 提示"
echo ""

echo "Phase 2: 幻灯片管理 (US2)"
echo "  6. [ ] 点击 '+ 新建幻灯片' 创建 3 张"
echo "  7. [ ] 在每张幻灯片输入文本"
echo "  8. [ ] 点击不同幻灯片切换"
echo "  9. [ ] 删除一张幻灯片"
echo ""

echo "Phase 3: 幻灯片编辑 (US3)"
echo "  10. [ ] 编辑文本，看到 '保存中' -> '已保存'"
echo "  11. [ ] 修改文本，出现 '重新生成图片' 按钮"
echo "  12. [ ] 点击重新生成，看到新图片"
echo ""

echo "Phase 4: 拖拽排序 (US2)"
echo "  13. [ ] 拖动幻灯片到不同位置"
echo "  14. [ ] 看到拖拽预览效果"
echo "  15. [ ] 顺序改变并保存"
echo ""

echo "Phase 5: 全屏播放 (US4) ⭐ 重点测试"
echo "  16. [ ] 点击 '播放演示' 按钮"
echo "  17. [ ] 进入全屏黑色背景"
echo "  18. [ ] 等待 5 秒自动翻页"
echo "  19. [ ] 点击左右箭头手动切换"
echo "  20. [ ] 点击暂停/播放按钮"
echo "  21. [ ] 按键盘 ← → Space ESC"
echo "  22. [ ] 看到页面指示器 (圆点)"
echo "  23. [ ] 按 ESC 退出全屏"
echo ""

echo "======================================"
echo "🚀 开始测试"
echo "======================================"
echo ""

# 尝试打开浏览器
if command -v xdg-open > /dev/null; then
    echo "正在打开浏览器..."
    xdg-open http://localhost:5173 &
elif command -v open > /dev/null; then
    echo "正在打开浏览器..."
    open http://localhost:5173 &
else
    echo "请手动打开浏览器访问: http://localhost:5173"
fi

echo ""
echo "📝 提示:"
echo "  - 按照上面的清单逐项测试"
echo "  - 重点测试 Phase 5 (全屏播放) 的所有功能"
echo "  - 如有问题，记录到 FRONTEND_E2E_TEST_RESULT.md"
echo ""
echo "✅ 如果所有测试通过，项目即完成！"
echo ""
