export default function Header({ title, tagline }) {
  return (
    <header className="header">
      <div>
        <h1 className="title">{title}</h1>
        <p className="tagline">{tagline}</p>
      </div>
    </header>
  );
}
