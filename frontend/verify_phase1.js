#!/usr/bin/env node
/**
 * 前端阶段 1 验证脚本
 * 用于验证前端项目的基础设施是否正常
 */

const fs = require('fs')
const path = require('path')

console.log('='.repeat(60))
console.log('前端阶段 1 验证脚本')
console.log('='.repeat(60))

let allPassed = true

// 检查文件是否存在
function checkFile(filePath, description) {
  const fullPath = path.join(__dirname, filePath)
  if (fs.existsSync(fullPath)) {
    console.log(`  ✅ ${description}`)
    return true
  } else {
    console.log(`  ❌ ${description} - 文件不存在: ${filePath}`)
    return false
  }
}

// 检查目录是否存在
function checkDir(dirPath, description) {
  const fullPath = path.join(__dirname, dirPath)
  if (fs.existsSync(fullPath) && fs.statSync(fullPath).isDirectory()) {
    console.log(`  ✅ ${description}`)
    return true
  } else {
    console.log(`  ❌ ${description} - 目录不存在: ${dirPath}`)
    return false
  }
}

console.log('\n🔍 检查项目结构...')

// 检查配置文件
allPassed &= checkFile('package.json', 'package.json')
allPassed &= checkFile('tsconfig.json', 'tsconfig.json')
allPassed &= checkFile('vite.config.ts', 'vite.config.ts')
allPassed &= checkFile('tailwind.config.js', 'tailwind.config.js')
allPassed &= checkFile('components.json', 'components.json')

// 检查源代码目录
allPassed &= checkDir('src', 'src 目录')
allPassed &= checkDir('src/components', 'src/components 目录')
allPassed &= checkDir('src/pages', 'src/pages 目录')
allPassed &= checkDir('src/services', 'src/services 目录')
allPassed &= checkDir('src/hooks', 'src/hooks 目录')
allPassed &= checkDir('src/store', 'src/store 目录')
allPassed &= checkDir('src/types', 'src/types 目录')
allPassed &= checkDir('src/lib', 'src/lib 目录')
allPassed &= checkDir('src/styles', 'src/styles 目录')

// 检查关键文件
console.log('\n🔍 检查关键文件...')
allPassed &= checkFile('src/main.tsx', 'main.tsx')
allPassed &= checkFile('src/App.tsx', 'App.tsx')
allPassed &= checkFile('src/types/ticket.ts', 'Ticket 类型定义')
allPassed &= checkFile('src/types/tag.ts', 'Tag 类型定义')
allPassed &= checkFile('src/services/api.ts', 'API 服务配置')
allPassed &= checkFile('src/services/ticketService.ts', 'Ticket Service')
allPassed &= checkFile('src/services/tagService.ts', 'Tag Service')
allPassed &= checkFile('src/store/useStore.ts', '状态管理 Store')
allPassed &= checkFile('src/hooks/useTickets.ts', 'useTickets Hook')
allPassed &= checkFile('src/hooks/useTags.ts', 'useTags Hook')
allPassed &= checkFile('src/hooks/useDebounce.ts', 'useDebounce Hook')

// 检查 package.json 依赖
console.log('\n🔍 检查依赖配置...')
try {
  const packageJson = JSON.parse(fs.readFileSync('package.json', 'utf8'))
  const requiredDeps = [
    'react',
    'react-dom',
    'axios',
    'zustand',
    'react-router-dom',
    'tailwindcss',
  ]

  const missingDeps = requiredDeps.filter(
    (dep) => !packageJson.dependencies[dep] && !packageJson.devDependencies[dep]
  )

  if (missingDeps.length === 0) {
    console.log('  ✅ 所有必需依赖已配置')
  } else {
    console.log(`  ❌ 缺少依赖: ${missingDeps.join(', ')}`)
    allPassed = false
  }
} catch (error) {
  console.log(`  ❌ 无法读取 package.json: ${error.message}`)
  allPassed = false
}

// 总结
console.log('\n' + '='.repeat(60))
console.log('验证结果总结')
console.log('='.repeat(60))

if (allPassed) {
  console.log('🎉 所有检查通过！前端阶段 1 已完成。')
  console.log('\n下一步：')
  console.log('  1. 运行 npm install 安装依赖')
  console.log('  2. 运行 npm run dev 启动开发服务器')
  console.log('  3. 访问 http://localhost:5173')
  console.log('  4. 开始阶段 4：实现 UI 组件和核心功能')
} else {
  console.log('⚠️  部分检查未通过，请根据上述提示修复问题。')
}

console.log('='.repeat(60))

process.exit(allPassed ? 0 : 1)
