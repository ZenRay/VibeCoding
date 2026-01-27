import { useCallback, useEffect, useState } from "react";
import { invoke, isTauri as isTauriApi } from "@tauri-apps/api/core";
import { OverlayWindow } from "./components/OverlayWindow";
import { SettingsPanel, SettingsValue } from "./components/SettingsPanel";
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
    proxyUrl: "",
  });
  const isRecording = useTranscriptStore((state) => state.isRecording);
  const audioLevel = useTranscriptStore((state) => state.audioLevel);
  const partialText = useTranscriptStore((state) => state.partialText);
  const committedText = useTranscriptStore((state) => state.committedText);
  const latestCommitted = committedText[committedText.length - 1] ?? "";
  const overlayText = partialText || latestCommitted;
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
        proxy_url: string | null;
      }>("get_config_cmd")
        .then((config) => {
          setSettings({
            apiKey: config.api_key ?? "",
            language: config.language,
            hotkey: config.hotkey,
            proxyUrl: config.proxy_url ?? "",
          });
        })
        .catch(() => {});
      invoke("check_connectivity_cmd").catch(() => {});
    });
  }, []);
  return (
    <main className="app">
      <h1>ScribeFlow</h1>
      <div className="overlay-slot">
        <OverlayWindow isRecording={isRecording} transcriptLine={overlayText} />
      </div>
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
                      proxy_url: value.proxyUrl || null,
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
