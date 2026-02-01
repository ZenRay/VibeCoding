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
import { StyleManager } from './StyleManager';
import type { Slide } from '../types';

interface SidebarProps {
  slides: Slide[];
  currentSlideId: string | null;
  currentStyle: string | null;
  currentPrompt: string | null;
  onSelectSlide: (slideId: string) => void;
  onDoubleClickSlide: (slideId: string) => void;  // 新增：双击事件
  onReorderSlides: (slideIds: string[]) => Promise<void>;
  onAddSlide: () => Promise<void>;
  onAddSlideAt: (afterSlideId: string | null) => Promise<void>;
  onDeleteSlide: (slideId: string) => Promise<void>;
  onPlayPresentation: () => void;
  onStyleUpdated: () => void;
}

interface SortableSlideItemProps {
  slide: Slide;
  isActive: boolean;
  onSelect: () => void;
  onDoubleClick: () => void;  // 新增：双击事件
  onDelete: (e: React.MouseEvent) => void;
}

const SortableSlideItem: React.FC<SortableSlideItemProps> = ({
  slide,
  isActive,
  onSelect,
  onDoubleClick,
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
      <div 
        className="relative" 
        onClick={onSelect}
        onDoubleClick={onDoubleClick}  // 添加双击事件
      >
        {/* Drag Handle - 浮动在左上角 */}
        <div
          {...attributes}
          {...listeners}
          className="absolute top-2 left-2 z-10 bg-white/90 backdrop-blur-sm rounded p-1 opacity-0 group-hover:opacity-100 transition-opacity text-gray-400 hover:text-gray-600 cursor-grab active:cursor-grabbing shadow-sm"
        >
          <GripVertical className="w-4 h-4" />
        </div>

        {/* Delete Button - 浮动在右上角 */}
        <button
          onClick={onDelete}
          className="absolute top-2 right-2 z-10 bg-white/90 backdrop-blur-sm rounded p-1.5 opacity-0 group-hover:opacity-100 transition-opacity hover:bg-red-50 text-red-500 hover:text-red-700 shadow-sm"
          title="删除幻灯片"
        >
          <Trash2 className="w-4 h-4" />
        </button>

        {/* Thumbnail - 16:9 比例，纯图片展示 */}
        <div className="w-full aspect-[16/9] bg-gradient-to-br from-gray-100 to-gray-200 rounded-lg overflow-hidden">
          {slide.image_path ? (
            <img
              src={`http://localhost:8000/${slide.image_path}`}
              alt={`幻灯片 ${slide.id.substring(0, 8)}`}
              className="w-full h-full object-cover"
              onError={(e) => {
                e.currentTarget.style.display = 'none';
                const parent = e.currentTarget.parentElement;
                if (parent) {
                  parent.classList.add('flex', 'items-center', 'justify-center');
                  parent.innerHTML = `
                    <div class="text-center text-gray-400">
                      <svg class="w-8 h-8 mx-auto mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                      </svg>
                      <p class="text-xs">图片加载失败</p>
                    </div>
                  `;
                }
              }}
            />
          ) : (
            <div className="w-full h-full flex flex-col items-center justify-center text-gray-400">
              <svg className="w-8 h-8 mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              <p className="text-xs">尚未生成</p>
            </div>
          )}
        </div>

        {/* 状态指示器 - 浮动在底部 */}
        {slide.content_hash !== slide.image_hash && slide.image_path && (
          <div className="absolute bottom-2 left-2 right-2 flex justify-center">
            <span className="inline-block text-xs text-orange-600 bg-orange-50/95 backdrop-blur-sm px-2 py-0.5 rounded shadow-sm">
              内容已更新
            </span>
          </div>
        )}
      </div>
    </div>
  );
};

// 插入分隔线组件
interface InsertDividerProps {
  onClick: () => void;
  position: 'top' | 'between';
}

const InsertDivider: React.FC<InsertDividerProps> = ({ onClick }) => {
  const [isHovered, setIsHovered] = useState(false);
  const [isFocused, setIsFocused] = useState(false);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      onClick();
    }
  };

  return (
    <div
      className="relative group/divider h-3 flex items-center cursor-pointer"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onClick={onClick}
      onKeyDown={handleKeyDown}
      tabIndex={0}
      onFocus={() => setIsFocused(true)}
      onBlur={() => setIsFocused(false)}
      role="button"
      aria-label="在此处插入幻灯片"
    >
      {/* 横实线 */}
      <div 
        className={`
          absolute inset-x-0 h-0.5 transition-all
          ${isHovered || isFocused 
            ? 'bg-purple-500 h-1' 
            : 'bg-gray-300 opacity-0 group-hover/divider:opacity-100'
          }
        `}
      />
      
      {/* Plus 按钮 */}
      {(isHovered || isFocused) && (
        <div className="absolute left-1/2 -translate-x-1/2 -top-3">
          <div className="bg-purple-500 text-white rounded-full p-1 shadow-lg animate-in fade-in zoom-in duration-150">
            <Plus className="w-3 h-3" />
          </div>
        </div>
      )}
    </div>
  );
};

export const Sidebar: React.FC<SidebarProps> = ({
  slides,
  currentSlideId,
  currentStyle,
  currentPrompt,
  onSelectSlide,
  onDoubleClickSlide,
  onReorderSlides,
  onAddSlide,
  onAddSlideAt,
  onDeleteSlide,
  onPlayPresentation,
  onStyleUpdated,
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
    await onDeleteSlide(slideId);
  };

  const handleInsertAt = async (afterSlideId: string | null) => {
    try {
      await onAddSlideAt(afterSlideId);
    } catch (err) {
      console.error('Insert slide failed:', err);
      alert('插入幻灯片失败，请重试');
    }
  };

  return (
    <div className="w-80 bg-gray-50 border-r border-gray-200 flex flex-col h-screen">
      {/* Header */}
      <div className="px-4 py-5 bg-white border-b border-gray-200">
        <h2 className="text-lg font-bold text-gray-800 mb-3">幻灯片列表</h2>
        
        {/* Action Buttons */}
        <div className="space-y-2">
          {/* 新风格生成按钮 */}
          <StyleManager
            currentStyle={currentStyle}
            currentPrompt={currentPrompt}
            onStyleUpdated={onStyleUpdated}
          />

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
      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        {slides.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-gray-500 mb-6">
              <p className="text-sm">暂无幻灯片</p>
              <p className="text-xs mt-1">点击下方按钮添加第一张</p>
            </div>
            <button
              onClick={onAddSlide}
              className="mx-auto bg-purple-600 hover:bg-purple-700 text-white py-3 px-6 rounded-lg font-medium transition-colors flex items-center justify-center gap-2 shadow-lg"
            >
              <Plus className="w-5 h-5" />
              添加第一张幻灯片
            </button>
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
              {/* 顶部插入区 */}
              <InsertDivider 
                position="top"
                onClick={() => handleInsertAt(null)} 
              />
              
              {slides.map((slide) => (
                <React.Fragment key={slide.id}>
                  <SortableSlideItem
                    slide={slide}
                    isActive={slide.id === currentSlideId}
                    onSelect={() => onSelectSlide(slide.id)}
                    onDoubleClick={() => onDoubleClickSlide(slide.id)}
                    onDelete={(e) => handleDelete(e, slide.id)}
                  />
                  
                  {/* 每个 Slide 后面都有插入区（包括最后一个） */}
                  <InsertDivider 
                    position="between"
                    onClick={() => handleInsertAt(slide.id)} 
                  />
                </React.Fragment>
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
