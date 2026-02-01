import React, { useState, useEffect } from 'react';
import { Folder, Plus, Loader2, Calendar, FileText } from 'lucide-react';
import { api } from '../api/client';
import { StyleInitializer } from './StyleInitializer';
import type { VersionInfo } from '../types';

interface VersionSelectorProps {
  onSelectVersion: (version: number) => void;
}

export const VersionSelector: React.FC<VersionSelectorProps> = ({ onSelectVersion }) => {
  const [versions, setVersions] = useState<VersionInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [showNewProject, setShowNewProject] = useState(false);
  const [creatingVersion, setCreatingVersion] = useState(false);

  useEffect(() => {
    loadVersions();
  }, []);

  const loadVersions = async () => {
    try {
      setLoading(true);
      console.log('🔍 Loading versions...');
      const data = await api.listVersions();
      console.log('✅ Loaded versions:', data);
      setVersions(data);
    } catch (err) {
      console.error('❌ Failed to load versions:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateNewVersion = async (stylePrompt: string) => {
    try {
      setCreatingVersion(true);
      const result = await api.createNewVersion({ description: stylePrompt });
      
      // 创建成功后直接选择这个新版本
      onSelectVersion(result.version);
    } catch (err) {
      console.error('Failed to create new version:', err);
      alert('创建新项目失败，请重试');
      setCreatingVersion(false);
    }
  };

  const handleSelectVersion = (version: number) => {
    onSelectVersion(version);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-50 to-blue-50">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="w-12 h-12 text-purple-600 animate-spin" />
          <p className="text-lg font-medium text-gray-700">加载中...</p>
        </div>
      </div>
    );
  }

  // 如果显示创建新项目界面
  if (showNewProject) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 to-blue-50">
        <StyleInitializer
          onStyleSelected={() => {
            // 风格选择完成后，新版本已在 handleCreateNewVersion 中创建
            // 这里不需要额外操作
          }}
          onCreateVersion={handleCreateNewVersion}
          onCancel={() => setShowNewProject(false)}
          isCreating={creatingVersion}
        />
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-50 to-blue-50 p-8">
      <div className="max-w-6xl w-full">
        {/* 标题 */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            AI Slide Generator
          </h1>
          <p className="text-lg text-gray-600">
            选择项目继续编辑，或创建新项目
          </p>
        </div>

        {/* 版本列表 */}
        {versions.length > 0 && (
          <div className="mb-8">
            <h2 className="text-xl font-semibold text-gray-800 mb-4">
              我的项目
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {versions.map((version) => (
                <div
                  key={version.version}
                  className="bg-white rounded-xl shadow-lg overflow-hidden hover:shadow-xl transition-all cursor-pointer group"
                  onClick={() => handleSelectVersion(version.version)}
                >
                  {/* 缩略图区域 */}
                  <div className="relative h-48 bg-gradient-to-br from-purple-100 to-blue-100 flex items-center justify-center">
                    {version.style_reference ? (
                      <img
                        src={`http://localhost:8000/${version.style_reference}`}
                        alt={`Version ${version.version}`}
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <Folder className="w-16 h-16 text-gray-400" />
                    )}
                    
                    {/* 版本号标签 */}
                    <div className="absolute top-4 right-4 bg-white/90 backdrop-blur-sm px-3 py-1 rounded-full">
                      <span className="text-sm font-semibold text-purple-600">
                        v{version.version}
                      </span>
                    </div>
                  </div>

                  {/* 信息区域 */}
                  <div className="p-4">
                    <h3 className="font-semibold text-gray-900 mb-2">
                      {version.project_name || version.style_prompt || `项目 ${version.version}`}
                    </h3>
                    
                    <div className="flex items-center gap-4 text-sm text-gray-600 mb-3">
                      <div className="flex items-center gap-1">
                        <FileText className="w-4 h-4" />
                        <span>{version.slide_count} 张幻灯片</span>
                      </div>
                      {version.created_at && (
                        <div className="flex items-center gap-1">
                          <Calendar className="w-4 h-4" />
                          <span>{version.created_at.split(' ')[0]}</span>
                        </div>
                      )}
                    </div>

                    <button className="w-full bg-purple-600 text-white py-2 rounded-lg hover:bg-purple-700 transition-colors group-hover:bg-purple-700">
                      继续编辑
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 创建新项目按钮 */}
        <div className="flex justify-center">
          <button
            onClick={() => setShowNewProject(true)}
            className="flex items-center gap-3 px-8 py-4 bg-white text-purple-600 border-2 border-purple-600 rounded-xl hover:bg-purple-50 transition-all shadow-lg hover:shadow-xl"
          >
            <Plus className="w-6 h-6" />
            <span className="font-semibold text-lg">创建新项目</span>
          </button>
        </div>

        {/* 空状态提示 */}
        {versions.length === 0 && (
          <div className="text-center text-gray-500 mb-8">
            <p>还没有任何项目，点击下方按钮创建第一个项目</p>
          </div>
        )}
      </div>
    </div>
  );
};
