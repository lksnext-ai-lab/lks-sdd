import type { Metadata } from 'next';
import './styles.css';

export const metadata: Metadata = {
  title: 'LKS-SDD Next.js SSR',
  description: 'Perfil SSR reproducible',
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}
