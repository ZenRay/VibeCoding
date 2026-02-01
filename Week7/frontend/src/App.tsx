import { useEffect, useState } from 'react';
import { Loader2 } from 'lucide-react';
import { Toaster, toast } from 'sonner';
import { useAppStore } from './store/appStore';
import { VersionSelector } from './components/VersionSelector';
import { StyleInitializer } from './components/StyleInitializer';
import { Sidebar } from './components/Sidebar';
import { SlideViewer } from './components/SlideViewer';
import { SlideEditModal } from './components/SlideEditModal';
import { Carousel } from './components/Carousel';
import './index.css';

function App() {
  const {
    currentVersion,
    style_reference,
    style_prompt,
    slides,
    loading,
    error,
    currentSlideId,
    setVersion,
    loadProject,
    setCurrentSlide,
    createSlide,
    deleteSlide,
    reorderSlides,
    updateSlideInState,
  } = useAppStore();

  const [showCarousel, setShowCarousel] = useState(false);
  const [editingSlideId, setEditingSlideId] = useState<string | null>(null);

  // 显示错误提示
  useEffect(() => {
    if (error) {
      toast.error(error);
    }
  }, [error]);

  const handleSelectVersion = async (version: number) => {
    setVersion(version);
    await loadProject(version);
  };

  const handleStyleSelected = async () => {
    // 风格选择后重新加载项目
    if (currentVersion) {
      await loadProject(currentVersion);
    }
  };

  const handleAddSlide = async () => {
    try {
      await createSlide('新幻灯片\n\n点击编辑内容...');
      toast.success('幻灯片已创建');
    } catch (err) {
      toast.error('创建失败,请重试');
    }
  };

  const handleAddSlideAt = async (afterSlideId: string | null) => {
    try {
      await createSlide('新幻灯片\n\n点击编辑内容...', afterSlideId);
      toast.success('幻灯片已插入');
    } catch (err) {
      toast.error('插入失败,请重试');
    }
  };

  const handleDeleteSlide = async (slideId: string) => {
    try {
      await deleteSlide(slideId);
      toast.success('幻灯片已删除');
    } catch (err) {
      toast.error('删除失败,请重试');
    }
  };

  const handleReorderSlides = async (slideIds: string[]) => {
    try {
      await reorderSlides(slideIds);
      toast.success('顺序已保存');
    } catch (err) {
      toast.error('保存顺序失败');
    }
  };

  const handlePlayPresentation = () => {
    if (slides.length === 0) {
      toast.warning('没有可播放的幻灯片');
      return;
    }
    setShowCarousel(true);
  };

  const handleStyleUpdated = async () => {
    // 风格更新后重新加载项目
    if (currentVersion) {
      await loadProject(currentVersion);
    }
    toast.success('风格已更新');
  };

  const handleDoubleClickSlide = (slideId: string) => {
    setEditingSlideId(slideId);
  };

  const handleCloseEditModal = () => {
    setEditingSlideId(null);
  };

  // 如果没有选择版本，显示版本选择器
  if (!currentVersion) {
    return (
      <>
        <Toaster position="top-right" richColors />
        <VersionSelector onSelectVersion={handleSelectVersion} />
      </>
    );
  }

  // 获取当前选中的幻灯片
  const currentSlide = slides.find((s) => s.id === currentSlideId) || null;
  
  // 获取正在编辑的幻灯片
  const editingSlide = slides.find((s) => s.id === editingSlideId) || null;

  // Loading state
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

  return (
    <div className="flex h-screen overflow-hidden bg-gray-50">
      {/* Toast Notifications */}
      <Toaster position="top-right" richColors />

      {/* Style Initialization Modal */}
      {!style_reference && (
        <StyleInitializer 
          onStyleSelected={handleStyleSelected}
          version={currentVersion}
        />
      )}

      {/* Main Content (only show after style is selected) */}
      {style_reference && (
        <>
          {/* Sidebar */}
          <Sidebar
            slides={slides}
            currentSlideId={currentSlideId}
            currentStyle={style_reference}
            currentPrompt={style_prompt}
            onSelectSlide={setCurrentSlide}
            onDoubleClickSlide={handleDoubleClickSlide}
            onReorderSlides={handleReorderSlides}
            onAddSlide={handleAddSlide}
            onAddSlideAt={handleAddSlideAt}
            onDeleteSlide={handleDeleteSlide}
            onPlayPresentation={handlePlayPresentation}
            onStyleUpdated={handleStyleUpdated}
          />

          {/* Viewer - 居中显示幻灯片 */}
          <SlideViewer 
            slide={currentSlide} 
            onSlideUpdated={updateSlideInState}
          />
          
          {/* Edit Modal - 双击缩略图后显示 */}
          {editingSlide && (
            <SlideEditModal
              slide={editingSlide}
              isOpen={!!editingSlideId}
              onClose={handleCloseEditModal}
              onSlideUpdated={updateSlideInState}
            />
          )}
        </>
      )}

      {/* Carousel */}
      <Carousel
        slides={slides}
        isOpen={showCarousel}
        onClose={() => setShowCarousel(false)}
        initialIndex={0}
      />
    </div>
  );
}

export default App;
