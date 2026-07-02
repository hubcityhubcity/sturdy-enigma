import './globals.css';
import type { ReactNode } from 'react';

export const metadata = {
  title: 'BPC Clipper',
  description: 'AI producer workspace for short-form podcast clips',
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
