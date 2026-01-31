import { create } from 'zustand';
import type { ProjectState, Slide } from '../types';
import { api } from '../api/client';

interface AppState extends ProjectState {
  // Loading states
  loading: boolean;
  error: string | null;
  
  // Current selection
  currentSlideId: string | null;
  
  // Actions
  loadProject: () => Promise<void>;
  setCurrentSlide: (slideId: string | null) => void;
  
  // Style actions
  selectStyle: (imagePath: string) => Promise<void>;
  
  // Slide actions
  createSlide: (text?: string) => Promise<void>;
  updateSlide: (slideId: string, text: string) => Promise<void>;
  deleteSlide: (slideId: string) => Promise<void>;
  reorderSlides: (slideIds: string[]) => Promise<void>;
  regenerateSlideImage: (slideId: string) => Promise<void>;
  
  // Update single slide in state
  updateSlideInState: (updatedSlide: Slide) => void;
}

export const useAppStore = create<AppState>((set, get) => ({
  // Initial state
  style_reference: null,
  slides: [],
  loading: false,
  error: null,
  currentSlideId: null,

  // Load project from backend
  loadProject: async () => {
    set({ loading: true, error: null });
    try {
      const state = await api.getProject();
      set({ 
        style_reference: state.style_reference,
        slides: state.slides,
        loading: false,
        // 自动选中第一张幻灯片
        currentSlideId: state.slides.length > 0 ? state.slides[0].id : null,
      });
    } catch (err) {
      set({ error: '加载项目失败', loading: false });
      console.error(err);
    }
  },

  setCurrentSlide: (slideId) => {
    set({ currentSlideId: slideId });
  },

  // Style actions
  selectStyle: async (imagePath) => {
    try {
      const state = await api.selectStyle({ image_path: imagePath });
      set({ 
        style_reference: state.style_reference,
        slides: state.slides,
      });
    } catch (err) {
      console.error('选择风格失败:', err);
      throw err;
    }
  },

  // Create slide
  createSlide: async (text = '新幻灯片') => {
    try {
      const newSlide = await api.createSlide({ text });
      const slides = [...get().slides, newSlide];
      set({ 
        slides,
        currentSlideId: newSlide.id, // 自动选中新创建的幻灯片
      });
    } catch (err) {
      console.error('创建幻灯片失败:', err);
      throw err;
    }
  },

  // Update slide text
  updateSlide: async (slideId, text) => {
    try {
      const updatedSlide = await api.updateSlide(slideId, { text });
      const slides = get().slides.map((s) => 
        s.id === slideId ? updatedSlide : s
      );
      set({ slides });
    } catch (err) {
      console.error('更新幻灯片失败:', err);
      throw err;
    }
  },

  // Delete slide
  deleteSlide: async (slideId) => {
    try {
      await api.deleteSlide(slideId);
      const slides = get().slides.filter((s) => s.id !== slideId);
      const currentSlideId = get().currentSlideId;
      
      // 如果删除的是当前选中的幻灯片,自动选中第一张
      const newCurrentId = currentSlideId === slideId 
        ? (slides.length > 0 ? slides[0].id : null)
        : currentSlideId;
      
      set({ 
        slides,
        currentSlideId: newCurrentId,
      });
    } catch (err) {
      console.error('删除幻灯片失败:', err);
      throw err;
    }
  },

  // Reorder slides
  reorderSlides: async (slideIds) => {
    try {
      const state = await api.reorderSlides(slideIds);
      set({ slides: state.slides });
    } catch (err) {
      console.error('重排序失败:', err);
      throw err;
    }
  },

  // Regenerate slide image
  regenerateSlideImage: async (slideId) => {
    try {
      const updatedSlide = await api.regenerateImage(slideId);
      const slides = get().slides.map((s) => 
        s.id === slideId ? updatedSlide : s
      );
      set({ slides });
    } catch (err) {
      console.error('重新生成图片失败:', err);
      throw err;
    }
  },

  // Update single slide in state (used by SlideEditor)
  updateSlideInState: (updatedSlide) => {
    const slides = get().slides.map((s) => 
      s.id === updatedSlide.id ? updatedSlide : s
    );
    set({ slides });
  },
}));
