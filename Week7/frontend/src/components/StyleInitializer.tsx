import React, { useState } from 'react';
import { X, Loader2, Sparkles } from 'lucide-react';
import { api } from '../api/client';
import type { StyleCandidate } from '../types';

interface StyleInitializerProps {
  onStyleSelected: () => void;
}

export const StyleInitializer: React.FC<StyleInitializerProps> = ({ onStyleSelected }) => {
  const [description, setDescription] = useState('');
  const [candidates, setCandidates] = useState<StyleCandidate[]>([]);
  const [loading, setLoading] = useState(false);
  const [selecting, setSelecting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleGenerate = async () => {
    if (!description.trim()) {
      setError('请输入风格描述');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const result = await api.initStyle({ description: description.trim() });
      setCandidates(result);
    } catch (err) {
      setError('生成风格失败,请重试');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSelect = async (imagePath: string) => {
    try {
      setSelecting(true);
      setError(null);
      await api.selectStyle({ image_path: imagePath });
      onStyleSelected();
    } catch (err) {
      setError('保存风格失败,请重试');
      console.error(err);
    } finally {
      setSelecting(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleGenerate();
    }
  };

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-gradient-to-r from-purple-600 to-blue-600 text-white px-8 py-6 rounded-t-2xl">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Sparkles className="w-8 h-8" />
              <div>
                <h2 className="text-2xl font-bold">初始化幻灯片风格</h2>
                <p className="text-purple-100 text-sm mt-1">
                  描述您想要的视觉风格,AI 将生成 2 个候选方案供您选择
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="p-8 space-y-6">
          {/* Input Section */}
          <div className="space-y-3">
            <label className="block text-sm font-semibold text-gray-700">
              风格描述 <span className="text-red-500">*</span>
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="例如: 现代简约风格,使用蓝色和白色作为主色调,扁平化设计,适合科技产品演示"
              className="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-purple-500 focus:ring-4 focus:ring-purple-100 outline-none transition-all resize-none text-gray-800 placeholder:text-gray-400"
              rows={4}
              disabled={loading || selecting}
            />
            <p className="text-xs text-gray-500">按 Enter 快速生成,Shift+Enter 换行</p>
          </div>

          {/* Generate Button */}
          {candidates.length === 0 && (
            <button
              onClick={handleGenerate}
              disabled={loading || !description.trim()}
              className="w-full bg-gradient-to-r from-purple-600 to-blue-600 text-white py-4 rounded-xl font-semibold hover:from-purple-700 hover:to-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg hover:shadow-xl flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  正在生成风格...
                </>
              ) : (
                <>
                  <Sparkles className="w-5 h-5" />
                  生成风格候选
                </>
              )}
            </button>
          )}

          {/* Error Message */}
          {error && (
            <div className="bg-red-50 border-2 border-red-200 text-red-700 px-4 py-3 rounded-xl flex items-center gap-2">
              <X className="w-5 h-5 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Candidates Display */}
          {candidates.length > 0 && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-gray-800">
                  选择一个您喜欢的风格
                </h3>
                <button
                  onClick={() => {
                    setCandidates([]);
                    setDescription('');
                  }}
                  className="text-sm text-gray-500 hover:text-gray-700 underline"
                  disabled={selecting}
                >
                  重新生成
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {candidates.map((candidate, index) => (
                  <div
                    key={candidate.image_path}
                    className="group relative bg-gray-50 rounded-xl overflow-hidden border-2 border-gray-200 hover:border-purple-500 transition-all cursor-pointer"
                    onClick={() => !selecting && handleSelect(candidate.image_path)}
                  >
                    {/* Image Preview */}
                    <div className="aspect-video bg-gradient-to-br from-gray-100 to-gray-200 flex items-center justify-center relative overflow-hidden">
                      <img
                        src={`http://localhost:8000/${candidate.image_path}`}
                        alt={`候选风格 ${index + 1}`}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                        onError={(e) => {
                          e.currentTarget.style.display = 'none';
                          e.currentTarget.parentElement!.innerHTML = `<div class="text-gray-400 text-center px-4"><svg class="w-16 h-16 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path></svg><p class="text-sm">风格图片 ${index + 1}</p></div>`;
                        }}
                      />
                      
                      {/* Hover Overlay */}
                      <div className="absolute inset-0 bg-purple-600/0 group-hover:bg-purple-600/20 transition-all flex items-center justify-center">
                        <div className="bg-white px-6 py-3 rounded-full font-semibold text-purple-600 opacity-0 group-hover:opacity-100 transform scale-90 group-hover:scale-100 transition-all shadow-lg">
                          选择此风格
                        </div>
                      </div>

                      {/* Loading Overlay */}
                      {selecting && (
                        <div className="absolute inset-0 bg-white/90 flex items-center justify-center">
                          <Loader2 className="w-8 h-8 text-purple-600 animate-spin" />
                        </div>
                      )}
                    </div>

                    {/* Label */}
                    <div className="px-4 py-3 bg-white">
                      <p className="text-sm font-medium text-gray-700 text-center">
                        候选风格 {index + 1}
                      </p>
                    </div>
                  </div>
                ))}
              </div>

              <p className="text-xs text-gray-500 text-center">
                点击任意候选风格进行选择,选择后将应用于所有幻灯片
              </p>
            </div>
          )}

          {/* Loading State */}
          {loading && (
            <div className="flex flex-col items-center justify-center py-12 space-y-4">
              <Loader2 className="w-12 h-12 text-purple-600 animate-spin" />
              <p className="text-gray-600 font-medium">AI 正在生成风格候选图片...</p>
              <p className="text-sm text-gray-500">这可能需要几秒钟时间</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
