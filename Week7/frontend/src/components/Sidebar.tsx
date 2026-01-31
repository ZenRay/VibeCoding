import React, { useState } from 'react';
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
} from '@dnd-kit/core';
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { Plus, Trash2, GripVertical, Play } from 'lucide-react';
import type { Slide } from '../types';

interface SidebarProps {
  slides: Slide[];
  currentSlideId: string | null;
  onSelectSlide: (slideId: string) => void;
  onReorderSlides: (slideIds: string[]) => Promise<void>;
  onAddSlide: () => Promise<void>;
  onDeleteSlide: (slideId: string) => Promise<void>;
  onPlayPresentation: () => void;
}

interface SortableSlideItemProps {
  slide: Slide;
  isActive: boolean;
  onSelect: () => void;
  onDelete: (e: React.MouseEvent) => void;
}

const SortableSlideItem: React.FC<SortableSlideItemProps> = ({
  slide,
  isActive,
  onSelect,
  onDelete,
}) => {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: slide.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`
        group relative bg-white rounded-lg border-2 transition-all cursor-pointer
        ${isActive 
          ? 'border-purple-500 shadow-lg ring-2 ring-purple-200' 
          : 'border-gray-200 hover:border-purple-300 hover:shadow-md'
        }
        ${isDragging ? 'z-50 shadow-2xl' : ''}
      `}
    >
      <div className="flex items-start gap-2 p-3" onClick={onSelect}>
        {/* Drag Handle */}
        <div
          {...attributes}
          {...listeners}
          className="flex-shrink-0 text-gray-400 hover:text-gray-600 cursor-grab active:cursor-grabbing pt-1"
        >
          <GripVertical className="w-5 h-5" />
        </div>

        {/* Thumbnail */}
        <div className="flex-shrink-0 w-20 h-14 bg-gradient-to-br from-gray-100 to-gray-200 rounded overflow-hidden">
          {slide.image_path ? (
            <img
              src={`http://localhost:8000/${slide.image_path}`}
              alt="幻灯片缩略图"
              className="w-full h-full object-cover"
              onError={(e) => {
                e.currentTarget.style.display = 'none';
              }}
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-gray-400 text-xs">
              无图片
            </div>
          )}
        </div>

        {/* Text Preview */}
        <div className="flex-1 min-w-0">
          <p className="text-sm text-gray-800 line-clamp-2 leading-tight">
            {slide.text || '空白幻灯片'}
          </p>
          {slide.content_hash !== slide.image_hash && slide.image_path && (
            <span className="inline-block mt-1 text-xs text-orange-600 bg-orange-50 px-2 py-0.5 rounded">
              需重新生成
            </span>
          )}
        </div>

        {/* Delete Button */}
        <button
          onClick={onDelete}
          className="flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity p-1.5 hover:bg-red-50 rounded text-red-500 hover:text-red-700"
          title="删除幻灯片"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};

export const Sidebar: React.FC<SidebarProps> = ({
  slides,
  currentSlideId,
  onSelectSlide,
  onReorderSlides,
  onAddSlide,
  onDeleteSlide,
  onPlayPresentation,
}) => {
  const [isReordering, setIsReordering] = useState(false);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8, // 防止误触
      },
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const handleDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event;

    if (over && active.id !== over.id) {
      const oldIndex = slides.findIndex((s) => s.id === active.id);
      const newIndex = slides.findIndex((s) => s.id === over.id);

      const newOrder = arrayMove(slides, oldIndex, newIndex);
      const newIds = newOrder.map((s) => s.id);

      try {
        setIsReordering(true);
        await onReorderSlides(newIds);
      } catch (err) {
        console.error('Reorder failed:', err);
      } finally {
        setIsReordering(false);
      }
    }
  };

  const handleDelete = async (e: React.MouseEvent, slideId: string) => {
    e.stopPropagation();
    if (confirm('确定要删除这张幻灯片吗?')) {
      await onDeleteSlide(slideId);
    }
  };

  return (
    <div className="w-80 bg-gray-50 border-r border-gray-200 flex flex-col h-screen">
      {/* Header */}
      <div className="px-4 py-5 bg-white border-b border-gray-200">
        <h2 className="text-lg font-bold text-gray-800 mb-3">幻灯片列表</h2>
        
        {/* Action Buttons */}
        <div className="space-y-2">
          <button
            onClick={onAddSlide}
            className="w-full bg-purple-600 hover:bg-purple-700 text-white py-2.5 px-4 rounded-lg font-medium transition-colors flex items-center justify-center gap-2 shadow-sm"
          >
            <Plus className="w-5 h-5" />
            添加幻灯片
          </button>

          {slides.length > 0 && (
            <button
              onClick={onPlayPresentation}
              className="w-full bg-green-600 hover:bg-green-700 text-white py-2.5 px-4 rounded-lg font-medium transition-colors flex items-center justify-center gap-2 shadow-sm"
            >
              <Play className="w-5 h-5" />
              播放演示
            </button>
          )}
        </div>
      </div>

      {/* Slides List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {slides.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <p className="text-sm">暂无幻灯片</p>
            <p className="text-xs mt-1">点击上方按钮添加</p>
          </div>
        ) : (
          <DndContext
            sensors={sensors}
            collisionDetection={closestCenter}
            onDragEnd={handleDragEnd}
          >
            <SortableContext
              items={slides.map((s) => s.id)}
              strategy={verticalListSortingStrategy}
            >
              {slides.map((slide) => (
                <SortableSlideItem
                  key={slide.id}
                  slide={slide}
                  isActive={slide.id === currentSlideId}
                  onSelect={() => onSelectSlide(slide.id)}
                  onDelete={(e) => handleDelete(e, slide.id)}
                />
              ))}
            </SortableContext>
          </DndContext>
        )}

        {isReordering && (
          <div className="fixed inset-0 bg-black/10 flex items-center justify-center z-50 pointer-events-none">
            <div className="bg-white px-4 py-2 rounded-lg shadow-lg text-sm text-gray-600">
              正在保存顺序...
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="px-4 py-3 bg-white border-t border-gray-200">
        <p className="text-xs text-gray-500 text-center">
          共 {slides.length} 张幻灯片
        </p>
      </div>
    </div>
  );
};
