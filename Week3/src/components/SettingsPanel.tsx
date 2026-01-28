import { useState } from "react";

export interface SettingsValue {
  apiKey: string;
  language: string;
  hotkey: string;
  proxyUrl: string;
}

interface SettingsPanelProps {
  value: SettingsValue;
  onSave: (value: SettingsValue) => void;
}

export function SettingsPanel({ value, onSave }: SettingsPanelProps) {
  const [apiKey, setApiKey] = useState(value.apiKey);
  const [language, setLanguage] = useState(value.language);
  const [hotkey, setHotkey] = useState(value.hotkey);
  const [proxyUrl, setProxyUrl] = useState(value.proxyUrl);

  return (
    <section className="settings">
      <h2>Settings</h2>
      <label>
        API Key
        <input
          value={apiKey}
          onChange={(event) => setApiKey(event.target.value)}
          placeholder="sk-..."
        />
      </label>
      <label>
        Language
        <select value={language} onChange={(event) => setLanguage(event.target.value)}>
          <option value="auto">Auto</option>
          <option value="en">English</option>
          <option value="zh">Chinese</option>
        </select>
      </label>
      <label>
        Hotkey
        <input
          value={hotkey}
          onChange={(event) => setHotkey(event.target.value)}
        />
      </label>
      <label>
        Proxy (optional)
        <input
          value={proxyUrl}
          onChange={(event) => setProxyUrl(event.target.value)}
          placeholder="socks5://127.0.0.1:7890"
        />
      </label>
      <button
        type="button"
        onClick={() => onSave({ apiKey, language, hotkey, proxyUrl })}
      >
        Save
      </button>
    </section>
  );
}
