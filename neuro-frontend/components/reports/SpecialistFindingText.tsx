export function SpecialistFindingText({ statement }: { statement: string }) {
  const paragraphs = statement.replace(/\r\n/g, "\n").split(/\n[ \t]*\n/).filter((text) => text.trim());
  return <div className="space-y-3">{paragraphs.map((text, index) => <p key={index}>{text}</p>)}</div>;
}
