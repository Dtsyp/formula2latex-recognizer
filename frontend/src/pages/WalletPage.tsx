import { useState, useEffect } from 'react';
import { 
  CreditCardIcon, 
  PlusIcon,
  ClockIcon,
  ArrowUpIcon,
  ArrowDownIcon,
  BanknotesIcon
} from '@heroicons/react/24/outline';
import { Card, CardContent, CardHeader } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { useAuthStore } from '../stores/authStore';
import { walletAPI } from '../services/api';
import type { Transaction } from '../types';
import { formatDate, formatCurrency } from '../utils/helpers';

export function WalletPage() {
  const { wallet, setWallet } = useAuthStore();
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isTopUpModalOpen, setIsTopUpModalOpen] = useState(false);
  const [topUpAmount, setTopUpAmount] = useState('');
  const [isProcessingTopUp, setIsProcessingTopUp] = useState(false);
  const [topUpError, setTopUpError] = useState<string | null>(null);

  const predefinedAmounts = [5, 10, 25, 50, 100];

  useEffect(() => {
    const loadData = async () => {
      try {
        const [walletData, transactionsData] = await Promise.all([
          walletAPI.getWallet(),
          walletAPI.getTransactions()
        ]);
        
        setWallet(walletData);
        setTransactions(transactionsData.sort((a, b) => 
          new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        ));
      } catch (error) {
        console.error('Failed to load wallet data:', error);
      } finally {
        setIsLoading(false);
      }
    };

    loadData();
  }, [setWallet]);

  const handleTopUp = async () => {
    const amount = parseFloat(topUpAmount);
    if (!amount || amount <= 0) {
      setTopUpError('Please enter a valid amount');
      return;
    }

    if (amount < 5) {
      setTopUpError('Minimum top-up amount is $5');
      return;
    }

    if (amount > 1000) {
      setTopUpError('Maximum top-up amount is $1000');
      return;
    }

    setIsProcessingTopUp(true);
    setTopUpError(null);

    try {
      const transaction = await walletAPI.topUp({ amount });
      
      // Update wallet balance based on transaction
      if (wallet) {
        setWallet({
          ...wallet,
          balance: parseFloat(transaction.post_balance.toString())
        });
      }
      
      // Reload transactions to show the new one
      const transactionsData = await walletAPI.getTransactions();
      setTransactions(transactionsData.sort((a, b) => 
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      ));

      setIsTopUpModalOpen(false);
      setTopUpAmount('');
    } catch (error: any) {
      setTopUpError(error.response?.data?.detail || 'Top-up failed. Please try again.');
    } finally {
      setIsProcessingTopUp(false);
    }
  };

  const getTransactionIcon = (type: string) => {
    return type === 'top_up' ? ArrowUpIcon : ArrowDownIcon;
  };

  const getTransactionColor = (type: string) => {
    return type === 'top_up' 
      ? 'text-green-600 dark:text-green-400' 
      : 'text-red-600 dark:text-red-400';
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Wallet
          </h1>
          <p className="mt-2 text-lg text-gray-600 dark:text-gray-400">
            Manage your credits and view transaction history
          </p>
        </div>
      </div>

      {/* Balance Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="md:col-span-2">
          <CardContent className="p-8">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
                  Current Balance
                </p>
                <p className="text-4xl font-bold text-gray-900 dark:text-white">
                  {formatCurrency(wallet ? (typeof wallet.balance === 'number' ? wallet.balance : parseFloat(wallet.balance)) : 0)}
                </p>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                  Available for formula conversions
                </p>
              </div>
              <div className="flex flex-col space-y-2">
                <Button
                  onClick={() => setIsTopUpModalOpen(true)}
                  className="flex items-center"
                >
                  <PlusIcon className="h-4 w-4 mr-2" />
                  Add Credits
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <BanknotesIcon className="h-8 w-8 text-blue-600" />
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
                  Total Spent
                </p>
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {formatCurrency(
                    transactions
                      .filter(t => t.type === 'spend')
                      .reduce((sum, t) => sum + t.amount, 0)
                  )}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quick Top-up */}
      <Card>
        <CardHeader>
          <h3 className="text-lg font-medium text-gray-900 dark:text-white">
            Quick Top-up
          </h3>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-3">
            {predefinedAmounts.map((amount) => (
              <Button
                key={amount}
                variant="outline"
                onClick={() => {
                  setTopUpAmount(amount.toString());
                  setIsTopUpModalOpen(true);
                }}
                className="flex-shrink-0"
              >
                +{formatCurrency(amount)}
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Transaction History */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-medium text-gray-900 dark:text-white">
              Transaction History
            </h3>
            <ClockIcon className="h-5 w-5 text-gray-400" />
          </div>
        </CardHeader>
        <CardContent>
          {transactions.length === 0 ? (
            <div className="text-center py-8">
              <CreditCardIcon className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">
                No transactions yet
              </h3>
              <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
                Your transaction history will appear here.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {transactions.map((transaction) => {
                const Icon = getTransactionIcon(transaction.type);
                return (
                  <div
                    key={transaction.id}
                    className="flex items-center justify-between p-4 border border-gray-200 dark:border-gray-700 rounded-lg"
                  >
                    <div className="flex items-center space-x-4">
                      <div className={`p-2 rounded-full bg-gray-100 dark:bg-gray-800`}>
                        <Icon className={`h-5 w-5 ${getTransactionColor(transaction.type)}`} />
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-900 dark:text-white">
                          {transaction.type === 'top_up' ? 'Credit Top-up' : 'Formula Conversion'}
                        </p>
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                          {formatDate(transaction.created_at)}
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className={`text-sm font-medium ${getTransactionColor(transaction.type)}`}>
                        {transaction.type === 'top_up' ? '+' : '-'}{formatCurrency(transaction.amount)}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        Balance: {formatCurrency(transaction.post_balance)}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Top-up Modal */}
      {isTopUpModalOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg max-w-md w-full">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                  Add Credits
                </h3>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    setIsTopUpModalOpen(false);
                    setTopUpAmount('');
                    setTopUpError(null);
                  }}
                >
                  ×
                </Button>
              </div>

              <div className="space-y-4">
                <div>
                  <Input
                    label="Amount (USD)"
                    type="number"
                    value={topUpAmount}
                    onChange={(e) => setTopUpAmount(e.target.value)}
                    placeholder="Enter amount"
                    min="5"
                    max="1000"
                    step="0.01"
                    error={topUpError || undefined}
                  />
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    Minimum: $5, Maximum: $1000
                  </p>
                </div>

                <div className="grid grid-cols-3 gap-2">
                  {predefinedAmounts.slice(0, 3).map((amount) => (
                    <Button
                      key={amount}
                      variant="outline"
                      size="sm"
                      onClick={() => setTopUpAmount(amount.toString())}
                    >
                      ${amount}
                    </Button>
                  ))}
                </div>

                <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-md">
                  <p className="text-sm text-blue-800 dark:text-blue-200">
                    💳 Secure payment processing powered by Stripe
                  </p>
                </div>

                <div className="flex space-x-3">
                  <Button
                    variant="outline"
                    className="flex-1"
                    onClick={() => {
                      setIsTopUpModalOpen(false);
                      setTopUpAmount('');
                      setTopUpError(null);
                    }}
                  >
                    Cancel
                  </Button>
                  <Button
                    className="flex-1"
                    onClick={handleTopUp}
                    disabled={!topUpAmount || isProcessingTopUp}
                    isLoading={isProcessingTopUp}
                  >
                    {isProcessingTopUp ? 'Processing...' : 'Add Credits'}
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}