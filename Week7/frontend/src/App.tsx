import { useEffect, useState } from 'react';
import { Loader2 } from 'lucide-react';
import { Toaster, toast } from 'sonner';
import { useAppStore } from './store/appStore';
import { StyleInitializer } from './components/StyleInitializer';
import { Sidebar } from './components/Sidebar';
import { SlideEditor } from './components/SlideEditor';
import { Carousel } from './components/Carousel';
import './index.css';

function App() {
  const {
    style_reference,
    slides,
    loading,
    error,
    currentSlideId,
    loadProject,
    setCurrentSlide,
    createSlide,
    deleteSlide,
    reorderSlides,
    updateSlideInState,
  } = useAppStore();

  const [showCarousel, setShowCarousel] = useState(false);

  useEffect(() => {
    loadProject();
  }, [loadProject]);

  // 显示错误提示
  useEffect(() => {
    if (error) {
      toast.error(error);
    }
  }, [error]);

  const handleStyleSelected = async () => {
    // 重新加载项目状态
    await loadProject();
  };

  const handleAddSlide = async () => {
    try {
      await createSlide('新幻灯片\n\n点击编辑内容...');
      toast.success('幻灯片已创建');
    } catch (err) {
      toast.error('创建失败,请重试');
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

  // 获取当前选中的幻灯片
  const currentSlide = slides.find((s) => s.id === currentSlideId) || null;

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
        <StyleInitializer onStyleSelected={handleStyleSelected} />
      )}

      {/* Main Content (only show after style is selected) */}
      {style_reference && (
        <>
          {/* Sidebar */}
          <Sidebar
            slides={slides}
            currentSlideId={currentSlideId}
            onSelectSlide={setCurrentSlide}
            onReorderSlides={handleReorderSlides}
            onAddSlide={handleAddSlide}
            onDeleteSlide={handleDeleteSlide}
            onPlayPresentation={handlePlayPresentation}
          />

          {/* Editor */}
          <SlideEditor
            slide={currentSlide}
            onSlideUpdated={updateSlideInState}
          />
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
