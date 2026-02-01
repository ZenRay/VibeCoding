import React, { useState, useEffect } from 'react';
import { Plus, Loader2, Check } from 'lucide-react';
import { api } from '../api/client';
import { useAppStore, ImageCandidate } from '../store/appStore';
import type { Slide } from '../types';

interface ImageCandidatesPanelProps {
  slideId: string;
  onImagePreview: (imagePath: string) => void;
  onSlideUpdated: (updatedSlide: Slide) => void;  // 新增
}

export const ImageCandidatesPanel: React.FC<ImageCandidatesPanelProps> = ({
  slideId,
  onImagePreview,
  onSlideUpdated,
}) => {
  const [generating, setGenerating] = useState(false);
  const [selectedCandidateId, setSelectedCandidateId] = useState<string | null>(null);
  
  // 从 store 获取当前 slide 的候选图片
  const currentVersion = useAppStore((state) => state.currentVersion);
  const getCandidatesForSlide = useAppStore((state) => state.getCandidatesForSlide);
  const addImageCandidate = useAppStore((state) => state.addImageCandidate);
  const selectImageCandidate = useAppStore((state) => state.selectImageCandidate);
  
  const candidates = getCandidatesForSlide(slideId);

  // 当切换 slide 时，重置选中状态
  useEffect(() => {
    const selectedCandidate = candidates.find(c => c.isSelected);
    setSelectedCandidateId(selectedCandidate?.id || null);
  }, [slideId, candidates]);

  const handleGenerate = async () => {
    if (!currentVersion) return;
    
    try {
      setGenerating(true);
      
      // 调用 API 生成图片（根据当前 slide 的文本和风格）
      const result = await api.regenerateImage(currentVersion, slideId);
      
      if (!result.image_path) {
        throw new Error('未返回图片路径');
      }
      
      // 添加到当前 slide 的候选图片列表
      const candidateId = addImageCandidate(slideId, result.image_path);
      
      // 自动预览新生成的图片
      setSelectedCandidateId(candidateId);
      onImagePreview(result.image_path);
      
    } catch (err) {
      console.error('生成失败:', err);
      alert('生成图片失败，请重试');
    } finally {
      setGenerating(false);
    }
  };

  const handleClickCandidate = (candidate: ImageCandidate) => {
    // 单击：预览图片（更新中间和左侧显示，但不保存到后端）
    setSelectedCandidateId(candidate.id);
    onImagePreview(candidate.imagePath);
    
    // 临时更新前端 store 中的 slide（仅用于显示，不保存到后端）
    // 这样左侧缩略图也会更新
    const slides = useAppStore.getState().slides;
    const currentSlide = slides.find(s => s.id === slideId);
    if (currentSlide) {
      const tempSlide = {
        ...currentSlide,
        image_path: candidate.imagePath  // 临时更新
      };
      onSlideUpdated(tempSlide);
    }
  };

  const handleDoubleClickCandidate = async (candidate: ImageCandidate) => {
    if (!currentVersion) return;
    
    // 双击：确认选择并保存到对应的 slide
    try {
      // 调用后端 API 保存图片路径到文件
      const updatedSlide = await api.updateSlide(currentVersion, slideId, { 
        image_path: candidate.imagePath 
      });
      
      // 更新前端 store（标记为已选择，并更新 slide 的 image_path）
      selectImageCandidate(slideId, candidate.id);
      
      // 通知父组件更新 slide 数据（这会更新左侧缩略图）
      onSlideUpdated(updatedSlide);
      
      // 更新预览
      onImagePreview(candidate.imagePath);
      
    } catch (err) {
      console.error('保存失败:', err);
      alert('保存失败，请重试');
    }
  };

  return (
    <div className="fixed right-4 top-1/2 -translate-y-1/2 flex flex-col gap-3 z-40">
      {/* 已生成的候选图片 */}
      {candidates.map((candidate) => (
        <div
          key={candidate.id}
          className={`
            relative w-32 h-20 rounded-lg overflow-hidden cursor-pointer 
            transition-all shadow-lg hover:shadow-xl
            ${selectedCandidateId === candidate.id 
              ? 'ring-4 ring-purple-500 scale-105' 
              : 'ring-2 ring-gray-300 hover:ring-purple-300'
            }
            ${candidate.isSelected ? 'ring-4 ring-green-500' : ''}
          `}
          onClick={() => handleClickCandidate(candidate)}
          onDoubleClick={() => handleDoubleClickCandidate(candidate)}
        >
          <img
            src={`http://localhost:8000/${candidate.imagePath}`}
            alt="候选图片"
            className="w-full h-full object-cover"
          />
          
          {/* 已选择标记 */}
          {candidate.isSelected && (
            <div className="absolute inset-0 bg-green-500/20 flex items-center justify-center">
              <div className="bg-green-500 text-white rounded-full p-1">
                <Check className="w-4 h-4" />
              </div>
            </div>
          )}
        </div>
      ))}

      {/* 生成按钮/加载状态 */}
      {generating ? (
        <div className="w-32 h-20 rounded-lg border-2 border-dashed border-purple-400 bg-purple-50 flex items-center justify-center">
          <Loader2 className="w-8 h-8 text-purple-600 animate-spin" />
        </div>
      ) : (
        <button
          onClick={handleGenerate}
          className="w-32 h-20 rounded-lg border-2 border-dashed border-gray-400 bg-gray-50 hover:bg-purple-50 hover:border-purple-400 transition-all flex items-center justify-center group"
        >
          <Plus className="w-8 h-8 text-gray-400 group-hover:text-purple-600 transition-colors" />
        </button>
      )}
    </div>
  );
};
