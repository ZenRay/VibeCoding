import { useEffect } from "react";
import { listen } from "@tauri-apps/api/event";
import { isTauri as isTauriApi } from "@tauri-apps/api/core";
import { useTranscriptStore } from "../stores/transcriptStore";

export function useTauriEvents(onRecordingChange: (value: boolean) => void) {
  const setAudioLevel = useTranscriptStore((state) => state.setAudioLevel);
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
      cleanups = [
        () => unlistenPromise.then((unlisten) => unlisten()),
        () => unlistenAudioPromise.then((unlisten) => unlisten()),
      ];
    });

    return () => {
      cleanups.forEach((fn) => fn());
    };
  }, [onRecordingChange, setAudioLevel]);
}
