import { NavLink as RouterNavLink } from 'react-router-dom';
import { cn } from '@/lib/utils';
import { LucideIcon } from 'lucide-react';

interface SidebarNavLinkProps {
  to: string;
  icon: LucideIcon;
  children: React.ReactNode;
  collapsed?: boolean;
  title?: string;
}

export function SidebarNavLink({ to, icon: Icon, children, collapsed, title }: SidebarNavLinkProps) {
  return (
    <RouterNavLink
      to={to}
      className={({ isActive }) =>
        cn(
          'flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all duration-200',
          'hover:bg-sidebar-accent hover:text-sidebar-accent-foreground',
          isActive
            ? 'bg-primary/10 text-primary border-l-2 border-primary'
            : 'text-sidebar-foreground'
        )
      }
    >
      <Icon className="h-5 w-5 flex-shrink-0" />
      <span>{children}</span>
    </RouterNavLink>
  );
}
