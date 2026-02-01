import React, { useState } from 'react';
import { Palette, X, Loader2, RefreshCw } from 'lucide-react';
import { api } from '../api/client';
import { useAppStore } from '../store/appStore';
import type { StyleCandidate } from '../types';

interface StyleManagerProps {
  currentStyle: string | null;
  currentPrompt: string | null;
  onStyleUpdated: () => void;
}

export const StyleManager: React.FC<StyleManagerProps> = ({
  currentStyle,
  currentPrompt,
  onStyleUpdated,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [prompt, setPrompt] = useState(currentPrompt || '');
  const [loading, setLoading] = useState(false);
  const [candidates, setCandidates] = useState<StyleCandidate[]>([]);
  const [selecting, setSelecting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const currentVersion = useAppStore((state) => state.currentVersion);

  const handleOpen = () => {
    setPrompt('');  // 清空输入框，让用户输入新的风格描述
    setIsOpen(true);
    setCandidates([]);
    setError(null);
  };

  const handleClose = () => {
    setIsOpen(false);
    setCandidates([]);
    setError(null);
  };

  const handleGenerate = async () => {
    if (!prompt.trim() || !currentVersion) {
      setError('请输入风格描述');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const result = await api.generateStyle(currentVersion, { description: prompt });
      setCandidates(result);
    } catch (err) {
      setError('生成失败,请重试');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSelect = async (imagePath: string) => {
    if (!currentVersion) return;
    
    try {
      setSelecting(true);
      setError(null);
      await api.selectStyle(currentVersion, { 
        image_path: imagePath,
        style_prompt: prompt
      });
      onStyleUpdated();
      handleClose();
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

  if (!isOpen) {
    return (
      <button
        onClick={handleOpen}
        className="w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white py-2.5 px-4 rounded-lg font-medium transition-colors flex items-center justify-center gap-2 shadow-sm"
      >
        <Palette className="w-5 h-5" />
        新风格生成
      </button>
    );
  }

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-gradient-to-r from-purple-600 to-blue-600 text-white px-8 py-6 rounded-t-2xl">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Palette className="w-8 h-8" />
              <div>
                <h2 className="text-2xl font-bold">生成新风格</h2>
                <p className="text-purple-100 text-sm mt-1">
                  描述新的视觉风格，AI 将生成 2 个全新候选方案
                </p>
              </div>
            </div>
            <button
              onClick={handleClose}
              className="text-white/80 hover:text-white transition-colors"
            >
              <X className="w-6 h-6" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-8 space-y-6">
          {/* Current Style - 仅作参考展示 */}
          {currentStyle && (
            <div className="bg-blue-50 border-2 border-blue-200 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                <p className="text-sm font-semibold text-blue-900">当前风格（参考）</p>
              </div>
              <div className="flex gap-4 items-start">
                <div className="w-40 h-24 bg-gray-100 rounded-lg overflow-hidden flex-shrink-0">
                  <img
                    src={`http://localhost:8000/${currentStyle}`}
                    alt="当前风格"
                    className="w-full h-full object-cover"
                    onError={(e) => {
                      e.currentTarget.style.display = 'none';
                    }}
                  />
                </div>
                <div className="flex-1">
                  <p className="text-xs text-gray-600 mb-1">原始描述:</p>
                  <p className="text-sm text-gray-700 bg-white p-2 rounded border border-gray-200">
                    {currentPrompt || '(无描述)'}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Input Section */}
          <div className="space-y-3">
            <label className="block text-sm font-semibold text-gray-700">
              新风格描述 <span className="text-red-500">*</span>
            </label>
            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="例如: 科技未来风格,深蓝色渐变背景,简约线条设计,适合AI主题演示"
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
              disabled={loading || !prompt.trim()}
              className="w-full bg-gradient-to-r from-purple-600 to-blue-600 text-white py-4 rounded-xl font-semibold hover:from-purple-700 hover:to-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg hover:shadow-xl flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  正在生成新风格...
                </>
              ) : (
                <>
                  <RefreshCw className="w-5 h-5" />
                  生成全新风格候选
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
                  选择一个新风格
                </h3>
                <button
                  onClick={() => setCandidates([])}
                  className="text-sm text-gray-500 hover:text-gray-700 underline"
                  disabled={selecting}
                >
                  再次生成
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {candidates.map((candidate, index) => (
                  <div
                    key={candidate.image_path}
                    className="group relative bg-gray-50 rounded-xl overflow-hidden border-2 border-gray-200 hover:border-purple-500 transition-all cursor-pointer"
                    onClick={() => !selecting && handleSelect(candidate.image_path)}
                  >
                    <div className="aspect-video bg-gradient-to-br from-gray-100 to-gray-200 flex items-center justify-center relative overflow-hidden">
                      <img
                        src={`http://localhost:8000/${candidate.image_path}`}
                        alt={`候选风格 ${index + 1}`}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                      />
                      <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
                      <div className="absolute bottom-4 left-4 right-4 text-white opacity-0 group-hover:opacity-100 transition-opacity">
                        <p className="text-sm font-semibold">点击选择此风格</p>
                      </div>
                    </div>
                    <div className="p-4 bg-white">
                      <p className="text-sm font-medium text-gray-700">
                        候选方案 {index + 1}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Loading State */}
          {loading && (
            <div className="flex flex-col items-center justify-center py-12 space-y-4">
              <Loader2 className="w-12 h-12 text-purple-600 animate-spin" />
              <p className="text-gray-600 font-medium">AI 正在生成全新风格候选...</p>
              <p className="text-sm text-gray-500">这可能需要几秒钟时间</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
