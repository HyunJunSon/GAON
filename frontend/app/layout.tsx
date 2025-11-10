import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import Providers from "@/components/providers/Providers";
import AppNavigation from "@/components/navigation/AppNavigation";
import { UserInfoWrapper } from "@/components/user/UserInfoWrapper";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "GAON - 가족의온도",
  description: "가족과 함께하는 따뜻한 소통 플랫폼",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko">
      <body
        className={`min-h-dvh ${geistSans.variable} ${geistMono.variable} antialiased`}
        suppressHydrationWarning={true}
      >
        <div className="mx-auto flex max-w-screen-2xl relative">
          {/* 오른쪽 상단 사용자 정보 */}
          <div className="absolute top-4 right-4 z-50">
            <Providers>
              <UserInfoWrapper />
            </Providers>
          </div>
          
          <AppNavigation />
          <main className="min-h-dvh flex-1 p-4 md:p-6 pt-16 md:pt-6">
            {/* 전역 Provider로 모든 페이지 감싸기 */}
            <Providers>{children}</Providers>
          </main>
        </div>
        <div className="h-14 md:hidden"/>
      </body>
    </html>
  );
}
