/**
 * API 客户端 - 与后端通信
 */
import axios from 'axios';
import type {
  ProjectState,
  StylePrompt,
  StyleCandidate,
  SelectedStyle,
  Slide,
  SlideCreate,
  SlideUpdate,
} from '../types';

const client = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

export const api = {
  // 获取项目状态
  getProject: async (): Promise<ProjectState> => {
    const { data } = await client.get<ProjectState>('/project');
    return data;
  },

  // 风格初始化
  initStyle: async (prompt: StylePrompt): Promise<StyleCandidate[]> => {
    const { data } = await client.post<StyleCandidate[]>('/style/init', prompt);
    return data;
  },

  // 选择风格
  selectStyle: async (selected: SelectedStyle): Promise<ProjectState> => {
    const { data } = await client.post<ProjectState>('/style/select', selected);
    return data;
  },

  // 创建幻灯片
  createSlide: async (slideData: SlideCreate): Promise<Slide> => {
    const { data } = await client.post<Slide>('/slides', slideData);
    return data;
  },

  // 更新幻灯片顺序
  reorderSlides: async (slideIds: string[]): Promise<ProjectState> => {
    const { data } = await client.put<ProjectState>('/slides/reorder', slideIds);
    return data;
  },

  // 更新幻灯片文本
  updateSlide: async (slideId: string, slideData: SlideUpdate): Promise<Slide> => {
    const { data } = await client.put<Slide>(`/slides/${slideId}`, slideData);
    return data;
  },

  // 重新生成图片
  regenerateImage: async (slideId: string): Promise<Slide> => {
    const { data } = await client.post<Slide>(`/slides/${slideId}/generate`);
    return data;
  },

  // 删除幻灯片
  deleteSlide: async (slideId: string): Promise<void> => {
    await client.delete(`/slides/${slideId}`);
  },
};
