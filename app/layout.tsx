import type { Metadata } from 'next';
import './globals.css';
import '../public/fonts.css';
import 'lenis/dist/lenis.css';
import './design.css';
import './landing.css';
export const metadata: Metadata = { title: 'HomeAtlas — Your home. On the record.', description: 'Private home records, answers with exact citations, and the details worth keeping. Manuals, warranties and maintenance in one place.' };
export default function RootLayout({children}:{children:React.ReactNode}) { return <html lang="en"><head><link rel="preload" href="/fonts/Satoshi-Regular.woff2" as="font" type="font/woff2" crossOrigin="anonymous"/><link rel="preload" href="/fonts/Satoshi-Medium.woff2" as="font" type="font/woff2" crossOrigin="anonymous"/></head><body><a href="#main-content" className="skip-link">Skip to content</a>{children}</body></html> }
