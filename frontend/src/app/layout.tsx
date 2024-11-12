import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Brooklyn College Computer Science Club AI Chatbot",
  description:
    "By the BC tech community, for the BC tech community. The Brooklyn College Computer Science Club AI Chatbot is a platform that enable students to search for opportunity, classes, and events with support of generative AI.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <div className="bg-white">{children}</div>
      </body>
    </html>
  );
}
