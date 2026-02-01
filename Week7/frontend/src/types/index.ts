/**
 * 前端类型定义 - 与后端 Pydantic 模型对应
 */

export interface Slide {
  id: string;
  text: string;
  image_path: string | null;
  content_hash: string;
  image_hash: string | null;
}

export interface ProjectState {
  version: number | null;  // 新增：版本号
  created_at: string | null;  // 新增：创建时间
  project_name: string | null;  // 新增：项目名称
  style_reference: string | null;
  style_prompt: string | null;
  slides: Slide[];
}

export interface VersionInfo {
  version: number;
  created_at: string | null;
  project_name: string | null;
  style_reference: string | null;
  style_prompt: string | null;
  slide_count: number;
}

export interface StylePrompt {
  description: string;
}

export interface StyleCandidate {
  image_path: string;
}

export interface SelectedStyle {
  image_path: string;
  style_prompt?: string;
}

export interface SlideCreate {
  text: string;
}

export interface SlideUpdate {
  text?: string;
  image_path?: string;
}
