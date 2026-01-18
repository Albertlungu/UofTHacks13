import "./globals.css";

export const metadata = {
  title: "Identity Console",
  description: "Minimal interface for identity and camera endpoints.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-background text-foreground antialiased">
        {children}
      </body>
    </html>
  );
}
