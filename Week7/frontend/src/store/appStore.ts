import { create } from 'zustand';
import type { ProjectState, Slide } from '../types';
import { api } from '../api/client';

// 候选图片接口
export interface ImageCandidate {
  id: string;
  slideId: string;  // 归属的 slide ID
  imagePath: string;
  isSelected: boolean;
}

interface AppState extends ProjectState {
  // Current version
  currentVersion: number | null;
  
  // Loading states
  loading: boolean;
  error: string | null;
  
  // Current selection
  currentSlideId: string | null;
  
  // Image candidates management - 每个 slide 的候选图片
  imageCandidates: Record<string, ImageCandidate[]>;  // slideId -> candidates[]
  
  // Actions
  setVersion: (version: number) => void;
  loadProject: (version: number) => Promise<void>;
  setCurrentSlide: (slideId: string | null) => void;
  
  // Style actions
  selectStyle: (imagePath: string) => Promise<void>;
  
  // Slide actions
  createSlide: (text?: string, afterSlideId?: string | null) => Promise<void>;
  updateSlide: (slideId: string, text: string) => Promise<void>;
  deleteSlide: (slideId: string) => Promise<void>;
  reorderSlides: (slideIds: string[]) => Promise<void>;
  regenerateSlideImage: (slideId: string) => Promise<void>;
  
  // Update single slide in state
  updateSlideInState: (updatedSlide: Slide) => void;
  
  // Image candidates actions
  addImageCandidate: (slideId: string, imagePath: string) => string;  // 返回 candidateId
  selectImageCandidate: (slideId: string, candidateId: string) => void;
  getCandidatesForSlide: (slideId: string) => ImageCandidate[];
}

export const useAppStore = create<AppState>((set, get) => ({
  // Initial state
  currentVersion: null,
  version: null,
  created_at: null,
  project_name: null,
  style_reference: null,
  style_prompt: null,
  slides: [],
  loading: false,
  error: null,
  currentSlideId: null,
  imageCandidates: {},

  // Set current version
  setVersion: (version) => {
    set({ currentVersion: version });
  },

  // Load project from backend
  loadProject: async (version: number) => {
    set({ loading: true, error: null, currentVersion: version });
    try {
      const state = await api.getProject(version);
      set({ 
        version: state.version,
        created_at: state.created_at,
        project_name: state.project_name,
        style_reference: state.style_reference,
        style_prompt: state.style_prompt,
        slides: state.slides,
        loading: false,
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
    const version = get().currentVersion;
    if (!version) {
      throw new Error('No version selected');
    }
    
    try {
      const state = await api.selectStyle(version, { 
        image_path: imagePath,
        style_prompt: get().style_prompt || undefined
      });
      set({ 
        style_reference: state.style_reference,
        style_prompt: state.style_prompt,
      });
    } catch (err) {
      set({ error: '保存风格失败' });
      throw err;
    }
  },

  // Slide actions
  createSlide: async (text = '新幻灯片\n\n点击编辑内容...', afterSlideId = null) => {
    const version = get().currentVersion;
    if (!version) {
      throw new Error('No version selected');
    }
    
    try {
      const newSlide = await api.createSlide(version, { text });
      const slides = get().slides;
      
      // 插入逻辑
      let newSlides;
      if (afterSlideId) {
        const index = slides.findIndex(s => s.id === afterSlideId);
        if (index !== -1) {
          newSlides = [
            ...slides.slice(0, index + 1),
            newSlide,
            ...slides.slice(index + 1)
          ];
        } else {
          newSlides = [...slides, newSlide];
        }
      } else {
        newSlides = [...slides, newSlide];
      }
      
      // 保存顺序
      await api.reorderSlides(version, newSlides.map(s => s.id));
      
      set({ 
        slides: newSlides,
        currentSlideId: newSlide.id
      });
    } catch (err) {
      set({ error: '创建幻灯片失败' });
      throw err;
    }
  },

  updateSlide: async (slideId, text) => {
    const version = get().currentVersion;
    if (!version) {
      throw new Error('No version selected');
    }
    
    try {
      const updated = await api.updateSlide(version, slideId, { text });
      set({
        slides: get().slides.map(s => 
          s.id === slideId ? updated : s
        )
      });
    } catch (err) {
      set({ error: '更新幻灯片失败' });
      throw err;
    }
  },

  deleteSlide: async (slideId) => {
    const version = get().currentVersion;
    if (!version) {
      throw new Error('No version selected');
    }
    
    try {
      await api.deleteSlide(version, slideId);
      const slides = get().slides.filter(s => s.id !== slideId);
      set({ 
        slides,
        currentSlideId: slides.length > 0 ? slides[0].id : null
      });
    } catch (err) {
      set({ error: '删除幻灯片失败' });
      throw err;
    }
  },

  reorderSlides: async (slideIds) => {
    const version = get().currentVersion;
    if (!version) {
      throw new Error('No version selected');
    }
    
    try {
      await api.reorderSlides(version, slideIds);
      const slideMap = new Map(get().slides.map(s => [s.id, s]));
      set({
        slides: slideIds.map(id => slideMap.get(id)!).filter(Boolean)
      });
    } catch (err) {
      set({ error: '更新顺序失败' });
      throw err;
    }
  },

  regenerateSlideImage: async (slideId) => {
    const version = get().currentVersion;
    if (!version) {
      throw new Error('No version selected');
    }
    
    try {
      const updatedSlide = await api.regenerateImage(version, slideId);
      set({
        slides: get().slides.map(s => 
          s.id === slideId ? updatedSlide : s
        )
      });
    } catch (err) {
      set({ error: '生成图片失败' });
      throw err;
    }
  },

  // Update single slide in state
  updateSlideInState: (updatedSlide) => {
    const slides = get().slides.map((s) => 
      s.id === updatedSlide.id ? updatedSlide : s
    );
    set({ slides });
  },

  // Image candidates management
  addImageCandidate: (slideId, imagePath) => {
    const candidateId = `${slideId}-${Date.now()}`;
    const candidates = get().imageCandidates[slideId] || [];
    
    set({
      imageCandidates: {
        ...get().imageCandidates,
        [slideId]: [
          ...candidates.map(c => ({ ...c, isSelected: false })),
          { id: candidateId, slideId, imagePath, isSelected: false }  // 改为 false，不自动选择
        ]
      }
    });
    
    return candidateId;
  },

  selectImageCandidate: (slideId, candidateId) => {
    const candidates = get().imageCandidates[slideId] || [];
    
    set({
      imageCandidates: {
        ...get().imageCandidates,
        [slideId]: candidates.map(c => ({
          ...c,
          isSelected: c.id === candidateId
        }))
      }
    });
  },

  getCandidatesForSlide: (slideId) => {
    return get().imageCandidates[slideId] || [];
  },
}));
