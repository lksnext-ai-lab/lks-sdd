import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';

const inter = Inter({
  variable: '--font-inter',
  subsets: ['latin'],
  display: 'swap',
});

export const metadata: Metadata = {
  title: 'Desarrollo SDD con CODEX · LKS Next',
  description:
    'Conoce LKS-SDD, el plugin Spec-anchored de LKS Next para desarrollar con Codex mediante especificaciones vivas, trazabilidad y evidencia.',
  openGraph: {
    title: 'Desarrollo SDD con CODEX · LKS Next',
    description:
      'Un plugin de LKS Next para CODEX que convierte las especificaciones en un contrato vivo.',
    images: ['/og.png'],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Desarrollo SDD con CODEX · LKS Next',
    description:
      'Un plugin de LKS Next para CODEX que convierte las especificaciones en un contrato vivo.',
    images: ['/og.png'],
  },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="es">
      <body className={`${inter.variable}`}>{children}</body>
    </html>
  );
}
