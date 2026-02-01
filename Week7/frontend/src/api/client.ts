/**
 * API 客户端 - 与后端通信（支持多版本）
 */
import axios from 'axios';
import type {
  ProjectState,
  VersionInfo,
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
  // ============ 版本管理 ============
  
  // 列出所有版本
  listVersions: async (): Promise<VersionInfo[]> => {
    const { data } = await client.get<{ versions: VersionInfo[] }>('/versions');
    return data.versions;
  },

  // 获取版本信息
  getVersionInfo: async (version: number): Promise<VersionInfo> => {
    const { data } = await client.get<VersionInfo>(`/versions/${version}`);
    return data;
  },

  // 创建新版本
  createNewVersion: async (prompt?: StylePrompt): Promise<{ version: number; message: string }> => {
    const { data } = await client.post<{ version: number; message: string }>('/versions/create', prompt);
    return data;
  },

  // ============ 项目数据（需要版本）============
  
  // 获取项目状态
  getProject: async (version: number): Promise<ProjectState> => {
    const { data } = await client.get<ProjectState>('/project', {
      params: { version }
    });
    return data;
  },

  // ============ 风格管理 ============
  
  // 风格初始化
  initStyle: async (version: number, prompt: StylePrompt): Promise<StyleCandidate[]> => {
    const { data } = await client.post<StyleCandidate[]>('/style/init', prompt, {
      params: { version }
    });
    return data;
  },

  // 生成风格（别名，指向 initStyle）
  generateStyle: async (version: number, prompt: StylePrompt): Promise<StyleCandidate[]> => {
    return api.initStyle(version, prompt);
  },

  // 选择风格
  selectStyle: async (version: number, selected: SelectedStyle): Promise<ProjectState> => {
    const { data } = await client.post<ProjectState>('/style/select', selected, {
      params: { version }
    });
    return data;
  },

  // ============ 幻灯片管理 ============
  
  // 创建幻灯片
  createSlide: async (version: number, slideData: SlideCreate): Promise<Slide> => {
    const { data } = await client.post<Slide>('/slides', slideData, {
      params: { version }
    });
    return data;
  },

  // 更新幻灯片顺序
  reorderSlides: async (version: number, slideIds: string[]): Promise<ProjectState> => {
    const { data } = await client.put<ProjectState>('/slides/reorder', slideIds, {
      params: { version }
    });
    return data;
  },

  // 更新幻灯片文本
  updateSlide: async (version: number, slideId: string, slideData: SlideUpdate): Promise<Slide> => {
    const { data } = await client.put<Slide>(`/slides/${slideId}`, slideData, {
      params: { version }
    });
    return data;
  },

  // 重新生成图片
  regenerateImage: async (version: number, slideId: string): Promise<Slide> => {
    const { data } = await client.post<Slide>(`/slides/${slideId}/generate`, {}, {
      params: { version }
    });
    return data;
  },

  // 删除幻灯片
  deleteSlide: async (version: number, slideId: string): Promise<void> => {
    await client.delete(`/slides/${slideId}`, {
      params: { version }
    });
  },
};
