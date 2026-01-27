interface WaveformVisualizerProps {
  level: number;
}

export function WaveformVisualizer({ level }: WaveformVisualizerProps) {
  const height = Math.max(10, Math.min(120, Math.round(level * 120)));
  return (
    <div className="waveform">
      <div className="waveform-bar" style={{ height }} />
      <div className="waveform-label">Level: {level.toExponential(3)}</div>
    </div>
  );
}
