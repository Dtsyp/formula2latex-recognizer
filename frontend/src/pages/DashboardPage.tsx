import { Link } from 'react-router-dom';
import { 
  CloudArrowUpIcon, 
  ClockIcon, 
  CreditCardIcon,
  DocumentTextIcon,
  ChartBarIcon,
  PlusIcon
} from '@heroicons/react/24/outline';
import { Card, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { useAuthStore } from '../stores/authStore';
import { ROUTES } from '../utils/constants';

export function DashboardPage() {
  const { user, wallet } = useAuthStore();

  const stats = [
    {
      name: 'Total Formulas',
      value: '24',
      icon: DocumentTextIcon,
      change: '+2.1%',
      changeType: 'increase' as const,
    },
    {
      name: 'Credits Used',
      value: '48',
      icon: ChartBarIcon,
      change: '+15.3%',
      changeType: 'increase' as const,
    },
    {
      name: 'Success Rate',
      value: '98.2%',
      icon: ChartBarIcon,
      change: '+0.4%',
      changeType: 'increase' as const,
    },
    {
      name: 'Wallet Balance',
      value: `$${wallet?.balance.toFixed(2) || '0.00'}`,
      icon: CreditCardIcon,
      change: '-$12.50',
      changeType: 'decrease' as const,
    },
  ];

  const recentTasks = [
    {
      id: '1',
      filename: 'equation_1.png',
      status: 'completed',
      created_at: '2024-01-15T10:30:00Z',
      credits_charged: 2,
    },
    {
      id: '2',
      filename: 'integral_formula.jpg',
      status: 'completed',
      created_at: '2024-01-15T09:15:00Z',
      credits_charged: 3,
    },
    {
      id: '3',
      filename: 'matrix_calc.png',
      status: 'in_progress',
      created_at: '2024-01-15T08:45:00Z',
      credits_charged: 2,
    },
  ];

  const quickActions = [
    {
      title: 'Upload Formula',
      description: 'Convert a new formula image to LaTeX',
      icon: CloudArrowUpIcon,
      href: ROUTES.UPLOAD,
      primary: true,
    },
    {
      title: 'View History',
      description: 'Browse your previous conversions',
      icon: ClockIcon,
      href: ROUTES.HISTORY,
      primary: false,
    },
    {
      title: 'Top Up Wallet',
      description: 'Add credits to your account',
      icon: CreditCardIcon,
      href: ROUTES.WALLET,
      primary: false,
    },
  ];

  return (
    <div className="space-y-8">
      {/* Welcome Section */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Welcome back, {user?.email}!
        </h1>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          Here's what's happening with your formula conversions.
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <Card key={stat.name}>
            <CardContent className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <stat.icon className="h-6 w-6 text-gray-400" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 dark:text-gray-400 truncate">
                      {stat.name}
                    </dt>
                    <dd className="flex items-baseline">
                      <div className="text-2xl font-semibold text-gray-900 dark:text-white">
                        {stat.value}
                      </div>
                      <div className={`ml-2 flex items-baseline text-sm font-semibold ${
                        stat.changeType === 'increase' 
                          ? 'text-green-600 dark:text-green-400' 
                          : 'text-red-600 dark:text-red-400'
                      }`}>
                        {stat.change}
                      </div>
                    </dd>
                  </dl>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Quick Actions */}
      <div>
        <h2 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
          Quick Actions
        </h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          {quickActions.map((action) => (
            <Card key={action.title} className="hover:shadow-md transition-shadow">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className={`flex-shrink-0 p-2 rounded-md ${
                      action.primary 
                        ? 'bg-blue-100 dark:bg-blue-900/20' 
                        : 'bg-gray-100 dark:bg-gray-800'
                    }`}>
                      <action.icon className={`h-6 w-6 ${
                        action.primary 
                          ? 'text-blue-600 dark:text-blue-400' 
                          : 'text-gray-600 dark:text-gray-400'
                      }`} />
                    </div>
                    <div>
                      <h3 className="text-sm font-medium text-gray-900 dark:text-white">
                        {action.title}
                      </h3>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        {action.description}
                      </p>
                    </div>
                  </div>
                  <Link to={action.href}>
                    <Button 
                      variant={action.primary ? 'primary' : 'outline'} 
                      size="sm"
                    >
                      <PlusIcon className="h-4 w-4" />
                    </Button>
                  </Link>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* Recent Tasks */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-medium text-gray-900 dark:text-white">
            Recent Tasks
          </h2>
          <Link to={ROUTES.HISTORY}>
            <Button variant="ghost" size="sm">
              View all
            </Button>
          </Link>
        </div>
        
        <Card>
          <CardContent className="p-0">
            <div className="overflow-hidden">
              <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                <thead className="bg-gray-50 dark:bg-gray-800">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      File
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Credits
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                      Date
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
                  {recentTasks.map((task) => (
                    <tr key={task.id} className="hover:bg-gray-50 dark:hover:bg-gray-800">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                        {task.filename}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          task.status === 'completed' 
                            ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400'
                            : task.status === 'in_progress'
                            ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400'
                            : 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400'
                        }`}>
                          {task.status.replace('_', ' ')}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                        {task.credits_charged}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                        {new Date(task.created_at).toLocaleDateString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}