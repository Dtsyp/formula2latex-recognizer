import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  CpuChipIcon, 
  DocumentDuplicateIcon, 
  EyeIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';
import { Card, CardContent, CardHeader } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { FileUpload } from '../components/ui/FileUpload';
import { useAuthStore } from '../stores/authStore';
import { modelsAPI, tasksAPI } from '../services/api';
import { ROUTES } from '../utils/constants';
import type { MLModel, Task } from '../types';

export function UploadPage() {
  const navigate = useNavigate();
  const { wallet, setWallet } = useAuthStore();
  
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [selectedModel, setSelectedModel] = useState<string>('');
  const [models, setModels] = useState<MLModel[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [result, setResult] = useState<Task | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Load available models
  useEffect(() => {
    const loadModels = async () => {
      try {
        const modelsData = await modelsAPI.getModels();
        setModels(modelsData.filter(model => model.is_active));
        if (modelsData.length > 0) {
          setSelectedModel(modelsData[0].id);
        }
      } catch (error) {
        console.error('Failed to load models:', error);
      }
    };

    loadModels();
  }, []);

  const handleFileSelect = (file: File) => {
    setSelectedFile(file);
    setResult(null);
    setError(null);
  };

  const handleFileRemove = () => {
    setSelectedFile(null);
    setResult(null);
    setError(null);
  };

  const handleSubmit = async () => {
    if (!selectedFile || !selectedModel) return;

    const selectedModelData = models.find(m => m.id === selectedModel);
    if (!selectedModelData) return;

    // Check wallet balance
    if (!wallet || wallet.balance < selectedModelData.credit_cost) {
      setError(`Insufficient credits. You need ${selectedModelData.credit_cost} credits but have ${wallet?.balance || 0}.`);
      return;
    }

    setIsProcessing(true);
    setError(null);

    try {
      // Upload and process the formula
      const task = await tasksAPI.uploadFormula(selectedFile, selectedModel);
      
      // Poll for completion
      let completedTask = task;
      let attempts = 0;
      const maxAttempts = 30; // 30 seconds max wait time

      while (completedTask.status === 'pending' || completedTask.status === 'in_progress') {
        if (attempts >= maxAttempts) {
          throw new Error('Processing timeout. Please check your task history.');
        }

        await new Promise(resolve => setTimeout(resolve, 1000));
        completedTask = await tasksAPI.getTask(task.id);
        attempts++;
      }

      if (completedTask.status === 'done') {
        setResult(completedTask);
        // Update wallet balance
        if (wallet) {
          setWallet({
            ...wallet,
            balance: wallet.balance - selectedModelData.credit_cost
          });
        }
      } else {
        setError(completedTask.error_message || 'Processing failed. Please try again.');
      }
    } catch (error: any) {
      setError(error.message || 'Failed to process formula. Please try again.');
    } finally {
      setIsProcessing(false);
    }
  };

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      // You could add a toast notification here
    } catch (error) {
      console.error('Failed to copy:', error);
    }
  };

  const selectedModelData = models.find(m => m.id === selectedModel);

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          Upload Formula
        </h1>
        <p className="mt-2 text-lg text-gray-600 dark:text-gray-400">
          Convert your mathematical formulas to LaTeX code instantly
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Upload Section */}
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                1. Select Formula Image
              </h2>
            </CardHeader>
            <CardContent>
              <FileUpload
                onFileSelect={handleFileSelect}
                onFileRemove={handleFileRemove}
                currentFile={selectedFile}
                isUploading={isProcessing}
                accept="image/*"
                maxSize={10}
              />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                2. Choose AI Model
              </h2>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 gap-4">
                {models.map((model) => (
                  <div
                    key={model.id}
                    className={`relative rounded-lg border-2 cursor-pointer transition-colors ${
                      selectedModel === model.id
                        ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                        : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                    }`}
                    onClick={() => setSelectedModel(model.id)}
                  >
                    <div className="p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          <CpuChipIcon className="h-6 w-6 text-blue-600" />
                          <div>
                            <h3 className="text-sm font-medium text-gray-900 dark:text-white">
                              {model.name}
                            </h3>
                            <p className="text-sm text-gray-500 dark:text-gray-400">
                              High accuracy formula recognition
                            </p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="text-sm font-medium text-gray-900 dark:text-white">
                            {model.credit_cost} credits
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <div className="flex justify-between items-center">
            <Button
              variant="outline"
              onClick={() => navigate(ROUTES.DASHBOARD)}
            >
              Cancel
            </Button>
            <Button
              onClick={handleSubmit}
              disabled={!selectedFile || !selectedModel || isProcessing}
              isLoading={isProcessing}
              className="min-w-[120px]"
            >
              {isProcessing ? 'Processing...' : 'Convert Formula'}
            </Button>
          </div>

          {error && (
            <div className="flex items-center space-x-2 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-md">
              <ExclamationTriangleIcon className="h-5 w-5 text-red-600 dark:text-red-400" />
              <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
            </div>
          )}
        </div>

        {/* Info Panel */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                Your Wallet
              </h3>
            </CardHeader>
            <CardContent>
              <div className="text-center">
                <p className="text-2xl font-bold text-blue-600">
                  ${wallet?.balance.toFixed(2) || '0.00'}
                </p>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Available credits
                </p>
                {selectedModelData && (
                  <div className="mt-4 p-3 bg-gray-50 dark:bg-gray-800 rounded-md">
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      This conversion will cost:
                    </p>
                    <p className="text-lg font-semibold text-gray-900 dark:text-white">
                      {selectedModelData.credit_cost} credits
                    </p>
                  </div>
                )}
                <Button
                  variant="outline"
                  size="sm"
                  className="mt-4 w-full"
                  onClick={() => navigate(ROUTES.WALLET)}
                >
                  Top Up Wallet
                </Button>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <h3 className="text-lg font-medium text-gray-900 dark:text-white">
                Tips for Best Results
              </h3>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2 text-sm text-gray-600 dark:text-gray-400">
                <li>• Use high-resolution images</li>
                <li>• Ensure good lighting and contrast</li>
                <li>• Keep formulas clearly visible</li>
                <li>• Avoid blur or distortion</li>
                <li>• PNG or JPEG formats work best</li>
              </ul>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Result Section */}
      {result && (
        <Card>
          <CardHeader>
            <div className="flex items-center space-x-2">
              <CheckCircleIcon className="h-6 w-6 text-green-600" />
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
                Conversion Complete!
              </h2>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  LaTeX Output:
                </label>
                <div className="relative">
                  <pre className="bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-md p-4 text-sm font-mono overflow-x-auto">
                    {result.output_data}
                  </pre>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="absolute top-2 right-2"
                    onClick={() => copyToClipboard(result.output_data || '')}
                  >
                    <DocumentDuplicateIcon className="h-4 w-4" />
                  </Button>
                </div>
              </div>

              <div className="flex space-x-4">
                <Button
                  variant="outline"
                  onClick={() => navigate(ROUTES.HISTORY)}
                >
                  <EyeIcon className="h-4 w-4 mr-2" />
                  View in History
                </Button>
                <Button
                  onClick={() => {
                    setResult(null);
                    setSelectedFile(null);
                  }}
                >
                  Convert Another
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}