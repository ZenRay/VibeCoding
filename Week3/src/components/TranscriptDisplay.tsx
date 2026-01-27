interface TranscriptDisplayProps {
  partialText: string;
  committedText: string[];
}

export function TranscriptDisplay({
  partialText,
  committedText,
}: TranscriptDisplayProps) {
  const normalizedPartial = partialText.trim().replace(/\s+/g, " ");
  const recent = committedText.slice(-3);
  const padded =
    recent.length < 3
      ? Array(3 - recent.length).fill("").concat(recent)
      : recent;
  const lastCommitted = recent[recent.length - 1] ?? "";
  const normalizedLast = lastCommitted.trim().replace(/\s+/g, " ");
  const showPartial =
    normalizedPartial.length > 0 && normalizedPartial !== normalizedLast;
  return (
    <section className="transcript">
      <h2>Transcript</h2>
      {padded.map((line, index) => (
        <p key={`${line}-${index}`} className="transcript-line">
          {line}
        </p>
      ))}
      <p className="transcript-partial">{showPartial ? partialText : ""}</p>
    </section>
  );
}
