export const metadata = {
  title: "Darukaa Biodiversity AI",
  description: "AI biodiversity intelligence chatbot",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
