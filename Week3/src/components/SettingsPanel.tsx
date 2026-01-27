import { useState } from "react";

export interface SettingsValue {
  apiKey: string;
  language: string;
  hotkey: string;
}

interface SettingsPanelProps {
  value: SettingsValue;
  onSave: (value: SettingsValue) => void;
}

export function SettingsPanel({ value, onSave }: SettingsPanelProps) {
  const [apiKey, setApiKey] = useState(value.apiKey);
  const [language, setLanguage] = useState(value.language);
  const [hotkey, setHotkey] = useState(value.hotkey);

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
      <button
        type="button"
        onClick={() => onSave({ apiKey, language, hotkey })}
      >
        Save
      </button>
    </section>
  );
}
