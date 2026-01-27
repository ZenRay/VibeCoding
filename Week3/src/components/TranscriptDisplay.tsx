interface TranscriptDisplayProps {
  partialText: string;
  committedText: string[];
}

export function TranscriptDisplay({
  partialText,
  committedText,
}: TranscriptDisplayProps) {
  return (
    <section className="transcript">
      <h2>Transcript</h2>
      {committedText.map((line, index) => (
        <p key={`${line}-${index}`} className="transcript-line">
          {line}
        </p>
      ))}
      {partialText && <p className="transcript-partial">{partialText}</p>}
    </section>
  );
}
