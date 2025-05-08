import React, { useState } from 'react';
import { FileItem } from './mockData';
import {
  FileIcon,
  FileImageIcon,
  FileTextIcon,
  FileSpreadsheetIcon,
  FileVideoIcon,
  FileAudioIcon,
  ChevronDownIcon,
  ChevronUpIcon
} from 'lucide-react';

interface FileListProps {
  files: FileItem[];
  selectedFiles: string[];
  onToggleSelect: (fileId: string) => void;
  onToggleSelectAll: () => void;
  onRename: (fileId: string, newName: string) => void;
}

export function FileList({
  files,
  selectedFiles,
  onToggleSelect,
  onToggleSelectAll,
  onRename
}: FileListProps) {
  const [sortBy, setSortBy] = useState<'name' | 'lastModified'>('name');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');
  const [editingFileId, setEditingFileId] = useState<string | null>(null);
  const [editingFileName, setEditingFileName] = useState('');

  const handleSort = (column: 'name' | 'lastModified') => {
    if (sortBy === column) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(column);
      setSortDirection('asc');
    }
  };

  const sortedFiles = [...files].sort((a, b) => {
    if (sortBy === 'name') {
      return sortDirection === 'asc' ? a.name.localeCompare(b.name) : b.name.localeCompare(a.name);
    } else {
      return sortDirection === 'asc'
        ? a.lastModified.getTime() - b.lastModified.getTime()
        : b.lastModified.getTime() - a.lastModified.getTime();
    }
  });

  const getFileIcon = (type: string) => {
    if (type.includes('image')) return <FileImageIcon className="w-5 h-5 text-blue-500" />;
    if (type.includes('pdf')) return <div className="w-5 h-5 text-red-500" />;
    if (type.includes('spreadsheet') || type.includes('csv') || type.includes('excel'))
      return <FileSpreadsheetIcon className="w-5 h-5 text-green-500" />;
    if (type.includes('presentation')) return <div className="w-5 h-5 text-orange-500" />;
    if (type.includes('document') || type.includes('word'))
      return <FileTextIcon className="w-5 h-5 text-indigo-500" />;
    if (type.includes('video')) return <FileVideoIcon className="w-5 h-5 text-purple-500" />;
    if (type.includes('audio')) return <FileAudioIcon className="w-5 h-5 text-pink-500" />;
    return <FileIcon className="w-5 h-5 text-gray-500" />;
  };

  const handleRenameClick = (file: FileItem) => {
    setEditingFileId(file.id);
    setEditingFileName(file.name);
  };

  const handleRenameSubmit = (fileId: string) => {
    if (editingFileName.trim()) {
      onRename(fileId, editingFileName.trim());
    }
    setEditingFileId(null);
  };

  const handleRenameKeyDown = (e: React.KeyboardEvent, fileId: string) => {
    if (e.key === 'Enter') {
      handleRenameSubmit(fileId);
    } else if (e.key === 'Escape') {
      setEditingFileId(null);
    }
  };

  if (files.length === 0) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center bg-white rounded-lg border border-gray-200 p-8">
        <FileIcon className="w-16 h-16 text-gray-300 mb-4" />
        <h3 className="text-lg font-medium text-gray-900">No files found</h3>
        <p className="text-gray-500">Upload files to see them here</p>
      </div>
    );
  }

  return (
    <div className="flex-1 bg-white rounded-lg border border-gray-200 overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full table-fixed">
          <thead className="bg-gray-50 text-xs text-gray-500 uppercase tracking-wider">
            <tr>
              <th className="w-12 px-4 py-3">
                <input
                  type="checkbox"
                  checked={selectedFiles.length === files.length && files.length > 0}
                  onChange={onToggleSelectAll}
                  className="w-4 h-4 appearance-none bg-white border border-gray-300 rounded checked:bg-indigo-600 checked:border-indigo-600 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </th>
              <th className="w-7/12 px-4 py-3 text-left">Name</th>
              <th className="w-5/12 px-4 py-3 text-right pr-8">Uploaded</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {files.length === 0 ? (
              <tr>
                <td colSpan={3} className="text-center py-6 text-gray-400">
                  No matching files found.
                </td>
              </tr>
            ) : (
              files.map((file) => (
                <tr
                  key={file.id}
                  className={`hover:bg-gray-50 ${
                    selectedFiles.includes(file.id) ? 'bg-indigo-50' : ''
                  }`}
                >
                  <td className="px-4 py-3">
                    <input
                      type="checkbox"
                      checked={selectedFiles.includes(file.id)}
                      onChange={() => onToggleSelect(file.id)}
                      className="w-4 h-4 appearance-none bg-white border border-gray-300 rounded checked:bg-indigo-600 checked:border-indigo-600 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center">
                      {getFileIcon(file.type)}
                      {editingFileId === file.id ? (
                        <input
                          type="text"
                          value={editingFileName}
                          onChange={(e) => setEditingFileName(e.target.value)}
                          onBlur={() => handleRenameSubmit(file.id)}
                          onKeyDown={(e) => handleRenameKeyDown(e, file.id)}
                          className="ml-3 px-2 py-1 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                          autoFocus
                        />
                      ) : (
                        <span className="ml-3 truncate text-black">{file.name}</span>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-500 text-right pr-8">
                    {file.lastModified.toLocaleDateString()}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}