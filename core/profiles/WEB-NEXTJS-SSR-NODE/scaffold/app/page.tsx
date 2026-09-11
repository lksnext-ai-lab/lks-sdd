import Counter from './ui/counter';

export default function Home() {
  const renderedAt = new Date().toISOString();
  return (
    <main>
      <p className="eyebrow">LKS-SDD · perfil de referencia SSR</p>
      <h1>Next.js listo para especificar</h1>
      <p data-testid="server-rendered">
        Documento renderizado por el servidor en <time>{renderedAt}</time>.
      </p>
      <Counter />
    </main>
  );
}
