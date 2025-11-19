import React, { useState, useCallback } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  Typography,
  LinearProgress,
  Alert,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  IconButton,
  Chip,
  Divider,
} from '@mui/material';
import {
  CloudUpload,
  Description,
  Delete,
  CheckCircle,
  Error as ErrorIcon,
} from '@mui/icons-material';
import { api } from '../api/client';
import SampleValidation from './SampleValidation';

interface FileUploadProps {
  runId: string;
  onUploadComplete?: () => void;
}

interface FileWithStatus {
  file: File;
  status: 'pending' | 'uploading' | 'success' | 'error';
  progress: number;
  error?: string;
}

const FileUpload: React.FC<FileUploadProps> = ({ runId, onUploadComplete }) => {
  const [files, setFiles] = useState<FileWithStatus[]>([]);
  const [dragOver, setDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);

  const allowedExtensions = ['.fq.gz', '.fastq.gz', '.fa', '.fasta', '.gtf', '.csv', '.tsv'];
  
  // File type descriptions for user guidance
  const fileTypeGuide = {
    fastq: {
      label: 'FASTQ Files',
      description: 'Raw sequencing reads (.fq.gz or .fastq.gz). Upload both R1 and R2 for paired-end data.',
      extensions: ['.fq.gz', '.fastq.gz']
    },
    genome: {
      label: 'Reference Genome',
      description: 'FASTA file (.fa or .fasta) with genome sequence. Use same version as GTF file.',
      extensions: ['.fa', '.fasta']
    },
    annotation: {
      label: 'Gene Annotation',
      description: 'GTF file with gene coordinates. Must match genome version (hg38, mm10, etc).',
      extensions: ['.gtf']
    },
    metadata: {
      label: 'Sample Metadata',
      description: 'CSV file with sample information (required for DESeq2). Must have columns for sample name and condition.',
      extensions: ['.csv', '.tsv']
    }
  };

  const isValidFile = (file: File): boolean => {
    const filename = file.name.toLowerCase();
    return allowedExtensions.some(ext => filename.endsWith(ext));
  };

  const getFileType = (filename: string): string => {
    const lower = filename.toLowerCase();
    if (lower.endsWith('.fq.gz') || lower.endsWith('.fastq.gz')) return 'FASTQ';
    if (lower.endsWith('.fa') || lower.endsWith('.fasta')) return 'FASTA';
    if (lower.endsWith('.gtf')) return 'GTF';
    if (lower.endsWith('.csv') || lower.endsWith('.tsv')) return 'Metadata';
    return 'Unknown';
  };

  const handleFiles = useCallback((newFiles: FileList) => {
    const fileArray = Array.from(newFiles);
    const validFiles: FileWithStatus[] = [];
    const invalidFiles: string[] = [];
    const oversizedFiles: string[] = [];
    const maxSize = 1000 * 1024 * 1024; // 1GB limit

    fileArray.forEach(file => {
      if (!isValidFile(file)) {
        invalidFiles.push(file.name);
      } else if (file.size > maxSize) {
        oversizedFiles.push(`${file.name} (${Math.round(file.size / 1024 / 1024)}MB)`);
      } else {
        validFiles.push({
          file,
          status: 'pending',
          progress: 0,
        });
      }
    });

    if (invalidFiles.length > 0) {
      alert(`Invalid file types: ${invalidFiles.join(', ')}\nAllowed: ${allowedExtensions.join(', ')}`);
    }

    if (oversizedFiles.length > 0) {
      alert(`Files too large (max 1GB): ${oversizedFiles.join(', ')}`);
    }

    setFiles(prev => [...prev, ...validFiles]);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    
    if (e.dataTransfer.files) {
      handleFiles(e.dataTransfer.files);
    }
  }, [handleFiles]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
  }, []);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      handleFiles(e.target.files);
    }
  }, [handleFiles]);

  const removeFile = (index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
  };

  const uploadFiles = async () => {
    if (files.length === 0) return;

    setUploading(true);

    try {
      const filesToUpload = files.filter(f => f.status === 'pending');
      
      // Update all files to uploading status
      setFiles(prev => prev.map(f => 
        f.status === 'pending' ? { ...f, status: 'uploading' as const } : f
      ));

      // Create FormData with all files
      const formData = new FormData();
      filesToUpload.forEach(({ file }) => {
        formData.append('files', file);
      });

      // Upload all files at once
      const response = await api.uploadFiles(runId, formData);

      // Mark all as successful
      setFiles(prev => prev.map(f => 
        f.status === 'uploading' ? { ...f, status: 'success' as const, progress: 100 } : f
      ));

      if (onUploadComplete) {
        onUploadComplete();
      }

    } catch (error) {
      console.error('Upload failed:', error);
      
      // Mark all uploading files as failed
      setFiles(prev => prev.map(f => 
        f.status === 'uploading' 
          ? { ...f, status: 'error' as const, error: 'Upload failed' }
          : f
      ));
    } finally {
      setUploading(false);
    }
  };

  const clearCompleted = () => {
    setFiles(prev => prev.filter(f => f.status !== 'success'));
  };

  const getStatusIcon = (status: FileWithStatus['status']) => {
    switch (status) {
      case 'success': return <CheckCircle color="success" />;
      case 'error': return <ErrorIcon color="error" />;
      case 'uploading': return <LinearProgress variant="indeterminate" />;
      default: return <Description />;
    }
  };

  return (
    <Box>
      {/* File Upload Guide */}
      <Alert severity="info" sx={{ mb: 3 }}>
        <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 'bold' }}>
          📚 What to Upload
        </Typography>
        <Box sx={{ ml: 2 }}>
          <Typography variant="body2" paragraph>
            <strong>Required for all runs:</strong>
            <ul style={{ margin: '8px 0', paddingLeft: 20 }}>
              <li>FASTQ files (.fq.gz or .fastq.gz) - Your raw sequencing data. Upload both R1 and R2 for paired-end.</li>
              <li>Reference genome (.fa or .fasta) - DNA sequence for alignment</li>
              <li>Gene annotation (.gtf) - Gene coordinates and features</li>
            </ul>
          </Typography>
          <Typography variant="body2">
            <strong>Required for DESeq2 analysis:</strong>
            <ul style={{ margin: '8px 0', paddingLeft: 20 }}>
              <li>Metadata (.csv or .tsv) - Sample information with condition/group assignments</li>
            </ul>
          </Typography>
        </Box>
      </Alert>

      {/* Drop Zone */}
      <Card 
        sx={{ 
          mb: 2, 
          border: dragOver ? '2px dashed #1976d2' : '2px dashed #ccc',
          backgroundColor: dragOver ? 'rgba(25, 118, 210, 0.08)' : 'transparent',
          cursor: 'pointer',
        }}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
      >
        <CardContent sx={{ textAlign: 'center', py: 4 }}>
          <CloudUpload sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" gutterBottom>
            Drop files here or click to browse
          </Typography>
          <Typography variant="body2" color="text.secondary" mb={2}>
            Supported: {allowedExtensions.join(', ')}
          </Typography>
          <input
            type="file"
            multiple
            accept={allowedExtensions.join(',')}
            onChange={handleFileSelect}
            style={{ display: 'none' }}
            id="file-input"
          />
          <label htmlFor="file-input">
            <Button variant="outlined" component="span">
              Browse Files
            </Button>
          </label>
        </CardContent>
      </Card>

      {/* File List */}
      {files.length > 0 && (
        <Card sx={{ mb: 2 }}>
          <CardContent>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">
                Files ({files.length})
              </Typography>
              <Box>
                <Button 
                  size="small" 
                  onClick={clearCompleted}
                  disabled={!files.some(f => f.status === 'success')}
                  sx={{ mr: 1 }}
                >
                  Clear Completed
                </Button>
                <Button
                  variant="contained"
                  onClick={uploadFiles}
                  disabled={uploading || files.length === 0 || !files.some(f => f.status === 'pending')}
                  startIcon={<CloudUpload />}
                >
                  Upload {files.filter(f => f.status === 'pending').length} Files
                </Button>
              </Box>
            </Box>

            <List dense>
              {files.map((fileWithStatus, index) => (
                <ListItem key={index} divider>
                  <ListItemIcon>
                    {getStatusIcon(fileWithStatus.status)}
                  </ListItemIcon>
                  <ListItemText
                    primary={fileWithStatus.file.name}
                    secondary={
                      <Box display="flex" alignItems="center" gap={1}>
                        <Chip
                          label={getFileType(fileWithStatus.file.name)}
                          size="small"
                          variant="outlined"
                        />
                        <Typography variant="caption">
                          {(fileWithStatus.file.size / 1024 / 1024).toFixed(1)} MB
                        </Typography>
                        {fileWithStatus.error && (
                          <Typography variant="caption" color="error">
                            {fileWithStatus.error}
                          </Typography>
                        )}
                      </Box>
                    }
                  />
                  {fileWithStatus.status === 'pending' && (
                    <IconButton
                      edge="end"
                      size="small"
                      onClick={() => removeFile(index)}
                    >
                      <Delete />
                    </IconButton>
                  )}
                </ListItem>
              ))}
            </List>

            {uploading && (
              <Box mt={2}>
                <LinearProgress />
                <Typography variant="caption" color="text.secondary">
                  Uploading files...
                </Typography>
              </Box>
            )}
          </CardContent>
        </Card>
      )}

      {/* Sample Validation */}
      <Divider sx={{ my: 3 }} />
      <SampleValidation runId={runId} />
    </Box>
  );
};

export default FileUpload;