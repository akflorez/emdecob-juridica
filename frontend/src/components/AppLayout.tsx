import { Outlet } from "react-router-dom";
import { AppSidebar } from "./AppSidebar";
import { Toaster } from "@/components/ui/toaster";

export function AppLayout() {
  return (
    <div className="flex min-h-dvh w-full bg-background">
      <AppSidebar />

      <main className="flex-1 overflow-auto">
        <div className="container mx-auto max-w-full px-2 py-6 md:px-4 md:py-8">
          <Outlet />
        </div>
      </main>

      <Toaster />
    </div>
  );
}
