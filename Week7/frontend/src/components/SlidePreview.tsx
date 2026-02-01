import React from 'react';
import { ImageIcon } from 'lucide-react';
import type { Slide } from '../types';

interface SlidePreviewProps {
  slide: Slide | null;
}

export const SlidePreview: React.FC<SlidePreviewProps> = ({ slide }) => {
  if (!slide) {
    return (
      <div className="flex-1 flex items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100">
        <div className="text-center text-gray-400">
          <ImageIcon className="w-16 h-16 mx-auto mb-4 opacity-50" />
          <p className="text-lg font-medium">请选择一张幻灯片</p>
          <p className="text-sm mt-2">双击缩略图进行编辑</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex items-center justify-center bg-gradient-to-br from-gray-800 to-gray-900 p-8">
      {/* Slide 容器 - 16:9 比例 */}
      <div className="relative w-full max-w-6xl aspect-[16/9] bg-white rounded-2xl shadow-2xl overflow-hidden">
        {slide.image_path ? (
          <img
            src={`http://localhost:8000/${slide.image_path}`}
            alt={`幻灯片预览 - ${slide.id.substring(0, 8)}`}
            className="w-full h-full object-contain"
            onError={(e) => {
              e.currentTarget.style.display = 'none';
              const parent = e.currentTarget.parentElement;
              if (parent) {
                parent.classList.add('flex', 'items-center', 'justify-center', 'bg-gradient-to-br', 'from-gray-100', 'to-gray-200');
                parent.innerHTML = `
                  <div class="text-center text-gray-400">
                    <svg class="w-24 h-24 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                    </svg>
                    <p class="text-xl font-medium">图片加载失败</p>
                    <p class="text-sm mt-2">请检查文件路径或重新生成</p>
                  </div>
                `;
              }
            }}
          />
        ) : (
          <div className="w-full h-full flex flex-col items-center justify-center bg-gradient-to-br from-gray-100 to-gray-200 text-gray-400">
            <svg className="w-24 h-24 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            <p className="text-xl font-medium">尚未生成图片</p>
            <p className="text-sm mt-2">双击缩略图编辑内容并生成</p>
          </div>
        )}

        {/* 状态提示 - 浮动在左下角 */}
        {slide.content_hash !== slide.image_hash && slide.image_path && (
          <div className="absolute bottom-6 left-6">
            <div className="bg-orange-500/90 backdrop-blur-sm text-white px-4 py-2 rounded-lg shadow-lg flex items-center gap-2">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <span className="text-sm font-medium">内容已更新，需要重新生成图片</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
