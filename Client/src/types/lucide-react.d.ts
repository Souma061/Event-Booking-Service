declare module 'lucide-react' {
  import { FC, SVGProps } from 'react';
  export interface LucideProps extends SVGProps<SVGSVGElement> {
    size?: number | string;
    strokeWidth?: number | string;
    absoluteStrokeWidth?: boolean;
    color?: string;
  }
  export type LucideIcon = FC<LucideProps>;

  // All icons used in this project
  export const ArrowRight: LucideIcon;
  export const ArrowLeft: LucideIcon;
  export const Calendar: LucideIcon;
  export const CheckCircle: LucideIcon;
  export const ChevronDown: LucideIcon;
  export const ChevronRight: LucideIcon;
  export const ChevronUp: LucideIcon;
  export const Clock: LucideIcon;
  export const Eye: LucideIcon;
  export const EyeOff: LucideIcon;
  export const Filter: LucideIcon;
  export const Github: LucideIcon;
  export const Home: LucideIcon;
  export const Instagram: LucideIcon;
  export const LayoutDashboard: LucideIcon;
  export const Lock: LucideIcon;
  export const LogOut: LucideIcon;
  export const Mail: LucideIcon;
  export const MapPin: LucideIcon;
  export const Menu: LucideIcon;
  export const Mic: LucideIcon;
  export const Minus: LucideIcon;
  export const Music: LucideIcon;
  export const Phone: LucideIcon;
  export const Plus: LucideIcon;
  export const RefreshCw: LucideIcon;
  export const Search: LucideIcon;
  export const Shield: LucideIcon;
  export const ShoppingBag: LucideIcon;
  export const ShoppingCart: LucideIcon;
  export const SlidersHorizontal: LucideIcon;
  export const Star: LucideIcon;
  export const Tag: LucideIcon;
  export const Ticket: LucideIcon;
  export const Trash2: LucideIcon;
  export const Trophy: LucideIcon;
  export const Twitter: LucideIcon;
  export const User: LucideIcon;
  export const Users: LucideIcon;
  export const X: LucideIcon;
  export const Zap: LucideIcon;
  export const AlertCircle: LucideIcon;
}
