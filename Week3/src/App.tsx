import { useCallback, useEffect, useState } from "react";
import { invoke, isTauri as isTauriApi } from "@tauri-apps/api/core";
import { listen } from "@tauri-apps/api/event";
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
  const [hotkeyNotice, setHotkeyNotice] = useState<string | null>(null);
  const [permissionNotice, setPermissionNotice] = useState<string | null>(null);
  const [statusNotice, setStatusNotice] = useState<string | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<string | null>(null);
  const [overlayVisible, setOverlayVisible] = useState(false);
  const [showAbout, setShowAbout] = useState(false);
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
    if (isRecording) {
      setOverlayVisible(true);
      return;
    }
    if (!latestCommitted && !partialText) {
      setOverlayVisible(false);
      return;
    }
    const timer = setTimeout(() => {
      setOverlayVisible(false);
    }, 500);
    return () => clearTimeout(timer);
  }, [isRecording, latestCommitted, partialText]);

  useEffect(() => {
    const result = isTauriApi();
    const resolved = typeof result === "boolean" ? Promise.resolve(result) : result;
    let cleanups: Array<() => void> = [];
    resolved.then((value) => {
      setIsTauriEnv(value);
      if (!value) {
        return;
      }
      listen("open_settings", () => {
        setShowSettings(true);
      })
        .then((stop) => cleanups.push(stop))
        .catch(() => {});
      listen("open_about", () => {
        setShowAbout(true);
      })
        .then((stop) => cleanups.push(stop))
        .catch(() => {});
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
      invoke("check_permissions_cmd").catch(() => {});
      invoke<{ supported: boolean; reason?: string }>("get_hotkey_status_cmd")
        .then((status) => {
          if (status.supported) {
            setHotkeyNotice(null);
          } else {
            setHotkeyNotice(status.reason ?? "Hotkey unavailable");
          }
        })
        .catch(() => {});
      listen<{ supported: boolean; reason?: string }>("hotkey_status", (event) => {
        if (event.payload.supported) {
          setHotkeyNotice(null);
        } else {
          setHotkeyNotice(event.payload.reason ?? "Hotkey unavailable");
        }
      }).then((stop) => {
        cleanups.push(stop);
      });
      listen<{ microphone: string; accessibility: string }>("permission_status", (event) => {
        const { microphone, accessibility } = event.payload;
        if (microphone === "denied") {
          setPermissionNotice("Microphone permission denied");
          return;
        }
        if (accessibility === "denied") {
          setPermissionNotice("Accessibility permission denied");
          return;
        }
        setPermissionNotice(null);
      }).then((stop) => {
        cleanups.push(stop);
      });
      listen<{ message: string }>("notification", (event) => {
        setStatusNotice(event.payload.message);
      }).then((stop) => {
        cleanups.push(stop);
      });
      listen<{ message: string }>("error", (event) => {
        setStatusNotice(event.payload.message);
      }).then((stop) => {
        cleanups.push(stop);
      });
      listen<{ state: string; attempt?: number }>("connection_status", (event) => {
        const { state, attempt } = event.payload;
        if (attempt) {
          setConnectionStatus(`${state} (${attempt})`);
        } else {
          setConnectionStatus(state);
        }
      }).then((stop) => {
        cleanups.push(stop);
      });
    });
    return () => {
      cleanups.forEach((stop) => stop());
    };
  }, []);

  useEffect(() => {
    if (!statusNotice) {
      return;
    }
    const timer = setTimeout(() => {
      setStatusNotice(null);
    }, 3000);
    return () => clearTimeout(timer);
  }, [statusNotice]);
  return (
    <main className="app">
      <h1>ScribeFlow</h1>
      <div className="overlay-slot">
        <OverlayWindow isRecording={overlayVisible} transcriptLine={overlayText} />
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
        <button
          type="button"
          onClick={() => {
            if (!isTauriEnv) {
              return;
            }
            invoke("copy_last_transcript_cmd").catch((error) => {
              setStatusNotice(String(error));
            });
          }}
          disabled={!isTauriEnv}
        >
          Copy
        </button>
        <button type="button" onClick={() => setShowSettings((v) => !v)}>
          {showSettings ? "Hide Settings" : "Show Settings"}
        </button>
      </div>
      {hotkeyNotice && (
        <p className="hotkey-notice">
          Hotkey unavailable: {hotkeyNotice}. Use the Start button instead.
        </p>
      )}
      {connectionStatus && (
        <p className="connection-status">Connection: {connectionStatus}</p>
      )}
      {permissionNotice && <p className="permission-notice">{permissionNotice}</p>}
      {statusNotice && <p className="status-notice">{statusNotice}</p>}
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
      {showAbout && (
        <div className="modal-backdrop" onClick={() => setShowAbout(false)}>
          <div className="modal" onClick={(event) => event.stopPropagation()}>
            <section className="about">
              <h2>About</h2>
              <p>ScribeFlow v0.1.0</p>
              <p>Real-time dictation with ElevenLabs Scribe v2.</p>
              <button type="button" onClick={() => setShowAbout(false)}>
                Close
              </button>
            </section>
          </div>
        </div>
      )}
    </main>
  );
}
