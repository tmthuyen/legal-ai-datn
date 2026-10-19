import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { useAuthStore } from '@/stores/auth.store';
import {
  ChevronDown,
  KeyRound,
  LogOut,
  MailQuestion,
  Settings,
  ShieldUser,
  UserIcon,
} from 'lucide-react';
import { useRouter } from 'next/navigation';

export default function UserDropdown() {
  const user = useAuthStore((state) => state.user);
  const router = useRouter();

  const handleLogout = () => {
    useAuthStore.getState().logout();
    router.push('/auth/login');
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button
          className={`focus:ring-primary flex cursor-pointer items-center gap-2 rounded-full p-1 pr-2 transition-colors hover:bg-gray-100 focus:ring-2 focus:outline-none dark:hover:bg-slate-800`}
        >
          <Avatar className="h-10 w-10">
            <AvatarImage
              src={user?.avatarUrl || 'https://github.com/shadcn.png'}
              alt={user?.fullName || '@shadcn'}
            />
            <AvatarFallback>{user?.fullName?.charAt(0) || 'U'}</AvatarFallback>
          </Avatar>
          <span className="hidden text-sm font-medium text-gray-700 sm:block dark:text-gray-200">
            {user?.fullName || 'No name'}
          </span>
          <ChevronDown className="hidden h-4 w-4 text-gray-500 sm:block" />
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent
        align="end"
        className="mt-2 flex w-56 flex-col gap-1 rounded-xl p-2 shadow-lg"
      >
        <DropdownMenuLabel className="font-normal">
          <div className="flex flex-col space-y-1">
            <p className="text-sm leading-none font-medium text-gray-900 dark:text-white">
              {user?.fullName}
            </p>
            <p className="text-xs leading-none text-gray-500 dark:text-gray-400">{user?.email}</p>
          </div>
        </DropdownMenuLabel>
        <DropdownMenuSeparator className="bg-gray-100 dark:bg-slate-700" />
        <DropdownMenuItem onClick={() => router.push('/profile')} className="cursor-pointer">
          <UserIcon /> Hồ sơ cá nhân
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => router.push('/setting/theme')} className="cursor-pointer">
          <Settings /> Cài đặt
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => router.push('/dashboard')} className="cursor-pointer">
          <ShieldUser /> Quản trị viên
        </DropdownMenuItem>
        <DropdownMenuSeparator className="bg-gray-100 dark:bg-slate-700" />
        <DropdownMenuItem onClick={() => router.push('/auth/signup')} className="cursor-pointer">
          <MailQuestion /> Đăng ký
        </DropdownMenuItem>
        <DropdownMenuItem onClick={() => router.push('/auth/login')} className="cursor-pointer">
          <KeyRound /> Đăng nhập
        </DropdownMenuItem>
        <DropdownMenuItem onClick={handleLogout} variant="destructive" className="cursor-pointer">
          <LogOut /> Đăng xuất
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
