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

export const useTranscriptStore = create<TranscriptState>((set) => ({
  audioLevel: 0,
  partialText: "",
  committedText: [],
  isRecording: false,
  setAudioLevel: (value) => set({ audioLevel: value }),
  setPartialText: (value) => set({ partialText: value }),
  addCommittedText: (value) =>
    set((state) => ({ committedText: [...state.committedText, value] })),
  setIsRecording: (value) => set({ isRecording: value }),
}));
