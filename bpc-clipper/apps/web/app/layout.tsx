import './globals.css';
import type { ReactNode } from 'react';

export const metadata = {
  title: 'Titan Clipper AI',
  description: 'The AI production system for high-retention short-form content. Built first for Black Podcast Clips.',
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <main className="app-shell">{children}</main>
      </body>
    </html>
  );
}
