import React, { useState, useRef } from 'react';
import { Upload, X, FileText, AlertCircle, Loader2 } from 'lucide-react';
import { uploadDocument } from '../../api/client';
import type { DocumentItem } from '../../types';

interface UploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUploadSuccess: (doc: DocumentItem) => void;
}

export const UploadModal: React.FC<UploadModalProps> = ({
  isOpen,
  onClose,
  onUploadSuccess,
}) => {
  const [dragActive, setDragActive] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStep, setUploadStep] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  if (!isOpen) return null;

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const validateAndSetFile = (f: File) => {
    setError(null);
    const validExtensions = ['.pdf', '.docx'];
    const hasValidExt = validExtensions.some((ext) => f.name.toLowerCase().endsWith(ext));
    if (!hasValidExt) {
      setError('Please upload a PDF (.pdf) or Word document (.docx).');
      return;
    }
    if (f.size > 15 * 1024 * 1024) {
      setError('File size exceeds the 15 MB limit.');
      return;
    }
    setFile(f);
  };

  const handleUpload = async () => {
    if (!file || isUploading) return;
    setIsUploading(true);
    setError(null);
    setUploadStep('Validating magic bytes & extracting text...');

    try {
      setTimeout(() => setUploadStep('Detecting clause boundaries & chunking...'), 600);
      setTimeout(() => setUploadStep('Indexing embeddings in ChromaDB...'), 1200);

      const doc = await uploadDocument(file);
      setUploadStep('Ready!');
      onUploadSuccess(doc);
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to process document');
    } finally {
      setIsUploading(false);
      setUploadStep('');
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-fadeIn"
      role="dialog"
      aria-modal="true"
      aria-labelledby="upload-modal-title"
      onKeyDown={(e) => e.key === 'Escape' && !isUploading && onClose()}
    >
      <div className="relative w-full max-w-md bg-white rounded-2xl shadow-xl border border-slate-200 overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-brand-50 text-brand-600">
              <Upload className="w-5 h-5" aria-hidden="true" />
            </div>
            <h2 id="upload-modal-title" className="text-sm font-bold text-slate-900">
              Upload Residential Lease
            </h2>
          </div>

          <button
            onClick={onClose}
            disabled={isUploading}
            className="p-1 text-slate-400 hover:text-slate-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand-500"
            aria-label="Close upload dialog"
          >
            <X className="w-5 h-5" aria-hidden="true" />
          </button>
        </div>

        {/* Body */}
        <div className="p-5 space-y-4">
          {error && (
            <div className="p-3 rounded-xl bg-red-50 border border-red-200 text-red-700 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" aria-hidden="true" />
              <span>{error}</span>
            </div>
          )}

          {/* Drag & Drop Zone */}
          <div
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            onClick={() => inputRef.current?.click()}
            className={`border-2 border-dashed rounded-2xl p-6 text-center cursor-pointer transition-all ${
              dragActive
                ? 'border-brand-500 bg-brand-50/50'
                : 'border-slate-300 hover:border-brand-400 bg-slate-50/50'
            }`}
          >
            <input
              ref={inputRef}
              type="file"
              accept=".pdf,.docx"
              onChange={handleChange}
              className="hidden"
              aria-label="File upload input"
            />

            <div className="w-12 h-12 rounded-full bg-brand-100 text-brand-600 flex items-center justify-center mx-auto mb-3">
              <FileText className="w-6 h-6" aria-hidden="true" />
            </div>

            {file ? (
              <div>
                <p className="text-xs font-bold text-slate-800">{file.name}</p>
                <p className="text-[11px] text-slate-500 mt-0.5">
                  {(file.size / (1024 * 1024)).toFixed(2)} MB &bull; Click or drag to replace
                </p>
              </div>
            ) : (
              <div>
                <p className="text-xs font-bold text-slate-800">
                  Drag &amp; drop your lease here, or <span className="text-brand-600 underline">browse</span>
                </p>
                <p className="text-[11px] text-slate-500 mt-1">
                  Supported formats: PDF (.pdf), Word (.docx) &bull; Max 15 MB
                </p>
              </div>
            )}
          </div>

          {/* Upload Progress Tracker */}
          {isUploading && (
            <div className="p-3.5 rounded-xl bg-brand-50 border border-brand-200 text-brand-900 space-y-2 text-xs">
              <div className="flex items-center gap-2 font-bold">
                <Loader2 className="w-4 h-4 animate-spin text-brand-600" aria-hidden="true" />
                <span>Processing Lease Pipeline</span>
              </div>
              <p className="text-[11px] text-brand-700 pl-6">{uploadStep}</p>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex items-center justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              disabled={isUploading}
              className="px-4 py-2 text-xs font-semibold text-slate-600 hover:text-slate-800 focus:outline-none"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleUpload}
              disabled={!file || isUploading}
              className="inline-flex items-center gap-2 px-5 py-2 text-xs font-bold bg-brand-600 hover:bg-brand-700 text-white rounded-xl shadow-sm disabled:opacity-40 focus:outline-none focus:ring-2 focus:ring-brand-500 transition-colors"
            >
              {isUploading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />
                  <span>Processing...</span>
                </>
              ) : (
                <>
                  <Upload className="w-4 h-4" aria-hidden="true" />
                  <span>Start Evidence Analysis</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
