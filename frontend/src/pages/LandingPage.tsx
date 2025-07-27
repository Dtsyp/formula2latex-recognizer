import { Link } from 'react-router-dom';
import { 
  DocumentTextIcon, 
  ArrowRightIcon, 
  CloudArrowUpIcon,
  CpuChipIcon,
  LightBulbIcon
} from '@heroicons/react/24/outline';
import { Button } from '../components/ui/Button';
import { Card, CardContent } from '../components/ui/Card';
import { ROUTES } from '../utils/constants';

export function LandingPage() {
  const features = [
    {
      icon: CloudArrowUpIcon,
      title: 'Easy Upload',
      description: 'Simply upload an image of your mathematical formula and let our AI do the work.',
    },
    {
      icon: CpuChipIcon,
      title: 'AI-Powered Recognition',
      description: 'Advanced machine learning models accurately convert handwritten or printed formulas.',
    },
    {
      icon: DocumentTextIcon,
      title: 'LaTeX Output',
      description: 'Get clean, properly formatted LaTeX code that you can use in your documents.',
    },
    {
      icon: LightBulbIcon,
      title: 'Smart Processing',
      description: 'Our models understand complex mathematical notation and structure.',
    },
  ];

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Hero Section */}
      <div className="relative overflow-hidden">
        <div className="max-w-7xl mx-auto">
          <div className="relative z-10 pb-8 bg-gray-50 dark:bg-gray-900 sm:pb-16 md:pb-20 lg:max-w-2xl lg:w-full lg:pb-28 xl:pb-32">
            <main className="mt-10 mx-auto max-w-7xl px-4 sm:mt-12 sm:px-6 md:mt-16 lg:mt-20 lg:px-8 xl:mt-28">
              <div className="sm:text-center lg:text-left">
                <h1 className="text-4xl tracking-tight font-extrabold text-gray-900 dark:text-white sm:text-5xl md:text-6xl">
                  <span className="block xl:inline">Convert formulas to</span>{' '}
                  <span className="block text-blue-600 xl:inline">LaTeX instantly</span>
                </h1>
                <p className="mt-3 text-base text-gray-500 dark:text-gray-400 sm:mt-5 sm:text-lg sm:max-w-xl sm:mx-auto md:mt-5 md:text-xl lg:mx-0">
                  Upload an image of any mathematical formula and get clean LaTeX code in seconds. 
                  Perfect for students, researchers, and anyone working with mathematical documents.
                </p>
                <div className="mt-5 sm:mt-8 sm:flex sm:justify-center lg:justify-start">
                  <div className="rounded-md shadow">
                    <Link to={ROUTES.REGISTER}>
                      <Button size="lg" className="w-full flex items-center justify-center px-8 py-3 text-base">
                        Get started
                        <ArrowRightIcon className="ml-2 -mr-1 w-5 h-5" />
                      </Button>
                    </Link>
                  </div>
                  <div className="mt-3 sm:mt-0 sm:ml-3">
                    <Link to={ROUTES.LOGIN}>
                      <Button 
                        variant="outline" 
                        size="lg" 
                        className="w-full flex items-center justify-center px-8 py-3 text-base"
                      >
                        Sign in
                      </Button>
                    </Link>
                  </div>
                </div>
              </div>
            </main>
          </div>
        </div>
        <div className="lg:absolute lg:inset-y-0 lg:right-0 lg:w-1/2">
          <div className="h-56 w-full bg-gradient-to-br from-blue-400 to-blue-600 sm:h-72 md:h-96 lg:w-full lg:h-full flex items-center justify-center">
            <div className="text-white text-6xl font-bold opacity-20">
              ∫ ∑ π ∞ ∂
            </div>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="py-12 bg-white dark:bg-gray-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="lg:text-center">
            <h2 className="text-base text-blue-600 font-semibold tracking-wide uppercase">Features</h2>
            <p className="mt-2 text-3xl leading-8 font-extrabold tracking-tight text-gray-900 dark:text-white sm:text-4xl">
              Powerful formula recognition
            </p>
            <p className="mt-4 max-w-2xl text-xl text-gray-500 dark:text-gray-400 lg:mx-auto">
              Our advanced AI models can handle complex mathematical notation with high accuracy.
            </p>
          </div>

          <div className="mt-10">
            <div className="space-y-10 md:space-y-0 md:grid md:grid-cols-2 md:gap-x-8 md:gap-y-10">
              {features.map((feature) => (
                <Card key={feature.title} className="relative">
                  <CardContent className="p-6">
                    <div className="flex">
                      <div className="flex-shrink-0">
                        <div className="flex items-center justify-center h-12 w-12 rounded-md bg-blue-500 text-white">
                          <feature.icon className="h-6 w-6" aria-hidden="true" />
                        </div>
                      </div>
                      <div className="ml-4">
                        <h3 className="text-lg leading-6 font-medium text-gray-900 dark:text-white">
                          {feature.title}
                        </h3>
                        <p className="mt-2 text-base text-gray-500 dark:text-gray-400">
                          {feature.description}
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Stats Section */}
      <div className="bg-blue-50 dark:bg-blue-900/20">
        <div className="max-w-7xl mx-auto py-12 px-4 sm:py-16 sm:px-6 lg:px-8 lg:py-20">
          <div className="max-w-4xl mx-auto text-center">
            <h2 className="text-3xl font-extrabold text-gray-900 dark:text-white sm:text-4xl">
              Trusted by thousands of users
            </h2>
            <p className="mt-3 text-xl text-gray-500 dark:text-gray-400 sm:mt-4">
              Join the community of students, researchers, and professionals.
            </p>
          </div>
          <dl className="mt-10 text-center sm:max-w-3xl sm:mx-auto sm:grid sm:grid-cols-3 sm:gap-8">
            <div className="flex flex-col">
              <dt className="order-2 mt-2 text-lg leading-6 font-medium text-gray-500 dark:text-gray-400">
                Formulas processed
              </dt>
              <dd className="order-1 text-5xl font-extrabold text-blue-600">50K+</dd>
            </div>
            <div className="flex flex-col mt-10 sm:mt-0">
              <dt className="order-2 mt-2 text-lg leading-6 font-medium text-gray-500 dark:text-gray-400">
                Accuracy rate
              </dt>
              <dd className="order-1 text-5xl font-extrabold text-blue-600">98%</dd>
            </div>
            <div className="flex flex-col mt-10 sm:mt-0">
              <dt className="order-2 mt-2 text-lg leading-6 font-medium text-gray-500 dark:text-gray-400">
                Active users
              </dt>
              <dd className="order-1 text-5xl font-extrabold text-blue-600">5K+</dd>
            </div>
          </dl>
        </div>
      </div>

      {/* CTA Section */}
      <div className="bg-gray-50 dark:bg-gray-900">
        <div className="max-w-7xl mx-auto py-12 px-4 sm:px-6 lg:py-16 lg:px-8 lg:flex lg:items-center lg:justify-between">
          <h2 className="text-3xl font-extrabold tracking-tight text-gray-900 dark:text-white sm:text-4xl">
            <span className="block">Ready to get started?</span>
            <span className="block text-blue-600">Create your account today.</span>
          </h2>
          <div className="mt-8 flex lg:mt-0 lg:flex-shrink-0">
            <div className="inline-flex rounded-md shadow">
              <Link to={ROUTES.REGISTER}>
                <Button size="lg" className="px-8 py-3">
                  Get started
                </Button>
              </Link>
            </div>
            <div className="ml-3 inline-flex rounded-md shadow">
              <Link to={ROUTES.LOGIN}>
                <Button variant="outline" size="lg" className="px-8 py-3">
                  Learn more
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}