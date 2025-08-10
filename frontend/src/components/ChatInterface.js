import React, { useState, useRef, useEffect } from 'react';
import { Mic, MicOff, Upload, Send, Loader, AlertCircle, CheckCircle } from 'lucide-react';
import { recordingAPI, StreamingAPI } from '../services/api';
import toast from 'react-hot-toast';

const ChatInterface = () => {
  const [messages, setMessages] = useState([]);
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentRecordingId, setCurrentRecordingId] = useState(null);
  const [title, setTitle] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const [streamingContent, setStreamingContent] = useState('');
  
  const fileInputRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, streamingContent]);

  const addMessage = (type, content, metadata = {}) => {
    const message = {
      id: Date.now(),
      type, // 'user', 'bot', 'system'
      content,
      timestamp: new Date().toLocaleTimeString(),
      metadata
    };
    setMessages(prev => [...prev, message]);
  };

  const updateLastMessage = (content) => {
    setMessages(prev => {
      const newMessages = [...prev];
      if (newMessages.length > 0) {
        newMessages[newMessages.length - 1].content = content;
      }
      return newMessages;
    });
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      audioChunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data);
      };

      mediaRecorderRef.current.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        setSelectedFile(audioBlob);
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorderRef.current.start();
      setIsRecording(true);
      addMessage('system', '🎤 Recording started... Click stop when finished.');
    } catch (error) {
      toast.error('Could not access microphone');
      console.error('Error accessing microphone:', error);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      addMessage('system', '✅ Recording stopped. Ready to upload.');
    }
  };

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file) {
      setSelectedFile(file);
      addMessage('system', `📁 File selected: ${file.name}`);
    }
  };

  const uploadAndProcess = async () => {
    if (!selectedFile || !title.trim()) {
      toast.error('Please provide a title and select/record an audio file');
      return;
    }

    setIsProcessing(true);
    
    try {
      // Upload file
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('title', title.trim());

      addMessage('user', `📤 Uploading "${title}"`);
      
      const uploadResponse = await recordingAPI.upload(formData);
      const recordingId = uploadResponse.data.recording_id;
      setCurrentRecordingId(recordingId);

      addMessage('bot', '⏳ File uploaded successfully. Starting transcription...', {
        recordingId,
        status: 'processing'
      });

      // Start processing with streaming updates
      const processResponse = await recordingAPI.processNow(recordingId);
      
      if (processResponse.data.transcript) {
        // Show transcript
        addMessage('bot', '📝 Transcript:', { type: 'transcript' });
        addMessage('bot', processResponse.data.transcript, { 
          type: 'transcript-content',
          recordingId 
        });

        // Show summary with streaming effect
        if (processResponse.data.summary?.content) {
          addMessage('bot', '📋 Summary:', { type: 'summary' });
          
          // Simulate streaming summary
          const summaryContent = processResponse.data.summary.content;
          let currentIndex = 0;
          setStreamingContent('');
          
          const streamInterval = setInterval(() => {
            if (currentIndex < summaryContent.length) {
              setStreamingContent(prev => prev + summaryContent[currentIndex]);
              currentIndex++;
            } else {
              clearInterval(streamInterval);
              addMessage('bot', summaryContent, { 
                type: 'summary-content',
                recordingId 
              });
              setStreamingContent('');
              
              // Show action items
              if (processResponse.data.summary.action_items?.length > 0) {
                addMessage('bot', '✅ Action Items:', { type: 'action-items' });
                processResponse.data.summary.action_items.forEach((item, index) => {
                  setTimeout(() => {
                    addMessage('bot', `${index + 1}. ${item}`, { 
                      type: 'action-item',
                      recordingId 
                    });
                  }, (index + 1) * 500);
                });
              }

              // Show key points
              if (processResponse.data.summary.key_points?.length > 0) {
                setTimeout(() => {
                  addMessage('bot', '🔑 Key Points:', { type: 'key-points' });
                  processResponse.data.summary.key_points.forEach((point, index) => {
                    setTimeout(() => {
                      addMessage('bot', `• ${point}`, { 
                        type: 'key-point',
                        recordingId 
                      });
                    }, (index + 1) * 300);
                  });
                }, 2000);
              }
            }
          }, 50); // Typing effect speed
        }
      }

      // Reset form
      setTitle('');
      setSelectedFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
      
      toast.success('Processing completed!');
      
    } catch (error) {
      console.error('Processing error:', error);
      addMessage('bot', '❌ Processing failed: ' + (error.response?.data?.detail || error.message), {
        type: 'error'
      });
      toast.error('Processing failed');
    } finally {
      setIsProcessing(false);
      setCurrentRecordingId(null);
    }
  };

  const renderMessage = (message) => {
    const baseClasses = "chat-bubble mb-4";
    const userClasses = "chat-bubble-user";
    const botClasses = "chat-bubble-bot";
    const systemClasses = "bg-blue-50 text-blue-800 border border-blue-200";

    let messageClasses = baseClasses;
    if (message.type === 'user') {
      messageClasses += ` ${userClasses}`;
    } else if (message.type === 'bot') {
      messageClasses += ` ${botClasses}`;
    } else if (message.type === 'system') {
      messageClasses += ` ${systemClasses}`;
    }

    // Special styling for different content types
    if (message.metadata?.type === 'transcript-content') {
      messageClasses += " font-mono text-sm bg-gray-50 border-l-4 border-blue-500 pl-4";
    } else if (message.metadata?.type === 'summary-content') {
      messageClasses += " bg-green-50 border-l-4 border-green-500 pl-4";
    } else if (message.metadata?.type === 'action-item') {
      messageClasses += " bg-yellow-50 border-l-4 border-yellow-500 pl-4";
    } else if (message.metadata?.type === 'key-point') {
      messageClasses += " bg-purple-50 border-l-4 border-purple-500 pl-4";
    }

    return (
      <div key={message.id} className={messageClasses}>
        <div className="text-sm">
          {message.content}
        </div>
        <div className="text-xs opacity-70 mt-1">
          {message.timestamp}
        </div>
      </div>
    );
  };

  return (
    <div className="flex flex-col h-[600px] bg-white rounded-lg shadow-lg">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b bg-gray-50 rounded-t-lg">
        <h2 className="text-lg font-semibold text-gray-800">Voice Processing Chat</h2>
        <div className="flex items-center space-x-2">
          {isProcessing && <Loader className="h-4 w-4 animate-spin text-primary-600" />}
          {currentRecordingId && (
            <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">
              Processing...
            </span>
          )}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        {messages.length === 0 && (
          <div className="text-center text-gray-500 mt-8">
            <Mic className="h-12 w-12 mx-auto mb-4 text-gray-300" />
            <p>Upload or record an audio file to get started</p>
          </div>
        )}
        
        {messages.map(renderMessage)}
        
        {/* Streaming content */}
        {streamingContent && (
          <div className="chat-bubble chat-bubble-bot bg-green-50 border-l-4 border-green-500 pl-4">
            <div className="text-sm">
              {streamingContent}
              <span className="animate-pulse">|</span>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="border-t p-4 bg-gray-50 rounded-b-lg">
        <div className="space-y-3">
          {/* Title Input */}
          <input
            type="text"
            placeholder="Enter recording title..."
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="input-field"
            disabled={isProcessing}
          />
          
          {/* File/Recording Controls */}
          <div className="flex items-center space-x-2">
            <input
              ref={fileInputRef}
              type="file"
              accept="audio/*,.m4a,.mp3,.wav,.aac"
              onChange={handleFileSelect}
              className="hidden"
              disabled={isProcessing}
            />
            
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={isProcessing || isRecording}
              className="btn-secondary flex items-center space-x-2"
            >
              <Upload className="h-4 w-4" />
              <span>Upload File</span>
            </button>
            
            <button
              onClick={isRecording ? stopRecording : startRecording}
              disabled={isProcessing}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg font-medium transition-colors ${
                isRecording 
                  ? 'bg-red-600 hover:bg-red-700 text-white' 
                  : 'bg-green-600 hover:bg-green-700 text-white'
              }`}
            >
              {isRecording ? <MicOff className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
              <span>{isRecording ? 'Stop Recording' : 'Record'}</span>
            </button>
            
            <button
              onClick={uploadAndProcess}
              disabled={!selectedFile || !title.trim() || isProcessing}
              className="btn-primary flex items-center space-x-2 ml-auto"
            >
              {isProcessing ? (
                <Loader className="h-4 w-4 animate-spin" />
              ) : (
                <Send className="h-4 w-4" />
              )}
              <span>Process</span>
            </button>
          </div>
          
          {/* File Info */}
          {selectedFile && (
            <div className="text-sm text-gray-600 bg-blue-50 p-2 rounded">
              📁 Ready: {selectedFile.name || 'Recorded audio'} 
              ({selectedFile.size ? (selectedFile.size / 1024 / 1024).toFixed(2) + ' MB' : 'Recording'})
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;
