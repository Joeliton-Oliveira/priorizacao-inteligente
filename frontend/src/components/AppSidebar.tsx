"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarMenuSub,
  SidebarMenuSubButton,
  SidebarMenuSubItem,
  SidebarRail,
} from "@/components/ui/sidebar";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import {
  ChevronRight,
  FolderKanban,
  Grid3x3,
  LayoutGrid,
  ListFilter,
  Rows3,
  Settings,
  ListTodo,
  SquareKanban,
} from "lucide-react";
import { cn } from "@/lib/utils";

const activeNavClass =
  "bg-violet-500/15 text-violet-200 shadow-sm shadow-violet-950/20 ring-1 ring-violet-500/25 hover:bg-violet-500/20 hover:text-violet-100";

const activeSubNavClass =
  "bg-violet-500/15 text-violet-200 ring-1 ring-violet-500/25 hover:bg-violet-500/20 hover:text-violet-100 data-[active=true]:bg-violet-500/15 data-[active=true]:text-violet-200";

export function AppSidebar() {
  const pathname = usePathname();
  const isActivityMatricesActive = pathname === "/activities";
  const isEsteiraActive = pathname === "/kanban";
  const isKanbanListActive =
    pathname === "/kanban/list" || pathname.startsWith("/kanban/list/");
  const isFilasActive =
    pathname === "/priority-queue" || pathname.startsWith("/priority-queue/");
  const isKanbanGroupActive = isEsteiraActive || isKanbanListActive || isFilasActive;
  const isNewActivityActive = pathname === "/activities/new";
  const isProjectsActive = pathname === "/projects";
  const isSettingsActive = pathname === "/settings";

  return (
    <Sidebar
      collapsible="icon"
      side="left"
      className="border-r border-white/[0.06] bg-sidebar/90 backdrop-blur-xl"
    >
      <SidebarContent className="px-2 py-4">
        <SidebarGroup className="gap-4 px-1 py-2">
          <SidebarGroupContent>
            <SidebarMenu className="gap-2">
              <SidebarMenuItem>
                <SidebarMenuButton
                  asChild
                  isActive={!!isNewActivityActive}
                  tooltip="Cadastrar"
                  className={cn(isNewActivityActive && activeNavClass)}
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
                  tooltip="Atividades priorizadas"
                  className={cn(isActivityMatricesActive && activeNavClass)}
                >
                  <Link href="/activities">
                    <Grid3x3 className="size-4" />
                    <span>Atividades priorizadas</span>
                  </Link>
                </SidebarMenuButton>
              </SidebarMenuItem>

              <Collapsible asChild defaultOpen={isKanbanGroupActive} className="group/collapsible">
                <SidebarMenuItem>
                  <CollapsibleTrigger asChild>
                    <SidebarMenuButton
                      tooltip="Kanban"
                      isActive={isKanbanGroupActive}
                      className={cn(isKanbanGroupActive && activeNavClass)}
                    >
                      <LayoutGrid className="size-4" />
                      <span>Kanban</span>
                      <ChevronRight className="ml-auto size-4 transition-transform group-data-[state=open]/collapsible:rotate-90" />
                    </SidebarMenuButton>
                  </CollapsibleTrigger>
                  <CollapsibleContent className="mt-1.5">
                    <SidebarMenuSub>
                      <SidebarMenuSubItem>
                        <SidebarMenuSubButton
                          asChild
                          isActive={isEsteiraActive}
                          className={cn(isEsteiraActive && activeSubNavClass)}
                        >
                          <Link href="/kanban">
                            <SquareKanban className="size-4" />
                            <span>Esteira</span>
                          </Link>
                        </SidebarMenuSubButton>
                      </SidebarMenuSubItem>
                      <SidebarMenuSubItem>
                        <SidebarMenuSubButton
                          asChild
                          isActive={isKanbanListActive}
                          className={cn(isKanbanListActive && activeSubNavClass)}
                        >
                          <Link href="/kanban/list">
                            <Rows3 className="size-4" />
                            <span>Lista</span>
                          </Link>
                        </SidebarMenuSubButton>
                      </SidebarMenuSubItem>
                      <SidebarMenuSubItem>
                        <SidebarMenuSubButton
                          asChild
                          isActive={isFilasActive}
                          className={cn(isFilasActive && activeSubNavClass)}
                        >
                          <Link href="/priority-queue">
                            <ListFilter className="size-4" />
                            <span>Fila</span>
                          </Link>
                        </SidebarMenuSubButton>
                      </SidebarMenuSubItem>
                    </SidebarMenuSub>
                  </CollapsibleContent>
                </SidebarMenuItem>
              </Collapsible>

              <SidebarMenuItem>
                <SidebarMenuButton
                  asChild
                  isActive={!!isProjectsActive}
                  tooltip="Projetos"
                  className={cn(isProjectsActive && activeNavClass)}
                >
                  <Link href="/projects">
                    <FolderKanban className="size-4" />
                    <span>Projetos</span>
                  </Link>
                </SidebarMenuButton>
              </SidebarMenuItem>
              <SidebarMenuItem>
                <SidebarMenuButton
                  asChild
                  isActive={!!isSettingsActive}
                  tooltip="Calibragem"
                  className={cn(isSettingsActive && activeNavClass)}
                >
                  <Link href="/settings">
                    <Settings className="size-4" />
                    <span>Calibragem</span>
                  </Link>
                </SidebarMenuButton>
              </SidebarMenuItem>

            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
      <SidebarRail />
    </Sidebar>
  );
}
