import React, { useState, useEffect, useRef } from 'react';
import { Loader2, RefreshCw, ImageIcon, AlertCircle } from 'lucide-react';
import { api } from '../api/client';
import type { Slide } from '../types';

interface SlideEditorProps {
  slide: Slide | null;
  onSlideUpdated: (updatedSlide: Slide) => void;
}

export const SlideEditor: React.FC<SlideEditorProps> = ({ slide, onSlideUpdated }) => {
  const [text, setText] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved'>('idle');
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const saveTimeoutRef = useRef<number | null>(null);

  // 当切换幻灯片时更新文本
  useEffect(() => {
    if (slide) {
      setText(slide.text);
    }
  }, [slide?.id]);

  // 自动保存逻辑
  const handleTextChange = (newText: string) => {
    setText(newText);
    
    // 取消之前的保存计划
    if (saveTimeoutRef.current) {
      clearTimeout(saveTimeoutRef.current);
    }

    // 如果文本没有变化,不保存
    if (newText === slide?.text) {
      setSaveStatus('idle');
      return;
    }

    setSaveStatus('saving');

    // 延迟保存 (防抖)
    saveTimeoutRef.current = window.setTimeout(async () => {
      await saveText(newText);
    }, 1000);
  };

  const saveText = async (newText: string) => {
    if (!slide || newText === slide.text) {
      setSaveStatus('idle');
      return;
    }

    try {
      setIsSaving(true);
      const updated = await api.updateSlide(slide.id, { text: newText });
      onSlideUpdated(updated);
      setSaveStatus('saved');
      
      // 2秒后清除"已保存"状态
      setTimeout(() => {
        setSaveStatus('idle');
      }, 2000);
    } catch (err) {
      console.error('保存失败:', err);
      setSaveStatus('idle');
      alert('保存失败,请重试');
    } finally {
      setIsSaving(false);
    }
  };

  // 失焦时立即保存
  const handleBlur = async () => {
    if (saveTimeoutRef.current) {
      clearTimeout(saveTimeoutRef.current);
      saveTimeoutRef.current = null;
    }

    if (slide && text !== slide.text) {
      await saveText(text);
    }
  };

  const handleRegenerate = async () => {
    if (!slide) return;

    try {
      setIsGenerating(true);
      const updated = await api.regenerateImage(slide.id);
      onSlideUpdated(updated);
    } catch (err) {
      console.error('重新生成失败:', err);
      alert('生成图片失败,请重试');
    } finally {
      setIsGenerating(false);
    }
  };

  // 检测是否需要重新生成
  const needsRegeneration = slide && slide.content_hash !== slide.image_hash && slide.image_path;

  if (!slide) {
    return (
      <div className="flex-1 flex items-center justify-center bg-gray-50">
        <div className="text-center text-gray-500">
          <ImageIcon className="w-16 h-16 mx-auto mb-4 text-gray-300" />
          <p className="text-lg font-medium">未选择幻灯片</p>
          <p className="text-sm mt-2">从左侧选择或创建一张幻灯片</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col h-screen bg-white">
      {/* Toolbar */}
      <div className="px-6 py-4 bg-white border-b border-gray-200 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h3 className="text-lg font-semibold text-gray-800">编辑幻灯片</h3>
          
          {/* Save Status */}
          <div className="text-xs text-gray-500">
            {saveStatus === 'saving' && (
              <span className="flex items-center gap-1">
                <Loader2 className="w-3 h-3 animate-spin" />
                保存中...
              </span>
            )}
            {saveStatus === 'saved' && (
              <span className="text-green-600 font-medium">✓ 已保存</span>
            )}
          </div>
        </div>

        {/* Regenerate Button */}
        {needsRegeneration && (
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-2 text-sm text-orange-600 bg-orange-50 px-3 py-1.5 rounded-lg">
              <AlertCircle className="w-4 h-4" />
              <span>内容已修改,图片需要更新</span>
            </div>
            <button
              onClick={handleRegenerate}
              disabled={isGenerating}
              className="bg-purple-600 hover:bg-purple-700 disabled:bg-gray-400 text-white px-4 py-2 rounded-lg font-medium transition-colors flex items-center gap-2 shadow-sm"
            >
              {isGenerating ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  生成中...
                </>
              ) : (
                <>
                  <RefreshCw className="w-4 h-4" />
                  重新生成图片
                </>
              )}
            </button>
          </div>
        )}
      </div>

      {/* Editor Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left: Text Editor */}
        <div className="w-1/2 border-r border-gray-200 flex flex-col">
          <div className="px-6 py-3 bg-gray-50 border-b border-gray-200">
            <h4 className="text-sm font-semibold text-gray-700">幻灯片文本</h4>
            <p className="text-xs text-gray-500 mt-1">编辑后自动保存</p>
          </div>
          
          <div className="flex-1 p-6">
            <textarea
              ref={textareaRef}
              value={text}
              onChange={(e) => handleTextChange(e.target.value)}
              onBlur={handleBlur}
              placeholder="输入幻灯片内容..."
              className="w-full h-full resize-none border-2 border-gray-200 rounded-xl px-4 py-3 focus:border-purple-500 focus:ring-4 focus:ring-purple-100 outline-none transition-all text-gray-800 placeholder:text-gray-400 font-mono text-sm leading-relaxed"
              disabled={isSaving}
            />
          </div>

          {/* Character Count */}
          <div className="px-6 py-3 bg-gray-50 border-t border-gray-200">
            <p className="text-xs text-gray-500">
              字符数: {text.length}
            </p>
          </div>
        </div>

        {/* Right: Image Preview */}
        <div className="w-1/2 flex flex-col">
          <div className="px-6 py-3 bg-gray-50 border-b border-gray-200">
            <h4 className="text-sm font-semibold text-gray-700">图片预览</h4>
            <p className="text-xs text-gray-500 mt-1">
              {slide.image_path ? '当前生成的图片' : '尚未生成图片'}
            </p>
          </div>

          <div className="flex-1 p-6 bg-gray-100 flex items-center justify-center relative">
            {isGenerating ? (
              <div className="flex flex-col items-center gap-4">
                <Loader2 className="w-12 h-12 text-purple-600 animate-spin" />
                <p className="text-gray-600 font-medium">AI 正在生成图片...</p>
                <p className="text-sm text-gray-500">这可能需要几秒钟时间</p>
              </div>
            ) : slide.image_path ? (
              <div className="relative w-full h-full flex items-center justify-center">
                <img
                  src={`http://localhost:8000/${slide.image_path}`}
                  alt="幻灯片图片"
                  className="max-w-full max-h-full object-contain rounded-lg shadow-xl"
                  onError={(e) => {
                    e.currentTarget.style.display = 'none';
                    const parent = e.currentTarget.parentElement;
                    if (parent) {
                      parent.innerHTML = `
                        <div class="text-center text-gray-500">
                          <svg class="w-16 h-16 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                          </svg>
                          <p>图片加载失败</p>
                        </div>
                      `;
                    }
                  }}
                />
                
                {/* Hash Mismatch Indicator */}
                {needsRegeneration && (
                  <div className="absolute top-4 right-4 bg-orange-500 text-white px-3 py-1.5 rounded-full text-xs font-semibold shadow-lg flex items-center gap-1">
                    <AlertCircle className="w-3.5 h-3.5" />
                    需要更新
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center text-gray-400">
                <ImageIcon className="w-20 h-20 mx-auto mb-4" />
                <p className="text-lg font-medium">暂无图片</p>
                <p className="text-sm mt-2">保存文本后将自动生成</p>
              </div>
            )}
          </div>

          {/* Image Info */}
          {slide.image_path && (
            <div className="px-6 py-3 bg-gray-50 border-t border-gray-200">
              <p className="text-xs text-gray-500">
                图片路径: {slide.image_path}
              </p>
              <div className="flex gap-4 mt-1">
                <p className="text-xs text-gray-500">
                  内容哈希: {slide.content_hash.substring(0, 8)}...
                </p>
                <p className="text-xs text-gray-500">
                  图片哈希: {slide.image_hash?.substring(0, 8) || 'N/A'}...
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
