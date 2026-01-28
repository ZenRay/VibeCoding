interface OverlayWindowProps {
  isRecording: boolean;
  transcriptLine?: string;
}

export function OverlayWindow({ isRecording, transcriptLine }: OverlayWindowProps) {
  if (!isRecording) {
    return null;
  }
  return (
    <div className="overlay">
      <div className="overlay-title">Recording...</div>
      {transcriptLine && <div className="overlay-text">{transcriptLine}</div>}
    </div>
  );
}
