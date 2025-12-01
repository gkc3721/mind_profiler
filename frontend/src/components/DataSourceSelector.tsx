import React, { useState } from 'react';

export type DataSourceType = 'folder' | 'upload';

interface DataSourceSelectorProps {
  onSelect: (type: DataSourceType, value: File[]) => void;
}

export const DataSourceSelector: React.FC<DataSourceSelectorProps> = ({ onSelect }) => {
  const [activeTab, setActiveTab] = useState<DataSourceType>('folder');
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [singleFile, setSingleFile] = useState<File | null>(null);

  const handleFolderSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const csvFiles = Array.from(e.target.files).filter(f => 
        f.name.toLowerCase().endsWith('.csv')
      );
      setSelectedFiles(csvFiles);
    }
  };

  const handleSingleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] || null;
    setSingleFile(file);
  };

  const handleSubmit = () => {
    if (activeTab === 'folder' && selectedFiles.length > 0) {
      onSelect('folder', selectedFiles);
    } else if (activeTab === 'upload' && singleFile) {
      onSelect('upload', [singleFile]);
    }
  };

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const totalSize = selectedFiles.reduce((acc, f) => acc + f.size, 0);

  return (
    <div className="rounded-2xl bg-slate-900 border border-slate-800 p-6 shadow-xl">
      <div className="flex items-start gap-3 mb-6">
        <div className="text-sky-400 mt-1">
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
          </svg>
        </div>
        <div>
          <h2 className="text-2xl font-semibold tracking-tight text-gray-100">Data Source</h2>
          <p className="text-sm text-gray-400 mt-1">Choose where to load your EEG data from</p>
        </div>
      </div>

      <div className="flex gap-2 mb-6">
        <button
          onClick={() => setActiveTab('folder')}
          className={`flex-1 px-4 py-2.5 rounded-xl font-medium transition-all duration-200 ${
            activeTab === 'folder'
              ? 'bg-gradient-to-r from-sky-600 to-teal-500 text-white shadow-lg shadow-sky-900/50'
              : 'bg-slate-800 text-gray-400 hover:text-gray-200 hover:bg-slate-700'
          }`}
        >
          Process Folder
        </button>
        <button
          onClick={() => setActiveTab('upload')}
          className={`flex-1 px-4 py-2.5 rounded-xl font-medium transition-all duration-200 ${
            activeTab === 'upload'
              ? 'bg-gradient-to-r from-sky-600 to-teal-500 text-white shadow-lg shadow-sky-900/50'
              : 'bg-slate-800 text-gray-400 hover:text-gray-200 hover:bg-slate-700'
          }`}
        >
          Upload CSV
        </button>
      </div>

      {activeTab === 'folder' && (
        <div className="space-y-4">
          <input
            type="file"
            // @ts-ignore - webkitdirectory is not in TypeScript types
            webkitdirectory="true"
            multiple
            onChange={handleFolderSelect}
            className="hidden"
            id="folder-upload"
          />
          <label
            htmlFor="folder-upload"
            className="block w-full px-6 py-8 bg-slate-800 border-2 border-dashed border-slate-600 rounded-xl text-center cursor-pointer hover:border-sky-500 hover:bg-slate-700/50 transition-all"
          >
            <svg className="w-12 h-12 mx-auto mb-3 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
            </svg>
            <p className="text-sm font-medium text-gray-300">Click to select folder</p>
            <p className="text-xs text-gray-500 mt-1">All CSV files will be uploaded and processed</p>
          </label>
          
          {selectedFiles.length > 0 && (
            <div className="p-4 bg-teal-900/20 border border-teal-700 rounded-xl">
              <div className="flex items-center gap-2 mb-2">
                <svg className="w-5 h-5 text-teal-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span className="font-medium text-teal-400">
                  {selectedFiles.length} CSV file{selectedFiles.length !== 1 ? 's' : ''} selected
                </span>
              </div>
              <p className="text-sm text-gray-400">Total size: {formatSize(totalSize)}</p>
              <div className="mt-2 text-xs text-gray-500 space-y-0.5">
                {selectedFiles.slice(0, 5).map((f, idx) => (
                  <div key={idx}>• {f.name}</div>
                ))}
                {selectedFiles.length > 5 && (
                  <div className="text-teal-400">...and {selectedFiles.length - 5} more files</div>
                )}
              </div>
            </div>
          )}
          
          <button
            onClick={handleSubmit}
            disabled={selectedFiles.length === 0}
            className="w-full px-5 py-2.5 rounded-xl font-medium bg-gradient-to-r from-sky-600 to-teal-500 hover:from-sky-500 hover:to-teal-400 text-white shadow-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:from-sky-600 disabled:hover:to-teal-500"
          >
            Use Folder ({selectedFiles.length} files)
          </button>
        </div>
      )}

      {activeTab === 'upload' && (
        <div className="space-y-4">
          <input
            type="file"
            accept=".csv"
            onChange={handleSingleFileSelect}
            className="hidden"
            id="file-upload"
          />
          <label
            htmlFor="file-upload"
            className="block w-full px-6 py-8 bg-slate-800 border-2 border-dashed border-slate-600 rounded-xl text-center cursor-pointer hover:border-sky-500 hover:bg-slate-700/50 transition-all"
          >
            <svg className="w-12 h-12 mx-auto mb-3 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            <p className="text-sm font-medium text-gray-300">Click to select CSV file</p>
            <p className="text-xs text-gray-500 mt-1">Upload a single CSV file for analysis</p>
          </label>
          
          {singleFile && (
            <div className="p-4 bg-teal-900/20 border border-teal-700 rounded-xl">
              <div className="flex items-center gap-2">
                <svg className="w-5 h-5 text-teal-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span className="font-medium text-teal-400">{singleFile.name}</span>
              </div>
              <p className="text-sm text-gray-400 mt-1">{formatSize(singleFile.size)}</p>
            </div>
          )}
          
          <button
            onClick={handleSubmit}
            disabled={!singleFile}
            className="w-full px-5 py-2.5 rounded-xl font-medium bg-gradient-to-r from-sky-600 to-teal-500 hover:from-sky-500 hover:to-teal-400 text-white shadow-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:from-sky-600 disabled:hover:to-teal-500"
          >
            Use Upload
          </button>
        </div>
      )}
    </div>
  );
};
