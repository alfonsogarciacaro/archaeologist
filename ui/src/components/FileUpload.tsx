import React, { useState, useRef, useCallback } from 'react';
import { apiClient } from '../utils/apiClient';
import './FileUpload.css';

interface FileUploadProps {
  projectId: number;
  onFilesUploaded?: () => void;
  onClose?: () => void;
}

interface UploadResponse {
  success: boolean;
  message: string;
  sources: Array<{
    id: number;
    original_filename: string;
    file_size: number;
    content_type: string;
  }>;
  total_files: number;
  processed_files: number;
  skipped_files: number;
}

const FileUpload: React.FC<FileUploadProps> = ({ projectId, onFilesUploaded, onClose }) => {
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState<UploadResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [metadata, setMetadata] = useState('');
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFiles(Array.from(e.dataTransfer.files));
    }
  }, []);

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFiles(Array.from(e.target.files));
    }
  };

  const handleFiles = (files: File[]) => {
    // TODO: Validate later if needed
    const { valid, invalid } = { valid: files, invalid: [] };

    if (invalid.length > 0) {
      setError(`The following files are not supported: ${invalid.join(', ')}. Supported formats: text files (.txt, .py, .js, etc.) and zip files.`);
      return;
    }

    if (valid.length === 0) {
      setError('No valid files to upload. Please upload text files or zip files containing text files.');
      return;
    }

    setError(null);
    setSelectedFiles(valid);
  };

  const handleUpload = async () => {
    if (selectedFiles.length === 0) {
      setError('Please select files to upload.');
      return;
    }

    setUploading(true);
    setError(null);
    setUploadProgress(null);

    try {
      const metadataToUpload = metadata.trim() || null;
      const response: UploadResponse = await apiClient.uploadProjectFiles(projectId, selectedFiles, metadataToUpload);
      setUploadProgress(response);

      if (response.success && onFilesUploaded) {
        onFilesUploaded();
      }
    } catch (err: any) {
      setError(err.message || 'Failed to upload files. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  const openFileDialog = () => {
    fileInputRef.current?.click();
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const resetUpload = () => {
    setUploadProgress(null);
    setError(null);
    setMetadata('');
    setSelectedFiles([]);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="file-upload">
      {uploadProgress ? (
        <div className="upload-results">
          <div className="results-header">
            <h3>Upload Complete</h3>
            <button className="close-btn" onClick={onClose} aria-label="Close">
              ×
            </button>
          </div>

          <div className="upload-summary">
            <p><strong>{uploadProgress.message}</strong></p>
            <div className="stats">
              <span>Total files: {uploadProgress.total_files}</span>
              <span>Processed: {uploadProgress.processed_files}</span>
              <span>Skipped: {uploadProgress.skipped_files}</span>
            </div>
          </div>

          {uploadProgress.sources.length > 0 && (
            <div className="uploaded-files">
              <h4>Uploaded Files:</h4>
              <ul className="file-list">
                {uploadProgress.sources.map((source) => (
                  <li key={source.id} className="file-item">
                    <span className="filename">{source.original_filename}</span>
                    <div className="file-details">
                      <span className="size">{formatFileSize(source.file_size)}</span>
                      <span className="type">{source.content_type}</span>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="results-actions">
            <button className="btn btn-primary" onClick={resetUpload}>
              Upload More Files
            </button>
            {onClose && (
              <button className="btn btn-secondary" onClick={onClose}>
                Done
              </button>
            )}
          </div>
        </div>
      ) : (
        <>
          {onClose && (
            <div className="upload-header">
              <h3>Upload Source Files</h3>
              <button className="close-btn" onClick={onClose} aria-label="Close">
                ×
              </button>
            </div>
          )}

          <div
            className={`drag-drop-area ${dragActive ? 'active' : ''} ${uploading ? 'uploading' : ''}`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            onClick={!uploading ? openFileDialog : undefined}
          >
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".txt,.py,.js,.ts,.jsx,.tsx,.html,.css,.json,.xml,.yaml,.yml,.md,.sql,.sh,.bash,.zsh,.cfg,.conf,.ini,.toml,.env,.log,.csv,.tsv,.zip"
              onChange={handleFileInput}
              disabled={uploading}
            />

            {uploading ? (
              <div className="upload-spinner">
                <div className="spinner"></div>
                <p>Processing files...</p>
              </div>
            ) : selectedFiles.length > 0 ? (
              <div className="drag-drop-content">
                <div className="upload-icon">✅</div>
                <h4>{selectedFiles.length} File{selectedFiles.length !== 1 ? 's' : ''} Selected</h4>
                <p>Click to add more files or drag & drop additional files</p>
                <p className="supported-formats">
                  Ready to upload with metadata below
                </p>
              </div>
            ) : (
              <div className="drag-drop-content">
                <div className="upload-icon">📁</div>
                <h4>Drag & Drop Files Here</h4>
                <p>or click to browse</p>
                <p className="supported-formats">
                  Supports: Text files (.txt, .py, .js, .html, .css, .json, .xml, .yaml, .md, etc.) and ZIP files containing text files
                </p>
              </div>
            )}
          </div>

          {selectedFiles.length > 0 && (
            <div className="file-preview-section">
              <h4>Selected Files:</h4>
              <ul className="file-list">
                {selectedFiles.map((file, index) => (
                  <li key={index} className="file-item">
                    <span className="filename">{file.name}</span>
                    <div className="file-details">
                      <span className="size">{formatFileSize(file.size)}</span>
                      <button
                        className="remove-file-btn"
                        onClick={() => {
                          setSelectedFiles(selectedFiles.filter((_, i) => i !== index));
                        }}
                        title="Remove file"
                      >
                        ×
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="metadata-section">
            <label htmlFor="metadata-input" className="metadata-label">
              Optional Metadata
            </label>
            <textarea
              id="metadata-input"
              value={metadata}
              onChange={(e) => setMetadata(e.target.value)}
              placeholder="Add optional metadata for these files (e.g., purpose, version, environment, etc.)"
              className="metadata-input"
              rows={3}
              disabled={uploading}
              maxLength={1000}
            />
            <div className="metadata-char-count">
              {metadata.length}/1000 characters
            </div>
          </div>

          {error && (
            <div className="upload-error">
              <span className="error-icon">⚠️</span>
              {error}
            </div>
          )}

          <div className="upload-actions">
            {selectedFiles.length > 0 && (
              <button
                className="btn btn-primary"
                onClick={handleUpload}
                disabled={uploading}
              >
                {uploading ? (
                  <>
                    <div className="btn-spinner"></div>
                    Uploading...
                  </>
                ) : (
                  `Upload ${selectedFiles.length} File${selectedFiles.length !== 1 ? 's' : ''}`
                )}
              </button>
            )}
            {onClose && (
              <button className="btn btn-secondary" onClick={onClose} disabled={uploading}>
                Cancel
              </button>
            )}
          </div>
        </>
      )}
    </div>
  );
};

export default FileUpload;