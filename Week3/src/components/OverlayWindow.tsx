interface OverlayWindowProps {
  isRecording: boolean;
}

export function OverlayWindow({ isRecording }: OverlayWindowProps) {
  if (!isRecording) {
    return null;
  }
  return <div className="overlay">Recording...</div>;
}
