import { Fragment } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { 
  XMarkIcon,
  HomeIcon,
  CloudArrowUpIcon,
  ClockIcon,
  CreditCardIcon,
  UserGroupIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline';
import { Link, useLocation } from 'react-router-dom';
import { useAuthStore } from '../../stores/authStore';
import { cn } from '../../utils/helpers';
import { ROUTES } from '../../utils/constants';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

const navigation = [
  { name: 'Dashboard', href: ROUTES.DASHBOARD, icon: HomeIcon },
  { name: 'Upload Formula', href: ROUTES.UPLOAD, icon: CloudArrowUpIcon },
  { name: 'History', href: ROUTES.HISTORY, icon: ClockIcon },
  { name: 'Wallet', href: ROUTES.WALLET, icon: CreditCardIcon },
];

const adminNavigation = [
  { name: 'Admin Panel', href: ROUTES.ADMIN, icon: UserGroupIcon },
  { name: 'Analytics', href: ROUTES.ADMIN + '/analytics', icon: ChartBarIcon },
];

export function Sidebar({ isOpen, onClose }: SidebarProps) {
  const location = useLocation();
  const { user } = useAuthStore();
  
  // Check if user is admin (you might want to add role to user type)
  const isAdmin = user?.email?.includes('admin'); // Temporary check

  const NavLink = ({ item, mobile = false }: { item: { name: string; href: string; icon: any }, mobile?: boolean }) => {
    const isActive = location.pathname === item.href;
    
    return (
      <Link
        to={item.href}
        onClick={mobile ? onClose : undefined}
        className={cn(
          'group flex items-center px-2 py-2 text-base font-medium rounded-md transition-colors',
          isActive
            ? 'bg-blue-100 dark:bg-blue-900/20 text-blue-900 dark:text-blue-100'
            : 'text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 hover:text-gray-900 dark:hover:text-white'
        )}
      >
        <item.icon
          className={cn(
            'mr-4 flex-shrink-0 h-6 w-6',
            isActive
              ? 'text-blue-500 dark:text-blue-400'
              : 'text-gray-400 group-hover:text-gray-500 dark:group-hover:text-gray-300'
          )}
        />
        {item.name}
      </Link>
    );
  };

  const SidebarContent = () => (
    <div className="flex flex-col h-full">
      <div className="flex-1 flex flex-col pt-5 pb-4 overflow-y-auto">
        <div className="flex items-center flex-shrink-0 px-4">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            Navigation
          </h2>
        </div>
        <nav className="mt-5 flex-1 px-2 space-y-1">
          {navigation.map((item) => (
            <NavLink key={item.name} item={item} mobile={true} />
          ))}
          
          {isAdmin && (
            <>
              <div className="pt-6">
                <h3 className="px-3 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Administration
                </h3>
                <div className="mt-2 space-y-1">
                  {adminNavigation.map((item) => (
                    <NavLink key={item.name} item={item} mobile={true} />
                  ))}
                </div>
              </div>
            </>
          )}
        </nav>
      </div>
    </div>
  );

  return (
    <>
      {/* Mobile sidebar */}
      <Transition.Root show={isOpen} as={Fragment}>
        <Dialog as="div" className="relative z-40 md:hidden" onClose={onClose}>
          <Transition.Child
            as={Fragment}
            enter="transition-opacity ease-linear duration-300"
            enterFrom="opacity-0"
            enterTo="opacity-100"
            leave="transition-opacity ease-linear duration-300"
            leaveFrom="opacity-100"
            leaveTo="opacity-0"
          >
            <div className="fixed inset-0 bg-gray-600 bg-opacity-75" />
          </Transition.Child>

          <div className="fixed inset-0 flex z-40">
            <Transition.Child
              as={Fragment}
              enter="transition ease-in-out duration-300 transform"
              enterFrom="-translate-x-full"
              enterTo="translate-x-0"
              leave="transition ease-in-out duration-300 transform"
              leaveFrom="translate-x-0"
              leaveTo="-translate-x-full"
            >
              <Dialog.Panel className="relative flex-1 flex flex-col max-w-xs w-full pt-5 pb-4 bg-white dark:bg-gray-900">
                <Transition.Child
                  as={Fragment}
                  enter="ease-in-out duration-300"
                  enterFrom="opacity-0"
                  enterTo="opacity-100"
                  leave="ease-in-out duration-300"
                  leaveFrom="opacity-100"
                  leaveTo="opacity-0"
                >
                  <div className="absolute top-0 right-0 -mr-12 pt-2">
                    <button
                      type="button"
                      className="ml-1 flex items-center justify-center h-10 w-10 rounded-full focus:outline-none focus:ring-2 focus:ring-inset focus:ring-white"
                      onClick={onClose}
                    >
                      <span className="sr-only">Close sidebar</span>
                      <XMarkIcon className="h-6 w-6 text-white" aria-hidden="true" />
                    </button>
                  </div>
                </Transition.Child>
                <SidebarContent />
              </Dialog.Panel>
            </Transition.Child>
            <div className="flex-shrink-0 w-14" aria-hidden="true">
              {/* Dummy element to force sidebar to shrink to fit close icon */}
            </div>
          </div>
        </Dialog>
      </Transition.Root>

      {/* Static sidebar for desktop */}
      <div className="hidden md:flex md:w-64 md:flex-col md:fixed md:inset-y-0">
        <div className="flex flex-col flex-grow border-r border-gray-200 dark:border-gray-700 pt-16 bg-white dark:bg-gray-900 overflow-y-auto">
          <SidebarContent />
        </div>
      </div>
    </>
  );
}