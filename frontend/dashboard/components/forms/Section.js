export default function Section({ name, id, children }) {
  return (
    <div style={{ paddingTop: "1.5em", paddingBottom: "1.5em" }}>
      <h2 id={id || name} style={{ scrollMarginTop: "3em" }}>
        {name}
      </h2>
      {children}
    </div>
  );
}
