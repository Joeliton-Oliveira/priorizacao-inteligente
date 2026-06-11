import type { ReactNode } from "react";
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/AppSidebar";
import { Separator } from "@/components/ui/separator";
import { Toaster } from "@/components/ui/sonner";

type PrivateLayoutProps = {
  children: ReactNode;
};

export function PrivateLayout({ children }: PrivateLayoutProps) {
  return (
    <SidebarProvider className="h-svh overflow-hidden">
      <Toaster richColors closeButton position="top-right" />
      <AppSidebar />
      <SidebarInset className="min-h-0 overflow-hidden">
        <header className="z-50 flex h-14 shrink-0 items-center gap-2 border-b border-white/[0.06] bg-background/80 px-4 backdrop-blur-md">
          <SidebarTrigger className="shrink-0 rounded-lg hover:bg-white/[0.06]" />
          <Separator orientation="vertical" className="h-6" />
        </header>
        <main className="flex min-h-0 flex-1 flex-col overflow-y-auto bg-gradient-to-br from-background via-background to-[oklch(0.14_0.02_280)] p-4 sm:p-6">
          {children}
        </main>
      </SidebarInset>
    </SidebarProvider>
  );
}
