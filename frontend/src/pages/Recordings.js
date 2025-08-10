import React, { useState, useEffect } from 'react';
import { recordingAPI } from '../services/api';
import { Trash2, Eye, Download, Play, Pause, Loader, FileText } from 'lucide-react';
import toast from 'react-hot-toast';

const Recordings = () => {
  const [recordings, setRecordings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedRecording, setSelectedRecording] = useState(null);
  const [showSummary, setShowSummary] = useState(false);

  useEffect(() => {
    loadRecordings();
  }, []);

  const loadRecordings = async () => {
    try {
      const response = await recordingAPI.getAll();
      setRecordings(response.data.recordings);
    } catch (error) {
      toast.error('Failed to load recordings');
      console.error('Error loading recordings:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this recording?')) {
      return;
    }

    try {
      await recordingAPI.delete(id);
      setRecordings(recordings.filter(r => r.id !== id));
      toast.success('Recording deleted successfully');
    } catch (error) {
      toast.error('Failed to delete recording');
      console.error('Error deleting recording:', error);
    }
  };

  const handleViewSummary = async (recording) => {
    try {
      const response = await recordingAPI.getSummary(recording.id);
      setSelectedRecording({
        ...recording,
        summary: response.data
      });
      setShowSummary(true);
    } catch (error) {
      toast.error('Failed to load summary');
      console.error('Error loading summary:', error);
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const formatFileSize = (bytes) => {
    if (!bytes) return 'N/A';
    const mb = bytes / 1024 / 1024;
    return `${mb.toFixed(2)} MB`;
  };

  const formatDuration = (seconds) => {
    if (!seconds) return 'N/A';
    const minutes = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'processing':
        return 'bg-yellow-100 text-yellow-800';
      case 'error':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <Loader className="h-8 w-8 animate-spin text-primary-600" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <h1 className="text-3xl font-bold text-gray-900">My Recordings</h1>
          <p className="mt-2 text-gray-600">
            Manage your uploaded audio files and view their summaries.
          </p>
        </div>

        {recordings.length === 0 ? (
          <div className="text-center py-12">
            <FileText className="h-12 w-12 mx-auto text-gray-400 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No recordings yet</h3>
            <p className="text-gray-600">Upload your first audio file to get started!</p>
          </div>
        ) : (
          <div className="bg-white shadow overflow-hidden sm:rounded-md">
            <ul className="divide-y divide-gray-200">
              {recordings.map((recording) => (
                <li key={recording.id}>
                  <div className="px-4 py-4 sm:px-6 hover:bg-gray-50">
                    <div className="flex items-center justify-between">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center space-x-3">
                          <h3 className="text-lg font-medium text-gray-900 truncate">
                            {recording.title}
                          </h3>
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(recording.status)}`}>
                            {recording.status}
                          </span>
                        </div>
                        
                        <div className="mt-2 flex items-center space-x-6 text-sm text-gray-500">
                          <span>📁 {recording.filename}</span>
                          <span>💾 {formatFileSize(recording.file_size)}</span>
                          <span>⏱️ {formatDuration(recording.duration)}</span>
                          <span>📅 {formatDate(recording.created_at)}</span>
                        </div>

                        {recording.transcript && (
                          <div className="mt-3">
                            <p className="text-sm text-gray-600 line-clamp-2">
                              <strong>Transcript:</strong> {recording.transcript.substring(0, 150)}...
                            </p>
                          </div>
                        )}
                      </div>

                      <div className="flex items-center space-x-2 ml-4">
                        {recording.status === 'completed' && (
                          <button
                            onClick={() => handleViewSummary(recording)}
                            className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                          >
                            <Eye className="h-4 w-4 mr-1" />
                            View Summary
                          </button>
                        )}
                        
                        <button
                          onClick={() => handleDelete(recording.id)}
                          className="inline-flex items-center px-3 py-2 border border-red-300 shadow-sm text-sm leading-4 font-medium rounded-md text-red-700 bg-white hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                        >
                          <Trash2 className="h-4 w-4 mr-1" />
                          Delete
                        </button>
                      </div>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Summary Modal */}
        {showSummary && selectedRecording && (
          <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
            <div className="relative top-20 mx-auto p-5 border w-11/12 md:w-3/4 lg:w-1/2 shadow-lg rounded-md bg-white">
              <div className="mt-3">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-medium text-gray-900">
                    Summary: {selectedRecording.title}
                  </h3>
                  <button
                    onClick={() => setShowSummary(false)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    ✕
                  </button>
                </div>

                <div className="max-h-96 overflow-y-auto space-y-6">
                  {/* Transcript */}
                  {selectedRecording.transcript && (
                    <div>
                      <h4 className="font-medium text-gray-900 mb-2">📝 Transcript</h4>
                      <div className="bg-gray-50 p-4 rounded-lg">
                        <p className="text-sm text-gray-700 whitespace-pre-wrap">
                          {selectedRecording.transcript}
                        </p>
                      </div>
                    </div>
                  )}

                  {/* Summary */}
                  {selectedRecording.summary?.content && (
                    <div>
                      <h4 className="font-medium text-gray-900 mb-2">📋 Summary</h4>
                      <div className="bg-green-50 border-l-4 border-green-500 p-4">
                        <p className="text-sm text-gray-700">
                          {selectedRecording.summary.content}
                        </p>
                      </div>
                    </div>
                  )}

                  {/* Action Items */}
                  {selectedRecording.summary?.action_items && JSON.parse(selectedRecording.summary.action_items).length > 0 && (
                    <div>
                      <h4 className="font-medium text-gray-900 mb-2">✅ Action Items</h4>
                      <div className="bg-yellow-50 border-l-4 border-yellow-500 p-4">
                        <ul className="list-disc list-inside space-y-1">
                          {JSON.parse(selectedRecording.summary.action_items).map((item, index) => (
                            <li key={index} className="text-sm text-gray-700">{item}</li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  )}

                  {/* Key Points */}
                  {selectedRecording.summary?.key_points && JSON.parse(selectedRecording.summary.key_points).length > 0 && (
                    <div>
                      <h4 className="font-medium text-gray-900 mb-2">🔑 Key Points</h4>
                      <div className="bg-purple-50 border-l-4 border-purple-500 p-4">
                        <ul className="list-disc list-inside space-y-1">
                          {JSON.parse(selectedRecording.summary.key_points).map((point, index) => (
                            <li key={index} className="text-sm text-gray-700">{point}</li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  )}
                </div>

                <div className="mt-6 flex justify-end">
                  <button
                    onClick={() => setShowSummary(false)}
                    className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500"
                  >
                    Close
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Recordings;
