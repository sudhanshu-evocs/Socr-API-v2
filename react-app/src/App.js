import React, { useState, useEffect, useMemo, useRef } from 'react';
import axios from 'axios';
import { Autocomplete, TextField } from '@mui/material';
import './App.css';

// SVG Icon Components
const UploadIcon = () => (
  <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
    <polyline points="17 8 12 3 7 8"></polyline>
    <line x1="12" y1="3" x2="12" y2="15"></line>
  </svg>
);

const FileIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
    <polyline points="14 2 14 8 20 8"></polyline>
  </svg>
);

const CheckIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="20 6 9 17 4 12"></polyline>
  </svg>
);

const AlertIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
    <line x1="12" y1="9" x2="12" y2="13"></line>
    <line x1="12" y1="17" x2="12.01" y2="17"></line>
  </svg>
);

const CodeIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="16 18 22 12 16 6"></polyline>
    <polyline points="8 6 2 12 8 18"></polyline>
  </svg>
);

const DownloadIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
    <polyline points="7 10 12 15 17 10"></polyline>
    <line x1="12" y1="15" x2="12" y2="3"></line>
  </svg>
);

const CopyIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
    <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
  </svg>
);

const RemoveIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <line x1="18" y1="6" x2="6" y2="18"></line>
    <line x1="6" y1="6" x2="18" y2="18"></line>
  </svg>
);

const MetadataValidatorIcon = ({ size = 22 }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="1.9"
    strokeLinecap="round"
    strokeLinejoin="round"
    aria-hidden="true"
  >
    <ellipse cx="10" cy="5" rx="6" ry="3"></ellipse>
    <path d="M4 5v5c0 1.7 2.7 3 6 3 1.1 0 2.1-.1 3-.4"></path>
    <path d="M4 10v5c0 1.7 2.7 3 6 3"></path>
    <circle cx="17" cy="16" r="4"></circle>
    <polyline points="15.4 16 16.6 17.2 18.8 14.8"></polyline>
  </svg>
);

const ShieldIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
    <polyline points="9 12 11 14 15 10"></polyline>
  </svg>
);

const EyeIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
    <circle cx="12" cy="12" r="3"></circle>
  </svg>
);

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

const normalizeStatus = (status, fallback = 'N/A') => {
  if (typeof status !== 'string') return fallback;
  const normalized = status.trim().toLowerCase();
  if (normalized === 'pass') return 'Pass';
  if (normalized === 'fdr') return 'FDR';
  if (normalized === 'fail') return 'Fail';
  return status;
};

const statusClassName = (status) => {
  const normalized = normalizeStatus(status).toLowerCase();
  return ['pass', 'fdr', 'fail'].includes(normalized) ? normalized : 'neutral';
};

const isImageFile = (file) => {
  if (!file) return false;
  if (typeof file === 'string') {
    return /\.(png|jpe?g|webp|gif|bmp|svg|tiff?)$/i.test(file);
  }
  if (typeof file === 'object') {
    const mimeType = file.type && typeof file.type === 'string' ? file.type : '';
    if (mimeType.toLowerCase().startsWith('image/')) return true;
    const name = file.name && typeof file.name === 'string' ? file.name : '';
    if (/\.(png|jpe?g|webp|gif|bmp|svg|tiff?)$/i.test(name)) return true;
  }
  return false;
};

