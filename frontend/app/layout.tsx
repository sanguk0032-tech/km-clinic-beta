import './globals.css';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: '일상 건강상태 트래킹',
  description: '자가 기록 기반 일상 트래킹 MVP',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <body>
        <main className="mx-auto min-h-screen w-full max-w-md p-4">{children}</main>
      </body>
    </html>
  );
}
