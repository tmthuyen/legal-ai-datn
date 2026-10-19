'use client';

import { NavSectionData, NAV_SECTIONS as dataBar } from '@/components/sidebar/nav-data';
import {
  SidebarGroup,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from '@/components/ui/sidebar';
import { useAuthStore } from '@/stores/auth.store';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

function isActivePath(pathname: string, url: string) {
  if (url === '/') return pathname === '/';
  return pathname === url || pathname.startsWith(`${url}/`);
}

function NavSection({ groupLabel, items }: NavSectionData) {
  const pathname = usePathname();

  return (
    <SidebarGroup>
      <SidebarGroupLabel>{groupLabel}</SidebarGroupLabel>
      <SidebarMenu>
        {items.map((item) => {
          const active = isActivePath(pathname, item.url);
          return (
            <SidebarMenuItem key={item.title}>
              <SidebarMenuButton
                asChild
                className={`${
                  active ? 'bg-accent text-accent-foreground dark:bg-accent/40' : ''
                } hover:bg-accent/70 dark:hover:bg-accent/40 hover:text-accent-foreground cursor-pointer transition-transform hover:scale-105`}
              >
                <Link href={item.url}>
                  <item.icon />
                  <span>{item.title}</span>
                </Link>
              </SidebarMenuButton>
            </SidebarMenuItem>
          );
        })}
      </SidebarMenu>
    </SidebarGroup>
  );
}

export function UserNavMain() {
  const user = useAuthStore((state) => state.user);

  return (
    <div>
      <NavSection groupLabel={dataBar.user.groupLabel} items={dataBar.user.items} />
      {user && (
        <NavSection groupLabel={dataBar.personal.groupLabel} items={dataBar.personal.items} />
      )}
      {user && (
        <NavSection groupLabel={dataBar.settings.groupLabel} items={dataBar.settings.items} />
      )}
    </div>
  );
}

export function NavMain() {
  return (
    <div>
      <NavSection groupLabel={dataBar.learning.groupLabel} items={dataBar.learning.items} />
      <NavSection groupLabel={dataBar.auth.groupLabel} items={dataBar.auth.items} />
      <NavSection groupLabel={dataBar.admin.groupLabel} items={dataBar.admin.items} />
      <NavSection groupLabel={dataBar.interaction.groupLabel} items={dataBar.interaction.items} />
      <NavSection groupLabel={dataBar.settings.groupLabel} items={dataBar.settings.items} />
    </div>
  );
}
