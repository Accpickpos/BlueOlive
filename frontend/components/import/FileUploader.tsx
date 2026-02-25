'use client';

import { Upload, FileText, AlertCircle } from 'lucide-react';

interface FileUploaderProps {
  file: File | null;
  onFileChange: (file: File | null) => void;
  onAnalyze: () => void;
  loading: boolean;
  dataTypeLabel: string;
  acceptedFormats?: string;
}

export function FileUploader({ 
  file, 
  onFileChange, 
  onAnalyze, 
  loading, 
  dataTypeLabel,
  acceptedFormats = '.csv,.xlsx,.xls' 
}: FileUploaderProps) {
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0] ?? null;
    onFileChange(selectedFile);
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold mb-2">Upload File</h2>
        <p className="text-gray-600 text-sm">
          Upload your {dataTypeLabel} data file for import
        </p>
      </div>

      {/* File input */}
      <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-indigo-400 transition-colors">
        <input
          type="file"
          accept={acceptedFormats}
          onChange={handleFileChange}
          className="hidden"
          id="file-upload"
        />
        
        <label htmlFor="file-upload" className="cursor-pointer">
          {file ? (
            <div className="flex flex-col items-center">
              <FileText className="w-12 h-12 text-indigo-600 mb-2" />
              <p className="font-medium text-gray-900">{file.name}</p>
              <p className="text-sm text-gray-500">
                {(file.size / 1024).toFixed(1)} KB
              </p>
              <p className="text-xs text-gray-400 mt-2">Click to change file</p>
            </div>
          ) : (
            <div className="flex flex-col items-center">
              <Upload className="w-12 h-12 text-gray-400 mb-2" />
              <p className="font-medium text-gray-700">
                Click to upload or drag and drop
              </p>
              <p className="text-sm text-gray-500 mt-1">
                CSV, XLSX or XLS files
              </p>
            </div>
          )}
        </label>
      </div>

      {/* File info */}
      {file && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-center gap-2">
            <FileText className="w-5 h-5 text-green-600" />
            <span className="text-green-800 font-medium">
              File selected: {file.name}
            </span>
          </div>
        </div>
      )}

      {/* Analyze button */}
      <div className="flex gap-4">
        <button
          onClick={onAnalyze}
          disabled={!file || loading}
          className={`flex-1 py-3 px-6 rounded-lg font-medium transition-colors ${
            !file || loading
              ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
              : 'bg-indigo-600 text-white hover:bg-indigo-700'
          }`}
        >
          {loading ? 'Analyzing...' : 'Analyze File'}
        </button>
      </div>

      {/* Format help */}
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <div className="flex items-start gap-2">
          <AlertCircle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-yellow-800">
            <p className="font-medium">File Format Requirements</p>
            <ul className="list-disc list-inside mt-1 space-y-1">
              <li>First row should contain column headers</li>
              <li>UTF-8 encoding recommended for special characters</li>
              <li>Maximum file size: 10MB</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
