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
  style_reference: string | null;
  slides: Slide[];
}

export interface StylePrompt {
  description: string;
}

export interface StyleCandidate {
  image_path: string;
}

export interface SelectedStyle {
  image_path: string;
}

export interface SlideCreate {
  text: string;
}

export interface SlideUpdate {
  text: string;
}
