"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarMenuSub,
  SidebarMenuSubButton,
  SidebarMenuSubItem,
  SidebarRail,
} from "@/components/ui/sidebar";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import {
  ChevronRight,
  ClipboardList,
  FolderKanban,
  Grid3x3,
  LayoutGrid,
  ListFilter,
  Settings,
  ListTodo,
} from "lucide-react";

export function AppSidebar() {
  const pathname = usePathname();
  const isActivityMatricesActive = pathname === "/activities";
  const isKanbanActive = pathname === "/kanban";
  const isNewActivityActive = pathname === "/activities/new";
  const isProjectsActive = pathname === "/projects";
  const isFilasBugActive = pathname === "/priority-queue/bug";
  const isFilasFeatureActive = pathname === "/priority-queue/feature";
  const isFilasActive = isFilasBugActive || isFilasFeatureActive;
  const isSettingsActive = pathname === "/settings";

  return (
    <Sidebar collapsible="icon" side="left">
      <SidebarHeader className="px-3 py-3">
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton asChild size="lg">
              <Link href="/activities/new" className="flex items-center gap-3">
                <div className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-primary text-primary-foreground">
                  <ClipboardList className="size-5 shrink-0" />
                </div>
                <span className="truncate text-sm font-semibold group-data-[collapsible=icon]:hidden">
                  Estruturação de Requisitos
                </span>
              </Link>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>

      <SidebarContent className="px-2 pb-3">
        <SidebarGroup className="gap-4 px-1 py-2">
          <SidebarGroupLabel>Navegação</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu className="gap-2">
              <SidebarMenuItem>
                <SidebarMenuButton
                  asChild
                  isActive={!!isNewActivityActive}
                  tooltip="Cadastrar"
                >
                  <Link href="/activities/new">
                    <ListTodo className="size-4" />
                    <span>Cadastrar</span>
                  </Link>
                </SidebarMenuButton>
              </SidebarMenuItem>
              <SidebarMenuItem>
                <SidebarMenuButton
                  asChild
                  isActive={!!isActivityMatricesActive}
                  tooltip="Matrizes de Atividades"
                >
                  <Link href="/activities">
                    <Grid3x3 className="size-4" />
                    <span>Matrizes de Atividades</span>
                  </Link>
                </SidebarMenuButton>
              </SidebarMenuItem>
              <SidebarMenuItem>
                <SidebarMenuButton
                  asChild
                  isActive={!!isKanbanActive}
                  tooltip="Kanban"
                >
                  <Link href="/kanban">
                    <LayoutGrid className="size-4" />
                    <span>Kanban</span>
                  </Link>
                </SidebarMenuButton>
              </SidebarMenuItem>
              <SidebarMenuItem>
                <SidebarMenuButton asChild isActive={!!isProjectsActive} tooltip="Projetos">
                  <Link href="/projects">
                    <FolderKanban className="size-4" />
                    <span>Projetos</span>
                  </Link>
                </SidebarMenuButton>
              </SidebarMenuItem>
              <SidebarMenuItem>
                <Collapsible defaultOpen={isFilasActive} className="group/filas">
                  <CollapsibleTrigger asChild>
                    <SidebarMenuButton isActive={isFilasActive} tooltip="Filas">
                      <ListFilter className="size-4" />
                      <span>Filas</span>
                      <ChevronRight className="ml-auto size-4 transition-transform group-data-[state=open]/filas:rotate-90" />
                    </SidebarMenuButton>
                  </CollapsibleTrigger>
                  <CollapsibleContent>
                    <SidebarMenuSub>
                      <SidebarMenuSubItem>
                        <SidebarMenuSubButton asChild isActive={!!isFilasBugActive}>
                          <Link href="/priority-queue/bug">Bug</Link>
                        </SidebarMenuSubButton>
                      </SidebarMenuSubItem>
                      <SidebarMenuSubItem>
                        <SidebarMenuSubButton asChild isActive={!!isFilasFeatureActive}>
                          <Link href="/priority-queue/feature">Feature</Link>
                        </SidebarMenuSubButton>
                      </SidebarMenuSubItem>
                    </SidebarMenuSub>
                  </CollapsibleContent>
                </Collapsible>
              </SidebarMenuItem>
              <SidebarMenuItem>
                <SidebarMenuButton
                  asChild
                  isActive={!!isSettingsActive}
                  tooltip="Configurações"
                >
                  <Link href="/settings">
                    <Settings className="size-4" />
                    <span>Configurações</span>
                  </Link>
                </SidebarMenuButton>
              </SidebarMenuItem>

            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
      <SidebarFooter className="px-3 pb-3 pt-2" />

      <SidebarRail />
    </Sidebar>
  );
}