function App() {
  const [fileName, setFileName] = useState('');
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [fileDetections, setFileDetections] = useState([]);
  const [batchResults, setBatchResults] = useState([]);
  const [activeBatchIndex, setActiveBatchIndex] = useState(0);
  const [responseMessage, setResponseMessage] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [templateNames, setTemplateNames] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState('');
  const [isDragOver, setIsDragOver] = useState(false);
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);
  const [viewMode, setViewMode] = useState('checklist'); // 'checklist' | 'preview' | 'rawText' | 'rawJson'
  const [categories, setCategories] = useState({ 'Bank Statements': [], 'Paystubs & Earnings': [] });
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [errorMessage, setErrorMessage] = useState('');
  const [detectingTemplate, setDetectingTemplate] = useState(false);
  const [templateDetection, setTemplateDetection] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [showHighlights, setShowHighlights] = useState(false);
  const [highlightedUrl, setHighlightedUrl] = useState(null);
  const [highlightLoading, setHighlightLoading] = useState(false);

  const [apiStatus, setApiStatus] = useState('checking');
  const detectionRequestRef = useRef(0);

  const currentFile = useMemo(() => {
    if (typeof fileName === 'object' && fileName) return fileName;
    if (selectedFiles[activeBatchIndex]) return selectedFiles[activeBatchIndex];
    if (selectedFiles[0]) return selectedFiles[0];
    return fileName;
  }, [fileName, selectedFiles, activeBatchIndex]);

  useEffect(() => {
    let url = null;
    if (currentFile && (currentFile instanceof Blob || typeof currentFile === 'object')) {
      try {
        url = URL.createObjectURL(currentFile);
        setPreviewUrl(url);
      } catch (e) {
        setPreviewUrl(null);
      }
    } else if (typeof currentFile === 'string' && currentFile.startsWith('blob:')) {
      setPreviewUrl(currentFile);
    } else {
      setPreviewUrl(null);
    }
    return () => {
      if (url && typeof URL.revokeObjectURL === 'function') {
        try { URL.revokeObjectURL(url); } catch (e) {}
      }
    };
  }, [currentFile]);

  useEffect(() => {
    setShowHighlights(false);
    if (highlightedUrl && typeof URL.revokeObjectURL === 'function') {
      try { URL.revokeObjectURL(highlightedUrl); } catch (e) {}
    }
    setHighlightedUrl(null);
  }, [currentFile]);

  useEffect(() => {
    const fetchTemplateNames = async () => {
      try {
        const [namesRes, catRes] = await Promise.all([
          axios.get(`${API_BASE_URL}/template_names`),
          axios.get(`${API_BASE_URL}/template_categories`).catch(() => null)
        ]);

        if (namesRes && Array.isArray(namesRes.data)) {
          setTemplateNames(namesRes.data);
          if (namesRes.data.length > 0 && !selectedTemplate) {
            setSelectedTemplate(namesRes.data[0]);
            setSearchTerm(namesRes.data[0]);
          }
        }

        if (catRes && catRes.data) {
          setCategories(catRes.data);
        }
        setApiStatus('ready');
      } catch (error) {
        console.error('Error fetching template names or categories:', error);
        setApiStatus('unavailable');
        setErrorMessage('Could not load validation templates. Check that the API is running, then refresh the page.');
      }
    };

    fetchTemplateNames();
  }, []);

  const filteredTemplates = useMemo(() => {
    if (selectedCategory === 'Bank Statements' && categories['Bank Statements']?.length > 0) {
      return categories['Bank Statements'];
    }
    if (selectedCategory === 'Paystubs & Earnings' && categories['Paystubs & Earnings']?.length > 0) {
      return categories['Paystubs & Earnings'];
    }
    return templateNames;
  }, [selectedCategory, categories, templateNames]);

  const docCategory = useMemo(() => {
    const t = selectedTemplate || searchTerm;
    if (!t) return 'Document Statement';
    if (selectedCategory === 'Bank Statements') return 'Bank Statement';
    if (selectedCategory === 'Paystubs & Earnings') return 'Paystub / Earning Statement';
    if (categories['Paystubs & Earnings']?.includes(t)) return 'Paystub / Earning Statement';
    if (categories['Bank Statements']?.includes(t)) return 'Bank Statement';
    if (/adp|gusto|paycom|paycor|paystub|earning|intuit|ceridian|paychex/i.test(t)) return 'Paystub / Earning Statement';
    return 'Bank Statement';
  }, [selectedTemplate, searchTerm, selectedCategory, categories]);

  const documentTypeForTemplate = (template, category = '') => {
    if (category === 'Paystubs & Earnings' || categories['Paystubs & Earnings']?.includes(template)) {
      return 'Paystub / Earning Statement';
    }
    return 'Bank Statement';
  };

  const batchTemplatesReady = selectedFiles.length <= 1
    ? Boolean(selectedTemplate || searchTerm)
    : fileDetections.length === selectedFiles.length && fileDetections.every((item) => Boolean(item.selected_template));

  const detectUploadedTemplate = async (file, requestId) => {
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(`${API_BASE_URL}/detect_template`, formData);
      if (detectionRequestRef.current !== requestId) return;

      const detection = response?.data || {};
      if (detection.auto_select && detection.template_name) {
        setSelectedTemplate(detection.template_name);
        setSearchTerm(detection.template_name);
        setSelectedCategory(detection.category || 'All');
        setTemplateDetection({ ...detection, status: 'detected' });
      } else {
        setTemplateDetection({ ...detection, status: 'review' });
      }
    } catch (error) {
      if (detectionRequestRef.current !== requestId) return;
      setTemplateDetection({
        status: 'error',
        reason: error.response?.data?.error || 'Automatic detection was unavailable. Select the template manually.'
      });
    } finally {
      if (detectionRequestRef.current === requestId) setDetectingTemplate(false);
    }
  };

  const detectBatchTemplates = async (files, requestId) => {
    const detections = await Promise.all(files.map(async (file) => {
      const formData = new FormData();
      formData.append('file', file);
      try {
        const response = await axios.post(`${API_BASE_URL}/detect_template`, formData);
        const detection = response?.data || {};
        return {
          file,
          ...detection,
          selected_template: detection.auto_select && detection.template_name ? detection.template_name : '',
          status: detection.auto_select && detection.template_name ? 'detected' : 'review'
        };
      } catch (error) {
        return {
          file,
          selected_template: '',
          status: 'error',
          reason: error.response?.data?.error || 'Automatic detection was unavailable.'
        };
      }
    }));
    if (detectionRequestRef.current !== requestId) return;
    setFileDetections(detections);
    setDetectingTemplate(false);
  };

  const updateBatchTemplate = (index, template) => {
    setFileDetections((current) => current.map((item, itemIndex) => {
      if (itemIndex !== index) return item;
      const category = categories['Paystubs & Earnings']?.includes(template) ? 'Paystubs & Earnings' : 'Bank Statements';
      return {
        ...item,
        selected_template: template,
        category,
        document_class: documentTypeForTemplate(template, category),
        status: template ? 'manual' : item.auto_select ? 'detected' : 'review'
      };
    }));
  };

  const selectFiles = (incomingFiles) => {
    const files = Array.from(incomingFiles || []);
    if (!files.length) return;
    const validFiles = files.filter((file) => {
      const isPdf = file.type === 'application/pdf' || file.name?.toLowerCase().endsWith('.pdf');
      const isImg = isImageFile(file);
      return isPdf || isImg;
    });
    if (validFiles.length !== files.length) {
      setFileName('');
      setSelectedFiles([]);
      setFileDetections([]);
      setBatchResults([]);
      setResponseMessage('');
      setErrorMessage('Please select a PDF document or image file. Other file types cannot be validated.');
      setTemplateDetection(null);
      return;
    }
    if (validFiles.length > 10) {
      setErrorMessage('Select no more than 10 documents in one local batch.');
      return;
    }
    const requestId = detectionRequestRef.current + 1;
    detectionRequestRef.current = requestId;
    setSelectedFiles(validFiles);
    setFileDetections(validFiles.map((file) => ({ file, selected_template: '', status: 'detecting' })));
    setFileName(validFiles[0]);
    setBatchResults([]);
    setActiveBatchIndex(0);
    setResponseMessage('');
    setErrorMessage('');
    setViewMode('checklist');
    setSelectedTemplate('');
    setSearchTerm('');
    setSelectedCategory('All');
    setTemplateDetection(validFiles.length === 1 ? { status: 'detecting' } : null);
    setDetectingTemplate(true);
    if (validFiles.length === 1) {
      setFileDetections([]);
      detectUploadedTemplate(validFiles[0], requestId);
    } else {
      detectBatchTemplates(validFiles, requestId);
    }
  };

  const handleFileChange = (event) => {
    if (event.target.files && event.target.files.length) {
      selectFiles(event.target.files);
    }
  };

  const clearFiles = (event) => {
    event?.stopPropagation();
    detectionRequestRef.current += 1;
    setFileName('');
    setSelectedFiles([]);
    setFileDetections([]);
    setBatchResults([]);
    setActiveBatchIndex(0);
    setResponseMessage('');
    setTemplateDetection(null);
    setDetectingTemplate(false);
    setErrorMessage('');
    setViewMode('checklist');
    const input = document.getElementById('file-input');
    if (input) input.value = '';
  };

  const removeSelectedFile = (index, event) => {
    event.stopPropagation();
    const remainingFiles = selectedFiles.filter((_, fileIndex) => fileIndex !== index);
    if (!remainingFiles.length) {
      clearFiles(event);
      return;
    }
    selectFiles(remainingFiles);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = () => {
    setIsDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length) {
      selectFiles(e.dataTransfer.files);
    }
  };

  const showBatchResult = (results, index) => {
    const item = results[index];
    if (!item) return;
    setActiveBatchIndex(index);
    setFileName(item.file);
    setResponseMessage(item.socrResponse ? JSON.stringify(item.socrResponse, null, 2) : '');
    setSelectedTemplate(item.template || '');
    setSearchTerm(item.template || '');
    setSelectedCategory(item.category || 'All');
    setErrorMessage(item.error || '');
    setViewMode('checklist');
  };

  const handleSubmit = async () => {
    if (!fileName || !batchTemplatesReady) {
      setErrorMessage('Choose a template for every PDF before starting the check.');
      return;
    }
    setLoading(true);
    setResponseMessage('');
    setErrorMessage('');
    const defaultTemplate = selectedTemplate || searchTerm || (templateNames.length > 0 ? templateNames[0] : '');
    const filesToValidate = selectedFiles.length ? selectedFiles : [fileName];
    setBatchResults([]);

    const validateFile = async (file, index) => {
      const detection = selectedFiles.length > 1 ? fileDetections[index] : null;
      const templateToUse = detection?.selected_template || defaultTemplate;
      const documentType = detection?.document_class || documentTypeForTemplate(templateToUse, detection?.category) || docCategory;
      const formData = new FormData();
      formData.append('file', file);
      formData.append('template', templateToUse);
      try {
        const response = await axios.post(`${API_BASE_URL}/validate_metadata`, formData);
        return {
          file,
          template: templateToUse,
          category: detection?.category || selectedCategory,
          documentType,
          socrResponse: response.data,
          socrStatus: response.data?.final_validation_results?.valid || 'UNKNOWN',
          error: ''
        };
      } catch (error) {
        return {
          file,
          template: templateToUse,
          category: detection?.category || selectedCategory,
          documentType,
          socrResponse: null,
          socrStatus: 'ERROR',
          error: error.response?.data?.error || 'Validation could not be completed for this PDF.'
        };
      }
    };

    try {
      const results = await Promise.all(filesToValidate.map(validateFile));
      setBatchResults(results);
      const firstSuccessfulIndex = results.findIndex((item) => item.socrResponse);
      showBatchResult(results, firstSuccessfulIndex >= 0 ? firstSuccessfulIndex : 0);
      if (results.every((item) => !item.socrResponse)) {
        setErrorMessage('Validation could not be completed for any PDF. Confirm that the API is available and try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleHighlightFile = () => {
    const formData = new FormData();
    formData.append('file', fileName);
    let font = 'Arial';
    try {
      font = JSON.parse(responseMessage)["template_rule_set_validation_results"][0]["fonts"]["additional_fonts"][0]["name"];
    } catch (e) {
      font = 'Arial';
    }
    formData.append('fonts', font);

    axios.post(`${API_BASE_URL}/highlight_fonts`, formData, { responseType: 'blob' })
      .then(response => {
        if (window.URL && typeof window.URL.createObjectURL === 'function' && response && response.data) {
          try {
            const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `highlighted_${fileName.name || 'document.pdf'}`);
            document.body.appendChild(link);
            link.click();
            link.remove();
          } catch (e) {
            // JSDOM environment
          }
        }
      })
      .catch(error => console.error('Error highlighting fonts:', error));
  };

  const fetchHighlightedPdf = async (font = 'all') => {
    if (!currentFile) return;
    setHighlightLoading(true);
    const formData = new FormData();
    formData.append('file', currentFile);
    formData.append('fonts', font);

    try {
      const response = await axios.post(`${API_BASE_URL}/highlight_fonts`, formData, {
        responseType: 'blob'
      });
      if (response && response.data) {
        let url = null;
        if (window.URL && typeof window.URL.createObjectURL === 'function') {
          url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }));
        }
        if (highlightedUrl && typeof URL.revokeObjectURL === 'function') {
          try { URL.revokeObjectURL(highlightedUrl); } catch (e) {}
        }
        setHighlightedUrl(url);
        setShowHighlights(true);
      }
    } catch (error) {
      console.error('Error fetching highlighted PDF:', error);
      setErrorMessage('Could not generate PDF highlights. Make sure the API is active.');
    } finally {
      setHighlightLoading(false);
    }
  };

  const handleToggleHighlight = () => {
    if (showHighlights) {
      setShowHighlights(false);
    } else {
      if (highlightedUrl) {
        setShowHighlights(true);
      } else {
        fetchHighlightedPdf('all');
      }
    }
  };

  const handleCopyText = (textToCopy) => {
    if (textToCopy) {
      navigator.clipboard.writeText(textToCopy);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  // Extract rule-by-rule breakdown
  const parsedDetails = useMemo(() => {
    if (!responseMessage) return null;
    try {
      const data = JSON.parse(responseMessage);
      const finalRes = data.final_validation_results || {};
      const ruleSets = data.template_rule_set_validation_results || [];
      const primaryRule = ruleSets[0] || {};

      // Format File Size display cleanly
      const fsObj = primaryRule.file_size || {};
      let fileSizeDisplay = 'N/A';
      if (fsObj.algorithm && fsObj.algorithm !== 'Unknown') {
        fileSizeDisplay = `${fsObj.algorithm} (${fsObj.min || 0} KB - ${fsObj.max || '∞'} KB)`;
      } else if (fsObj.actual) {
        fileSizeDisplay = `${fsObj.actual.toFixed(1)} KB (No Bounds Configured)`;
      } else {
        fileSizeDisplay = 'Dynamic / Unconstrained';
      }

      const baseRulesList = [
        {
          key: 'template',
          title: 'Template Selection & Validation',
          status: normalizeStatus(primaryRule.template?.valid || finalRes.valid),
          msgCode: primaryRule.template?.validation_message_code || finalRes.validation_message_code || 'MSG_UNKNOWN',
          details: `Target: ${primaryRule.template?.name || selectedTemplate || 'N/A'} (Actual: ${primaryRule.template?.actual || 'N/A'})`
        },
        {
          key: 'producer',
          title: 'Producer Software Match',
          status: normalizeStatus(primaryRule.producer?.valid),
          msgCode: primaryRule.producer?.validation_message_code || 'MSG_PRODUCER_CHECK',
          details: `Allowed Pattern: "${primaryRule.producer?.name || '*'}" | Actual: "${primaryRule.producer?.actual || 'N/A'}"`
        },
        {
          key: 'creator',
          title: 'Creator Software Match',
          status: normalizeStatus(primaryRule.creator?.valid),
          msgCode: primaryRule.creator?.validation_message_code || 'MSG_CREATOR_CHECK',
          details: `Allowed Pattern: "${primaryRule.creator?.name || '*'}" | Actual: "${primaryRule.creator?.actual || 'N/A'}"`
        },
        {
          key: 'file_size',
          title: 'File Size Validation',
          status: normalizeStatus(primaryRule.file_size?.valid),
          msgCode: primaryRule.file_size?.validation_message_code || 'MSG_FILE_SIZE_CHECK',
          details: fsObj.algorithm && fsObj.algorithm !== 'Unknown'
            ? `Algorithm: ${fsObj.algorithm} (${fsObj.min || 0} KB - ${fsObj.max || '∞'} KB) | Actual: ${fsObj.actual || 'N/A'} KB`
            : `Actual Size: ${fsObj.actual || 'N/A'} KB | Validation Rule: ${fsObj.validation_message_code || 'MSG_VALID_FILE_SIZE_UNKNOWN'}`
        },
        {
          key: 'fonts',
          title: 'Font Multiplicity & Verification',
          status: normalizeStatus(primaryRule.fonts?.valid),
          msgCode: primaryRule.fonts?.validation_message_code || 'MSG_FONT_CHECK',
          details: primaryRule.fonts?.additional_fonts?.length > 0 
            ? `Additional Fonts Detected: ${primaryRule.fonts.additional_fonts.map(f => f.name).join(', ')}`
            : 'All required fonts verified cleanly'
        },
        {
          key: 'dates',
          title: 'Creation & Mod Date Verification',
          status: normalizeStatus(primaryRule.dates?.valid),
          msgCode: primaryRule.dates?.validation_message_code || 'MSG_DATE_CHECK',
          details: `Created: ${primaryRule.dates?.created?.state || 'Unknown'}, Modified: ${primaryRule.dates?.modified?.state || 'Unknown'}`
        }
      ];

      const explanationByRule = {
        template: 'Checks whether the detected document template matches the template selected for validation.',
        producer: 'Checks whether the PDF producer software matches an allowed pattern for this template.',
        creator: 'Checks whether the PDF creator software matches an allowed pattern for this template.',
        file_size: 'Checks whether the document size is consistent with the configured template limits.',
        fonts: 'Checks for fonts that are not expected in the selected document template.',
        dates: 'Checks creation and modification date metadata against the template date policy.'
      };

      const statusExplanation = {
        Pass: 'The extracted evidence satisfies this rule.',
        FDR: 'The extracted evidence is unusual and should be reviewed manually.',
        Fail: 'The extracted evidence does not satisfy this rule.',
        'N/A': 'The API response did not provide enough evidence to evaluate this rule.'
      };

      const rulesList = baseRulesList.map((rule) => {
        let expected = 'Configured template rule';
        let actual = 'Not available';

        if (rule.key === 'template') {
          expected = primaryRule.template?.name || selectedTemplate || 'Selected template';
          actual = primaryRule.template?.actual || 'Not detected';
        } else if (rule.key === 'producer') {
          expected = primaryRule.producer?.name || 'Any producer allowed';
          actual = primaryRule.producer?.actual || 'Not present';
        } else if (rule.key === 'creator') {
          expected = primaryRule.creator?.name || 'Any creator allowed';
          actual = primaryRule.creator?.actual || 'Not present';
        } else if (rule.key === 'file_size') {
          expected = fsObj.algorithm && fsObj.algorithm !== 'Unknown'
            ? `${fsObj.min || 0} KB to ${fsObj.max || 'unbounded'} KB`
            : 'No configured size bounds';
          actual = fsObj.actual !== undefined ? `${fsObj.actual} KB` : 'Not available';
        } else if (rule.key === 'fonts') {
          expected = 'No unexpected fonts';
          actual = primaryRule.fonts?.additional_fonts?.length > 0
            ? primaryRule.fonts.additional_fonts.map((font) => font.name).join(', ')
            : 'No unexpected fonts found';
        } else if (rule.key === 'dates') {
          expected = 'Creation and modification dates consistent with template policy';
          actual = `Created: ${primaryRule.dates?.created?.state || 'Unknown'}; Modified: ${primaryRule.dates?.modified?.state || 'Unknown'}`;
        }

        const normalizedStatus = normalizeStatus(rule.status);
        return {
          ...rule,
          expected,
          actual,
          severity: normalizedStatus === 'Fail' ? 'High' : normalizedStatus === 'FDR' ? 'Medium' : normalizedStatus === 'Pass' ? 'Info' : 'Low',
          explanation: `${explanationByRule[rule.key]} ${statusExplanation[normalizedStatus] || statusExplanation['N/A']}`
        };
      });

      // Frontend-only scoring model for design evaluation. These weights are
      // deliberately kept out of the API contract until they are calibrated.
      const riskWeights = {
        template: 10,
        producer: 15,
        creator: 10,
        file_size: 5,
        fonts: 15,
        dates: 10
      };
      const riskFactors = { Pass: 0, FDR: 0.5, Fail: 1 };
      const scoredRules = rulesList
        .filter((rule) => Object.prototype.hasOwnProperty.call(riskFactors, rule.status))
        .map((rule) => ({
          ...rule,
          weight: riskWeights[rule.key] || 0,
          rawContribution: (riskWeights[rule.key] || 0) * riskFactors[rule.status]
        }));
      const availableRiskWeight = scoredRules.reduce((total, rule) => total + rule.weight, 0);
      const rawRiskPoints = scoredRules.reduce((total, rule) => total + rule.rawContribution, 0);
      const fallbackRiskScore = finalRes.valid === 'Fail' ? 100 : finalRes.valid === 'FDR' ? 50 : 0;
      const riskScore = availableRiskWeight > 0
        ? Math.round((rawRiskPoints / availableRiskWeight) * 100)
        : fallbackRiskScore;
      const riskLevel = riskScore >= 75 ? 'Critical' : riskScore >= 50 ? 'High' : riskScore >= 25 ? 'Moderate' : 'Low';
      const recommendedAction = riskLevel === 'Critical'
        ? 'Immediate escalation'
        : riskLevel === 'High'
          ? 'Priority manual review'
          : riskLevel === 'Moderate'
            ? 'Standard manual review'
            : 'No risk action required';
      const riskContributions = scoredRules
        .map((rule) => ({
          ...rule,
          contribution: availableRiskWeight > 0
            ? Math.round((rule.rawContribution / availableRiskWeight) * 1000) / 10
            : 0
        }))
        .filter((rule) => rule.contribution > 0)
        .sort((left, right) => right.contribution - left.contribution);

      // Format a simple, human-readable text report without decorative separators.
      let rawTextReport = `Document metadata validation report\n\n`;
      rawTextReport += `Overall status: ${normalizeStatus(finalRes.valid, 'Fail')}\n`;
      rawTextReport += `Preview risk score: ${riskScore}/100 (${riskLevel})\n`;
      rawTextReport += `Recommended action: ${recommendedAction}\n`;
      rawTextReport += `Message code: ${finalRes.validation_message_code || 'N/A'}\n`;
      rawTextReport += `Target template: ${selectedTemplate || primaryRule.template?.name || 'N/A'}\n`;
      rawTextReport += `File name: ${fileName ? fileName.name : 'N/A'}\n\n`;
      rawTextReport += `Rule evaluation\n\n`;

      rulesList.forEach((r, i) => {
        rawTextReport += `${i + 1}. ${r.title}\n`;
        rawTextReport += `Status: ${normalizeStatus(r.status)}\n`;
        rawTextReport += `Code: ${r.msgCode}\n`;
        rawTextReport += `Details: ${r.details}\n\n`;
      });
      rawTextReport = rawTextReport.trimEnd();

      const fontRule = rulesList.find(r => r.key === 'fonts');
      const dateRule = rulesList.find(r => r.key === 'dates');

      const fontsStatus = fontRule 
        ? `${fontRule.status} (${fontRule.msgCode})` 
        : 'N/A';

      const datesStatus = dateRule 
        ? `${dateRule.status} (${dateRule.msgCode})` 
        : 'N/A';

      const decisiveRules = rulesList.filter((rule) => rule.status === 'Fail');
      const reviewRules = rulesList.filter((rule) => rule.status === 'FDR');

      return {
        validState: normalizeStatus(finalRes.valid, 'Fail'),
        messageCode: finalRes.validation_message_code || 'MSG_UNKNOWN',
        templateName: primaryRule.template?.name || primaryRule.template?.actual || selectedTemplate || 'Unknown',
        producer: primaryRule.producer?.name || 'N/A',
        creator: primaryRule.creator?.name || 'N/A',
        fileSizeAlgo: fileSizeDisplay,
        fontsStatus,
        datesStatus,
        rulesList,
        decisiveRules,
        reviewRules,
        riskScore,
        riskLevel,
        recommendedAction,
        riskContributions,
        rawTextReport,
        counts: rulesList.reduce((counts, rule) => {
          const key = statusClassName(rule.status);
          counts[key] = (counts[key] || 0) + 1;
          return counts;
        }, { pass: 0, fdr: 0, fail: 0, neutral: 0 })
      };
    } catch (e) {
      return null;
    }
  }, [responseMessage, selectedTemplate, fileName]);



  const workflowStep = responseMessage ? 3 : fileName && batchTemplatesReady ? 2 : 1;
  const readinessMessage = loading
    ? `Validating ${selectedFiles.length > 1 ? `${selectedFiles.length} documents` : 'document'}…`
    : detectingTemplate
      ? 'Detecting document templates…'
      : !selectedFiles.length
        ? 'Add at least one PDF to begin.'
        : !batchTemplatesReady
          ? 'Choose a template for every document.'
          : `${selectedFiles.length} document${selectedFiles.length === 1 ? '' : 's'} ready for validation.`;

  return (
    <div className="app-container">
      <main className="main-card">
        <div className="product-bar">
          <div className="product-brand">
            <span className="brand-mark"><MetadataValidatorIcon size={20} /></span>
            <div>
              <strong>SOCR API V2 Rule Engine Metadata Inspector</strong>
              <span>Document intelligence workspace</span>
            </div>
          </div>
          <span className={`api-status ${apiStatus}`} role="status" aria-live="polite">
            <i></i>
            {apiStatus === 'checking' && 'Connecting to validator'}
            {apiStatus === 'ready' && 'Validator ready'}
            {apiStatus === 'unavailable' && 'Validator unavailable'}
          </span>
        </div>

        <div className="workflow-heading">
          <div className="workflow-icon" aria-hidden="true"><MetadataValidatorIcon size={23} /></div>
          <div>
            <span className="eyebrow">New analysis</span>
            <h2>Metadata validator</h2>
            <p>Upload one or more PDFs and choose the document template they should match.</p>
          </div>
        </div>

        <ol className="progress-steps" aria-label="Validation progress">
          <li className={workflowStep > 1 ? 'complete' : 'active'} aria-current={workflowStep === 1 ? 'step' : undefined}>
            <span>{workflowStep > 1 ? <CheckIcon /> : '1'}</span><div><strong>Upload PDFs</strong><small>Add up to 10 files</small></div>
          </li>
          <li className={workflowStep > 2 ? 'complete' : workflowStep === 2 ? 'active' : ''} aria-current={workflowStep === 2 ? 'step' : undefined}>
            <span>{workflowStep > 2 ? <CheckIcon /> : '2'}</span><div><strong>Assign templates</strong><small>Automatic or manual</small></div>
          </li>
          <li className={workflowStep === 3 ? 'active' : ''} aria-current={workflowStep === 3 ? 'step' : undefined}>
            <span>3</span><div><strong>Review results</strong><small>Inspect each document</small></div>
          </li>
        </ol>

        <div className="form-grid">
          {/* File Selection Dropzone */}
          <section className="input-section" aria-labelledby="documents-heading">
            <div className="section-heading">
              <div>
                <span className="section-icon"><FileIcon /></span>
                <div><h3 id="documents-heading">Documents</h3><p>PDF files only · up to 10 per batch</p></div>
              </div>
              {selectedFiles.length > 0 && <span className="section-count">{selectedFiles.length} selected</span>}
            </div>
            <div
              className={`file-upload-zone ${isDragOver ? 'drag-over' : ''} ${selectedFiles.length ? 'has-files' : ''}`}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              role="button"
              tabIndex="0"
              aria-label="Upload PDF documents"
              onKeyDown={(event) => {
                if (event.key === 'Enter' || event.key === ' ') document.getElementById('file-input')?.click();
              }}
              onClick={() => {
                const el = document.getElementById('file-input');
                if (el) el.click();
              }}
            >
              <input id="file-input" aria-label="Select files" type="file" accept="application/pdf,.pdf" multiple onChange={handleFileChange}/>
              <div className="upload-prompt">
                <div className="upload-icon-svg">
                  <UploadIcon />
                </div>
                {selectedFiles.length ? (
                  <div className="selected-files-summary">
                    <strong>{selectedFiles.length} PDF{selectedFiles.length === 1 ? '' : 's'} selected</strong>
                    <span>Drop more files or click to replace this selection</span>
                    <small>A separate template is detected for every PDF.</small>
                  </div>
                ) : (
                  <div>
                    <p className="upload-title">Drop your PDFs here, or click to browse</p>
                    <p className="upload-help">Up to 10 PDF files · each document is validated independently</p>
                  </div>
                )}
              </div>
            </div>
            {selectedFiles.length > 0 && (
              <div className="selected-file-list" aria-label="Selected PDF documents" aria-live="polite">
                <div className="selected-file-list-heading">
                  <strong>Files in this analysis</strong>
                  <button type="button" onClick={clearFiles}>Clear all</button>
                </div>
                {selectedFiles.map((file, index) => {
                  const detection = selectedFiles.length > 1 ? fileDetections[index] : templateDetection;
                  return (
                    <div className="selected-file-row" key={`${file.name}-${file.lastModified}-${index}`}>
                      <span className="selected-file-icon"><FileIcon /></span>
                      <div>
                        <strong>{file.name}</strong>
                        <small>{(file.size / 1024).toFixed(1)} KB · {detection?.status === 'detecting' ? 'Detecting template' : detection?.selected_template || detection?.template_name || 'Template pending'}</small>
                      </div>
                      <button type="button" className="remove-file-button" aria-label={`Remove ${file.name}`} onClick={(event) => removeSelectedFile(index, event)}><RemoveIcon /></button>
                    </div>
                  );
                })}
              </div>
            )}
          </section>

          {/* Template Autocomplete & Category Filter */}
          <section className="input-section" aria-labelledby="templates-heading">
            <div className="section-heading">
              <div>
                <span className="section-icon"><ShieldIcon /></span>
                <div><h3 id="templates-heading">Template assignment</h3><p>Confirm how each document should be validated</p></div>
              </div>
              <span className={`section-state ${batchTemplatesReady && selectedFiles.length ? 'ready' : ''}`}>{batchTemplatesReady && selectedFiles.length ? 'Ready' : 'Pending'}</span>
            </div>
            {selectedFiles.length > 1 && (
              <div className="batch-template-detections" aria-label="Templates detected for uploaded PDFs">
                <p>Each PDF is detected and validated independently.</p>
                {fileDetections.map((item, index) => (
                  <div className={`batch-template-row ${item.status}`} key={`${item.file.name}-${index}`}>
                    <div className="batch-template-file">
                      <strong>{item.file.name}</strong>
                      <span>
                        {item.status === 'detecting' && 'Detecting template…'}
                        {item.status === 'detected' && `Auto-selected · ${item.document_class} · ${item.confidence || 0}%`}
                        {item.status === 'review' && 'Manual selection required'}
                        {item.status === 'error' && (item.reason || 'Detection unavailable')}
                        {item.status === 'manual' && `Manually selected · ${item.document_class}`}
                      </span>
                    </div>
                    <label>
                      <span className="sr-only">Template for {item.file.name}</span>
                      <select
                        aria-label={`Template for ${item.file.name}`}
                        value={item.selected_template}
                        onChange={(event) => updateBatchTemplate(index, event.target.value)}
                        disabled={item.status === 'detecting'}
                      >
                        <option value="">Select template</option>
                        {templateNames.map((template) => <option value={template} key={template}>{template}</option>)}
                      </select>
                    </label>
                  </div>
                ))}
              </div>
            )}
            <div className={`single-template-controls ${selectedFiles.length > 1 ? 'hidden' : ''}`}>
            <div className="category-tabs" aria-label="Filter templates by document type">
              <button 
                type="button"
                className={`tab-btn ${selectedCategory === 'All' ? 'active' : ''}`}
                onClick={() => setSelectedCategory('All')}
              >
                All ({templateNames.length})
              </button>
              <button 
                type="button"
                className={`tab-btn ${selectedCategory === 'Bank Statements' ? 'active' : ''}`}
                onClick={() => setSelectedCategory('Bank Statements')}
              >
                Bank statements ({categories['Bank Statements']?.length || 0})
              </button>
              <button 
                type="button"
                className={`tab-btn ${selectedCategory === 'Paystubs & Earnings' ? 'active' : ''}`}
                onClick={() => setSelectedCategory('Paystubs & Earnings')}
              >
                Paystubs & earnings ({categories['Paystubs & Earnings']?.length || 0})
              </button>
            </div>

            <Autocomplete 
              data-testid="autocomplete" 
              onChange={(_, newValue) => {
                const val = newValue || '';
                setSelectedTemplate(val);
                setSearchTerm(val);
                if (val) setTemplateDetection((current) => current ? { ...current, status: 'manual' } : null);
              }}
              onInputChange={(_, newInputValue, reason) => {
                const val = newInputValue || '';
                setSelectedTemplate(val);
                setSearchTerm(val);
                if (val && reason === 'input') {
                  setTemplateDetection((current) => current ? { ...current, status: 'manual' } : null);
                }
              }}
              options={filteredTemplates} 
              value={searchTerm} 
              freeSolo
              renderInput={(params) => (
                <TextField 
                  {...params} 
                  id="template-search"
                  label="Search templates"
                  placeholder={`Search in ${selectedCategory} (${docCategory})...`}
                  inputProps={{...params.inputProps, role: 'textbox' }}
                />
              )}
            />
            <span className="template-context">Selected type <strong>{docCategory}</strong></span>
            {templateDetection && (
              <div className={`template-detection ${templateDetection.status}`} role="status" aria-live="polite">
                {templateDetection.status === 'detecting' && (
                  <>
                    <span className="detection-spinner" aria-hidden="true"></span>
                    <div><strong>Detecting template</strong><p>Comparing PDF metadata with known document fingerprints…</p></div>
                  </>
                )}
                {templateDetection.status === 'detected' && (
                  <>
                    <CheckIcon />
                    <div>
                      <strong>Auto-selected {templateDetection.template_name}</strong>
                      <p>{templateDetection.document_class} · {templateDetection.confidence}% fingerprint match</p>
                    </div>
                  </>
                )}
                {templateDetection.status === 'review' && (
                  <>
                    <AlertIcon />
                    <div>
                      <strong>Manual confirmation needed</strong>
                      <p>
                        {templateDetection.template_name
                          ? `Closest match: ${templateDetection.template_name} (${templateDetection.confidence || 0}%).`
                          : templateDetection.reason} Select the correct template above.
                      </p>
                    </div>
                  </>
                )}
                {templateDetection.status === 'error' && (
                  <>
                    <AlertIcon />
                    <div><strong>Automatic detection unavailable</strong><p>{templateDetection.reason}</p></div>
                  </>
                )}
                {templateDetection.status === 'manual' && (
                  <>
                    <ShieldIcon />
                    <div><strong>Manual selection</strong><p>Your selection will be used for validation.</p></div>
                  </>
                )}
              </div>
            )}
            </div>
          </section>

          {errorMessage && <div className="error-notice" role="alert"><AlertIcon /><span>{errorMessage}</span></div>}

          {/* Action Row */}
          <div className="actions-row">
            <div className={`validation-readiness ${batchTemplatesReady && selectedFiles.length ? 'ready' : ''}`} role="status" aria-live="polite">
              <span>{batchTemplatesReady && selectedFiles.length ? <CheckIcon /> : <ShieldIcon />}</span>
              <div><strong>{batchTemplatesReady && selectedFiles.length ? 'Ready to validate' : 'Validation setup'}</strong><small>{readinessMessage}</small></div>
            </div>
            <div className="action-buttons">
            <button 
              className="btn-primary"
              aria-label={selectedFiles.length > 1 ? `Validate ${selectedFiles.length} documents` : 'Submit metadata validation'}
              disabled={!fileName || !batchTemplatesReady || loading || detectingTemplate}
              onClick={handleSubmit}
            >
              {loading ? (
                  <span>Analyzing {selectedFiles.length > 1 ? `${selectedFiles.length} documents` : 'document'}...</span>
              ) : (
                <>
                  <CheckIcon />
                  <span>Validate {selectedFiles.length > 1 ? `${selectedFiles.length} documents` : 'metadata'}</span>
                </>
              )}
            </button>

            <button 
              className="btn-secondary"
              hidden={!responseMessage} 
              onClick={handleHighlightFile}
            >
              <DownloadIcon />
              <span>Get highlighted file</span>
            </button>
            </div>
          </div>
        </div>

        {batchResults.length > 1 && (
          <section className="batch-results" aria-label="Batch validation results">
            <div className="batch-results-heading">
              <strong>Batch results</strong>
              <span>{batchResults.filter((item) => item.socrResponse).length} of {batchResults.length} documents completed</span>
            </div>
            <div className="batch-result-tabs" role="tablist" aria-label="Choose a document result">
              {batchResults.map((item, index) => (
                <button
                  type="button"
                  role="tab"
                  aria-label={`${item.file.name}, ${item.template}, SOCR: ${item.socrStatus}`}
                  aria-selected={activeBatchIndex === index}
                  className={activeBatchIndex === index ? 'active' : ''}
                  onClick={() => showBatchResult(batchResults, index)}
                  key={`${item.file.name}-${index}`}
                >
                  <span>{index + 1}</span>
                  <div>
                    <strong>{item.file.name}</strong>
                    <small>{item.template}</small>
                    <span className="batch-result-statuses">
                      <b className={`batch-status ${statusClassName(item.socrStatus)}`}>SOCR: {item.socrStatus}</b>
                    </span>
                  </div>
                </button>
              ))}
            </div>
          </section>
        )}

        {/* Validation Results Section */}
        {responseMessage && (
          <div className="results-card">
            {parsedDetails && (
              <>
                {/* Status Banner */}
                <div className={`status-banner ${statusClassName(parsedDetails.validState)}`}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    {parsedDetails.validState === 'Pass' ? <CheckIcon /> : <AlertIcon />}
                    <div>
                      <strong style={{ fontSize: '1.05rem' }}>
                        {parsedDetails.validState === 'Pass' && 'Metadata Validated Successfully'}
                        {parsedDetails.validState === 'FDR' && 'FDR Alert: Modification Detected'}
                        {parsedDetails.validState === 'Fail' && 'Validation Failed / Fraud Detected'}
                      </strong>
                      <div style={{ fontSize: '0.85rem', opacity: 0.9, marginTop: 2 }}>
                        Code: {parsedDetails.messageCode}
                      </div>
                    </div>
                  </div>
                  <span className="status-pill">{parsedDetails.validState}</span>
                </div>

                <div className="result-summary" aria-label="Rule result summary">
                  <span><strong>{parsedDetails.rulesList.length}</strong> rules checked</span>
                  <span className="summary-pass"><strong>{parsedDetails.counts.pass}</strong> passed</span>
                  <span className="summary-fdr"><strong>{parsedDetails.counts.fdr}</strong> review</span>
                  <span className="summary-fail"><strong>{parsedDetails.counts.fail}</strong> failed</span>
                </div>

                <section className={`risk-score-preview risk-${parsedDetails.riskLevel.toLowerCase()}`} aria-label="Testing risk score preview">
                  <div
                    className="risk-score-ring"
                    style={{ '--risk-score-angle': `${parsedDetails.riskScore * 3.6}deg` }}
                    role="img"
                    aria-label={`Risk score ${parsedDetails.riskScore} out of 100`}
                  >
                    <div className="risk-score-ring-inner">
                      <strong>{parsedDetails.riskScore}</strong>
                      <span>/100</span>
                    </div>
                  </div>
                  <div className="risk-score-copy">
                    <div className="risk-score-heading">
                      <div>
                        <span className="risk-preview-label">Risk scoring preview</span>
                        <h3>{parsedDetails.riskLevel} risk</h3>
                      </div>
                      <span className="testing-badge">Testing only</span>
                    </div>
                    <p>{parsedDetails.recommendedAction}. This uncalibrated score summarizes the available metadata rules and is not a fraud probability.</p>
                    <div className="risk-contribution-list" aria-label="Risk contribution breakdown">
                      {parsedDetails.riskContributions.length > 0 ? (
                        parsedDetails.riskContributions.slice(0, 4).map((rule) => (
                          <div className="risk-contribution" key={rule.key}>
                            <span>{rule.title}</span>
                            <div className="risk-contribution-track" aria-hidden="true">
                              <i style={{ width: `${Math.min(rule.contribution * 2, 100)}%` }}></i>
                            </div>
                            <strong>+{rule.contribution}</strong>
                          </div>
                        ))
                      ) : (
                        <span className="no-risk-contribution">No rules contributed risk points.</span>
                      )}
                    </div>
                  </div>
                </section>

                <div className="decision-explanation">
                  <span className="decision-label">Why this final result?</span>
                  <p>
                    {parsedDetails.decisiveRules.length > 0
                      ? `The final decision is driven by: ${parsedDetails.decisiveRules.map((rule) => rule.title).join(', ')}.`
                      : parsedDetails.reviewRules.length > 0
                        ? `Manual review is recommended because of: ${parsedDetails.reviewRules.map((rule) => rule.title).join(', ')}.`
                        : 'All available rule evidence satisfies the selected template.'}
                  </p>
                </div>

                {/* Metrics Breakdown Grid */}
                <div className="metrics-grid">
                  <div className="metric-card">
                    <span className="metric-title">Template & Category</span>
                    <span className="metric-value">{parsedDetails.templateName} ({docCategory})</span>
                  </div>

                  <div className="metric-card">
                    <span className="metric-title">Producer Pattern</span>
                    <span className="metric-value">{parsedDetails.producer}</span>
                  </div>

                  <div className="metric-card">
                    <span className="metric-title">Creator Pattern</span>
                    <span className="metric-value">{parsedDetails.creator}</span>
                  </div>

                  <div className="metric-card">
                    <span className="metric-title">File Size Check</span>
                    <span className="metric-value">{parsedDetails.fileSizeAlgo}</span>
                  </div>

                  <div className="metric-card">
                    <span className="metric-title">Font Verification</span>
                    <span className="metric-value">{parsedDetails.fontsStatus}</span>
                  </div>

                  <div className="metric-card">
                    <span className="metric-title">Date Verification</span>
                    <span className="metric-value">{parsedDetails.datesStatus}</span>
                  </div>
                </div>

                {/* View Mode Navigation Tabs */}
                <div className="view-tabs">
                  <button 
                    className={`tab-btn ${viewMode === 'checklist' ? 'active' : ''}`}
                    onClick={() => setViewMode('checklist')}
                  >
                    <MetadataValidatorIcon size={18} />
                    <span>Metadata Validator</span>
                  </button>

                  <button 
                    className={`tab-btn ${viewMode === 'preview' ? 'active' : ''}`}
                    onClick={() => setViewMode('preview')}
                  >
                    <EyeIcon />
                    <span>PDF Preview</span>
                  </button>

                  <button 
                    className={`tab-btn ${viewMode === 'rawText' ? 'active' : ''}`}
                    onClick={() => setViewMode('rawText')}
                  >
                    <FileIcon />
                    <span>Raw Data Text</span>
                  </button>

                  <button 
                    className={`tab-btn ${viewMode === 'rawJson' ? 'active' : ''}`}
                    onClick={() => setViewMode('rawJson')}
                  >
                    <CodeIcon />
                    <span>Raw JSON Output</span>
                  </button>

                </div>
              </>
            )}

            {/* TAB 1: Rule-by-Rule Checklist */}
            {viewMode === 'checklist' && parsedDetails && (
              <div className="checklist-grid">
                <div className="explainability-preview">
                  <div>
                    <strong>Explainability preview</strong>
                    <span>Testing display only</span>
                  </div>
                  <p>Expected, found, and explanation fields are derived in the UI from the current API response.</p>
                </div>
                {parsedDetails.rulesList.map((rule) => {
                  const itemStatus = statusClassName(rule.status);
                  return (
                    <div key={rule.key} className={`checklist-item ${itemStatus}`}>
                      <div className="rule-info">
                        <div className="rule-heading-row">
                          <div className="rule-category-title">
                            {itemStatus === 'pass' && <CheckIcon />}
                            {itemStatus !== 'pass' && <AlertIcon />}
                            <span>{rule.title}</span>
                          </div>
                          <div className="rule-tags">
                            <span className={`severity-badge severity-${rule.severity.toLowerCase()}`}>{rule.severity} severity</span>
                            <span className={`rule-badge ${itemStatus}`}>{rule.status}</span>
                          </div>
                        </div>
                        <span className="rule-msg-code">{rule.msgCode}</span>
                        <div className="rule-evidence-grid">
                          <div>
                            <span>Expected</span>
                            <strong>{rule.expected}</strong>
                          </div>
                          <div>
                            <span>Found</span>
                            <strong>{rule.actual}</strong>
                          </div>
                        </div>
                        <div className="rule-why">
                          <span>Why</span>
                          <p>{rule.explanation}</p>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}

            {/* TAB 3: Raw Text Area Report */}
            {viewMode === 'rawText' && parsedDetails && (
              <div className="raw-text-container">
                <div className="results-header">
                  <div className="results-title">
                    <FileIcon />
                    <span>Raw Text Validation Report</span>
                  </div>

                  <button 
                    type="button"
                    onClick={() => handleCopyText(parsedDetails.rawTextReport)}
                    className="btn-secondary"
                    style={{ padding: '5px 10px', fontSize: '0.76rem' }}
                  >
                    <CopyIcon />
                    <span>{copied ? 'Copied!' : 'Copy Text'}</span>
                  </button>
                </div>

                <pre className="code-viewer">{parsedDetails.rawTextReport}</pre>
              </div>
            )}

            {/* TAB 2: Document Preview (PDF / Image) */}
            {viewMode === 'preview' && (
              <div className="pdf-preview-container">
                <div className="results-header">
                  <div className="results-title">
                    <EyeIcon />
                    <span>Document Preview — {typeof currentFile === 'object' && currentFile?.name ? currentFile.name : (typeof currentFile === 'string' ? currentFile : 'Document')}</span>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    {!isImageFile(currentFile) && (
                      <button
                        type="button"
                        className={`btn-highlight-toggle ${showHighlights ? 'active' : ''}`}
                        onClick={handleToggleHighlight}
                        disabled={highlightLoading}
                        aria-label="Toggle highlighted PDF text"
                      >
                        {highlightLoading ? (
                          <span>Highlighting...</span>
                        ) : (
                          <>
                            <span className="highlight-dot"></span>
                            <span>{showHighlights ? 'Hide Highlights' : 'Highlight Extracted Parts'}</span>
                          </>
                        )}
                      </button>
                    )}

                    {(showHighlights && highlightedUrl ? highlightedUrl : previewUrl) && (
                      <a 
                        href={showHighlights && highlightedUrl ? highlightedUrl : previewUrl} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="btn-preview-new-tab"
                      >
                        Open in New Tab ↗
                      </a>
                    )}
                  </div>
                </div>

                {showHighlights && (
                  <div className="highlight-banner" role="status">
                    <span className="highlight-indicator-dot"></span>
                    <span><strong>Extracted Parts Highlighted:</strong> Red box annotations highlight fonts and text extracted from this PDF for metadata analysis.</span>
                  </div>
                )}

                {previewUrl ? (
                  isImageFile(currentFile) ? (
                    <div className="image-preview-wrapper" data-testid="preview-image-wrapper">
                      <img
                        src={previewUrl}
                        alt={typeof currentFile === 'object' && currentFile?.name ? currentFile.name : (typeof currentFile === 'string' ? currentFile : 'Document Preview')}
                        className="document-preview-image"
                        data-testid="preview-image"
                      />
                    </div>
                  ) : (
                    <object
                      data={showHighlights && highlightedUrl ? highlightedUrl : previewUrl}
                      type="application/pdf"
                      className="pdf-preview-object"
                      data-testid="preview-pdf"
                    >
                      <iframe
                        src={showHighlights && highlightedUrl ? highlightedUrl : previewUrl}
                        title="PDF Document Preview"
                        className="pdf-preview-iframe"
                      />
                    </object>
                  )
                ) : (
                  <div className="pdf-preview-empty">
                    <AlertIcon />
                    <span>No active document available for preview.</span>
                  </div>
                )}
              </div>
            )}



            {/* TAB 3: Raw JSON Output (Preserved for tests) */}
            <div style={{ display: viewMode === 'rawJson' || !parsedDetails ? 'block' : 'none' }}>
              <div className="results-header">
                <div className="results-title">
                  <CodeIcon />
                  <span>Raw Validation JSON</span>
                </div>

                <button 
                  onClick={() => handleCopyText(responseMessage)}
                  style={{
                    background: '#ffffff',
                    border: '1px solid #cbd5e1',
                    color: '#475569',
                    borderRadius: '8px',
                    padding: '6px 12px',
                    fontSize: '0.8rem',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px'
                  }}
                >
                  <CopyIcon />
                  <span>{copied ? 'Copied!' : 'Copy JSON'}</span>
                </button>
              </div>

              <pre className="code-viewer">{responseMessage}</pre>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;



