import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import ChatInterface from '../components/ChatInterface';
import { recordingAPI, summaryAPI } from '../services/api';
import { Mic, FileText, Clock, TrendingUp } from 'lucide-react';

const Dashboard = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState({
    totalRecordings: 0,
    totalSummaries: 0,
    recentActivity: [],
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const [recordingsResponse, summariesResponse] = await Promise.all([
        recordingAPI.getAll(),
        summaryAPI.getAll(),
      ]);

      setStats({
        totalRecordings: recordingsResponse.data.total,
        totalSummaries: summariesResponse.data.total,
        recentActivity: recordingsResponse.data.recordings.slice(0, 5),
      });
    } catch (error) {
      console.error('Error loading stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        {/* Welcome Header */}
        <div className="px-4 py-6 sm:px-0">
          <h1 className="text-3xl font-bold text-gray-900">
            Welcome back, {user?.name}!
          </h1>
          <p className="mt-2 text-gray-600">
            Upload or record audio to get AI-powered transcriptions and summaries.
          </p>
        </div>

        {/* Stats Cards */}
        <div className="px-4 sm:px-0">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            <div className="card">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <Mic className="h-8 w-8 text-primary-600" />
                </div>
                <div className="ml-4">
                  <h2 className="text-lg font-medium text-gray-900">Total Recordings</h2>
                  <p className="text-3xl font-bold text-primary-600">
                    {loading ? '...' : stats.totalRecordings}
                  </p>
                </div>
              </div>
            </div>

            <div className="card">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <FileText className="h-8 w-8 text-green-600" />
                </div>
                <div className="ml-4">
                  <h2 className="text-lg font-medium text-gray-900">Summaries Generated</h2>
                  <p className="text-3xl font-bold text-green-600">
                    {loading ? '...' : stats.totalSummaries}
                  </p>
                </div>
              </div>
            </div>

            <div className="card">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <TrendingUp className="h-8 w-8 text-blue-600" />
                </div>
                <div className="ml-4">
                  <h2 className="text-lg font-medium text-gray-900">Processing Rate</h2>
                  <p className="text-3xl font-bold text-blue-600">
                    {stats.totalSummaries > 0 
                      ? `${Math.round((stats.totalSummaries / stats.totalRecordings) * 100)}%`
                      : '0%'
                    }
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="px-4 sm:px-0">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Chat Interface */}
            <div className="lg:col-span-2">
              <ChatInterface />
            </div>

            {/* Recent Activity */}
            <div className="lg:col-span-1">
              <div className="card">
                <h3 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
                  <Clock className="h-5 w-5 mr-2" />
                  Recent Activity
                </h3>
                
                {loading ? (
                  <div className="text-center py-8 text-gray-500">
                    Loading...
                  </div>
                ) : stats.recentActivity.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <Mic className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                    <p>No recordings yet</p>
                    <p className="text-sm">Upload your first audio file to get started!</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {stats.recentActivity.map((recording) => (
                      <div key={recording.id} className="border-b border-gray-200 pb-4 last:border-b-0">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <h4 className="text-sm font-medium text-gray-900 truncate">
                              {recording.title}
                            </h4>
                            <p className="text-xs text-gray-500 mt-1">
                              {formatDate(recording.created_at)}
                            </p>
                            <div className="mt-2">
                              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                                recording.status === 'completed' 
                                  ? 'bg-green-100 text-green-800'
                                  : recording.status === 'processing'
                                  ? 'bg-yellow-100 text-yellow-800'
                                  : recording.status === 'error'
                                  ? 'bg-red-100 text-red-800'
                                  : 'bg-gray-100 text-gray-800'
                              }`}>
                                {recording.status}
                              </span>
                            </div>
                          </div>
                          <div className="flex-shrink-0 ml-4">
                            {recording.file_size && (
                              <span className="text-xs text-gray-400">
                                {(recording.file_size / 1024 / 1024).toFixed(1)} MB
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
