import "./globals.css";

export const metadata = {
  title: "Darukaa Biodiversity AI",
  description: "AI biodiversity intelligence chatbot — soil, land use and climate reasoning for India.",
};

// Fonts are loaded via a plain <link> rather than next/font so the build
// never depends on reaching fonts.googleapis.com — a slow/offline network
// just falls back to the system font stack in globals.css instead of
// failing the build.
export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <link
          rel="stylesheet"
          href="https://fonts.googleapis.com/css2?family=Fraunces:wght@500;600;700&family=Work+Sans:wght@400;500;600&display=swap"
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
