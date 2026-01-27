import { useCallback, useEffect, useState } from "react";
import { invoke, isTauri as isTauriApi } from "@tauri-apps/api/core";
import { OverlayWindow } from "./components/OverlayWindow";
import { SettingsPanel, SettingsValue } from "./components/SettingsPanel";
import { TranscriptDisplay } from "./components/TranscriptDisplay";
import { WaveformVisualizer } from "./components/WaveformVisualizer";
import { useTauriEvents } from "./hooks/useTauriEvents";
import { useTranscriptStore } from "./stores/transcriptStore";

export default function App() {
  const [showSettings, setShowSettings] = useState(false);
  const [isTauriEnv, setIsTauriEnv] = useState(true);
  const [isStarting, setIsStarting] = useState(false);
  const [settings, setSettings] = useState<SettingsValue>({
    apiKey: "",
    language: "auto",
    hotkey: "Cmd+Shift+\\",
  });
  const isRecording = useTranscriptStore((state) => state.isRecording);
  const audioLevel = useTranscriptStore((state) => state.audioLevel);
  const partialText = useTranscriptStore((state) => state.partialText);
  const committedText = useTranscriptStore((state) => state.committedText);
  const setRecording = useTranscriptStore((state) => state.setIsRecording);
  const handleRecording = useCallback(
    (value: boolean) => {
      setRecording(value);
    },
    [setRecording]
  );
  useTauriEvents(handleRecording);

  useEffect(() => {
    const result = isTauriApi();
    const resolved = typeof result === "boolean" ? Promise.resolve(result) : result;
    resolved.then((value) => {
      setIsTauriEnv(value);
      if (!value) {
        return;
      }
      invoke<{
        api_key: string | null;
        language: string;
        hotkey: string;
      }>("get_config_cmd")
        .then((config) => {
          setSettings({
            apiKey: config.api_key ?? "",
            language: config.language,
            hotkey: config.hotkey,
          });
        })
        .catch(() => {});
    });
  }, []);
  return (
    <main className="app">
      <h1>ScribeFlow</h1>
      <OverlayWindow isRecording={isRecording} />
      <div className="controls">
        <button
          type="button"
          onClick={async () => {
            if (!isTauriEnv || isStarting) {
              return;
            }
            setIsStarting(true);
            try {
              if (isRecording) {
                await invoke("stop_transcription");
                setRecording(false);
              } else {
                await invoke("start_transcription");
                setRecording(true);
              }
            } catch (error) {
              alert(String(error));
            } finally {
              setIsStarting(false);
            }
          }}
          disabled={!isTauriEnv || isStarting}
        >
          {isRecording ? "Stop" : isStarting ? "Starting..." : "Start"}
        </button>
        <button type="button" onClick={() => setShowSettings((v) => !v)}>
          {showSettings ? "Hide Settings" : "Show Settings"}
        </button>
      </div>
      <WaveformVisualizer level={audioLevel} />
      <TranscriptDisplay partialText={partialText} committedText={committedText} />
      {showSettings && (
        <div className="modal-backdrop" onClick={() => setShowSettings(false)}>
          <div className="modal" onClick={(event) => event.stopPropagation()}>
            <SettingsPanel
              value={settings}
              onSave={(value) => {
                setSettings(value);
                if (isTauriEnv) {
                  invoke("save_config_cmd", {
                    config: {
                      api_key: value.apiKey || null,
                      language: value.language,
                      hotkey: value.hotkey,
                    },
                  }).catch(() => {});
                }
                setShowSettings(false);
              }}
            />
          </div>
        </div>
      )}
    </main>
  );
}
