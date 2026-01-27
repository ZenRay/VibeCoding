import { create } from "zustand";

interface TranscriptState {
  audioLevel: number;
  partialText: string;
  committedText: string[];
  isRecording: boolean;
  setAudioLevel: (value: number) => void;
  setPartialText: (value: string) => void;
  addCommittedText: (value: string) => void;
  setIsRecording: (value: boolean) => void;
}

const normalize = (value: string) => value.trim().replace(/\s+/g, " ");

export const useTranscriptStore = create<TranscriptState>((set) => ({
  audioLevel: 0,
  partialText: "",
  committedText: [],
  isRecording: false,
  setAudioLevel: (value) => set({ audioLevel: value }),
  setPartialText: (value) => set({ partialText: value }),
  addCommittedText: (value) =>
    set((state) => {
      const next = normalize(value);
      if (!next) {
        return state;
      }
      const last = state.committedText[state.committedText.length - 1];
      if (last && normalize(last) === next) {
        return state;
      }
      return { committedText: [...state.committedText, next] };
    }),
  setIsRecording: (value) => set({ isRecording: value }),
}));
