import { useEffect } from "react";
import { listen } from "@tauri-apps/api/event";
import { isTauri as isTauriApi } from "@tauri-apps/api/core";
import { useTranscriptStore } from "../stores/transcriptStore";

export function useTauriEvents(onRecordingChange: (value: boolean) => void) {
  const setAudioLevel = useTranscriptStore((state) => state.setAudioLevel);
  const setPartialText = useTranscriptStore((state) => state.setPartialText);
  const addCommittedText = useTranscriptStore((state) => state.addCommittedText);
  useEffect(() => {
    let cleanups: Array<() => void> = [];
    const result = isTauriApi();
    const resolved = typeof result === "boolean" ? Promise.resolve(result) : result;
    resolved.then((value) => {
      if (!value) {
        return;
      }
      const unlistenPromise = listen<{ is_recording: boolean }>(
        "recording_state_changed",
        (event) => {
          onRecordingChange(event.payload.is_recording);
        }
      );
      const unlistenAudioPromise = listen<{ level: number }>(
        "audio_level_update",
        (event) => {
          setAudioLevel(event.payload.level);
        }
      );
      const unlistenPartialPromise = listen<{ text: string }>(
        "partial_transcript",
        (event) => {
          setPartialText(event.payload.text);
        }
      );
      const unlistenCommittedPromise = listen<{ text: string }>(
        "committed_transcript",
        (event) => {
          addCommittedText(event.payload.text);
        }
      );
      cleanups = [
        () => unlistenPromise.then((unlisten) => unlisten()),
        () => unlistenAudioPromise.then((unlisten) => unlisten()),
        () => unlistenPartialPromise.then((unlisten) => unlisten()),
        () => unlistenCommittedPromise.then((unlisten) => unlisten()),
      ];
    });

    return () => {
      cleanups.forEach((fn) => fn());
    };
  }, [onRecordingChange, setAudioLevel, setPartialText, addCommittedText]);
}
