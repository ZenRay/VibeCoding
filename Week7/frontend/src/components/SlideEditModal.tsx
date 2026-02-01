import React, { useState, useEffect } from 'react';
import { X, Save } from 'lucide-react';
import { api } from '../api/client';
import { useAppStore } from '../store/appStore';
import type { Slide } from '../types';

interface SlideEditModalProps {
  slide: Slide;
  isOpen: boolean;
  onClose: () => void;
  onSlideUpdated: (updatedSlide: Slide) => void;
}

export const SlideEditModal: React.FC<SlideEditModalProps> = ({
  slide,
  isOpen,
  onClose,
  onSlideUpdated,
}) => {
  const [text, setText] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const currentVersion = useAppStore((state) => state.currentVersion);

  useEffect(() => {
    if (isOpen && slide) {
      // 如果是默认文本，显示 "New Slide Content"
      const defaultTexts = ['新幻灯片\n\n点击编辑内容...', '新幻灯片', 'New Slide Content'];
      const isDefault = defaultTexts.some(dt => slide.text.trim() === dt.trim());
      setText(isDefault ? 'New Slide Content' : slide.text);
    }
  }, [isOpen, slide]);

  const handleSave = async () => {
    if (!slide || !currentVersion) return;

    try {
      setIsSaving(true);
      const updated = await api.updateSlide(currentVersion, slide.id, { text });
      onSlideUpdated(updated);
      onClose();
    } catch (err) {
      console.error('保存失败:', err);
      alert('保存失败，请重试');
    } finally {
      setIsSaving(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    // Ctrl/Cmd + Enter 保存
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      handleSave();
    }
    // Escape 返回
    if (e.key === 'Escape') {
      e.preventDefault();
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-3xl max-h-[80vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
          <h2 className="text-xl font-bold text-gray-800">编辑幻灯片内容</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
            disabled={isSaving}
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 p-6 overflow-y-auto">
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={handleKeyDown}
            className="w-full h-full min-h-[400px] px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-purple-500 focus:ring-4 focus:ring-purple-100 outline-none transition-all resize-none text-gray-800 font-mono text-base"
            placeholder="输入幻灯片内容..."
            disabled={isSaving}
            autoFocus
          />
          <p className="text-xs text-gray-500 mt-2">
            提示：Ctrl+Enter 快速保存，Esc 返回
          </p>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 px-6 py-4 border-t border-gray-200 bg-gray-50 rounded-b-2xl">
          <button
            onClick={onClose}
            className="px-6 py-2.5 text-gray-700 bg-white border-2 border-gray-300 rounded-lg font-medium hover:bg-gray-50 transition-colors"
            disabled={isSaving}
          >
            返回
          </button>
          <button
            onClick={handleSave}
            className="px-6 py-2.5 bg-purple-600 text-white rounded-lg font-medium hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
            disabled={isSaving}
          >
            {isSaving ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                保存中...
              </>
            ) : (
              <>
                <Save className="w-4 h-4" />
                保存
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};
