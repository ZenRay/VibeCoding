import React, { useState, useEffect } from 'react';
import { ImageIcon } from 'lucide-react';
import { ImageCandidatesPanel } from './ImageCandidatesPanel';
import type { Slide } from '../types';

interface SlideViewerProps {
  slide: Slide | null;
  onSlideUpdated: (updatedSlide: Slide) => void;  // 新增
}

export const SlideViewer: React.FC<SlideViewerProps> = ({ slide, onSlideUpdated }) => {
  const [previewImage, setPreviewImage] = useState<string | null>(null);

  // 当 slide 改变时，更新预览图片
  useEffect(() => {
    if (slide?.image_path) {
      setPreviewImage(slide.image_path);
    } else {
      setPreviewImage(null);
    }
  }, [slide?.id, slide?.image_path]);

  const handleImagePreview = (imagePath: string) => {
    // 更新预览图片（单击候选图片时调用）
    setPreviewImage(imagePath);
  };

  if (!slide) {
    return (
      <div className="flex-1 flex items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100">
        <div className="text-center">
          <ImageIcon className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500 text-lg">选择一个幻灯片查看</p>
        </div>
      </div>
    );
  }

  const displayImage = previewImage || slide.image_path;

  return (
    <div className="flex-1 flex items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100 p-8 relative">
      {/* Slide Container - 居中放大显示 */}
      <div 
        className="relative bg-white rounded-2xl shadow-2xl overflow-hidden" 
        style={{ width: '1120px', height: '630px' }}
      >
        {displayImage ? (
          <>
            <img
              src={`http://localhost:8000/${displayImage}`}
              alt={`Slide ${slide.id}`}
              className="w-full h-full object-cover"
              onError={(e) => {
                e.currentTarget.style.display = 'none';
                e.currentTarget.nextElementSibling!.classList.remove('hidden');
              }}
            />
            <div className="hidden absolute inset-0 flex items-center justify-center bg-gray-100">
              <div className="text-center text-gray-400">
                <ImageIcon className="w-16 h-16 mx-auto mb-2" />
                <p>图片加载失败</p>
              </div>
            </div>
          </>
        ) : (
          <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-purple-50 to-blue-50">
            <div className="text-center">
              <ImageIcon className="w-24 h-24 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500 text-lg">点击右侧按钮生成图片</p>
            </div>
          </div>
        )}
      </div>

      {/* Image Candidates Panel - 右侧悬浮 */}
      <ImageCandidatesPanel
        slideId={slide.id}
        onImagePreview={handleImagePreview}
        onSlideUpdated={onSlideUpdated}
      />
    </div>
  );
};
