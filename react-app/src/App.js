import React, { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
import { Autocomplete, TextField } from '@mui/material';
import './App.css';

// SVG Icon Components
const LightningIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
  </svg>
);

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

function App() {
  const [fileName, setFileName] = useState('');
  const [responseMessage, setResponseMessage] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [templateNames, setTemplateNames] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState('');
  const [isDragOver, setIsDragOver] = useState(false);
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);
  const [viewMode, setViewMode] = useState('checklist'); // 'checklist' | 'rawText' | 'rawJson'
  const [categories, setCategories] = useState({ 'Bank Statements': [], 'Paystubs & Earnings': [] });
  const [selectedCategory, setSelectedCategory] = useState('All');

  useEffect(() => {
    const fetchTemplateNames = async () => {
      try {
        const [namesRes, catRes] = await Promise.all([
          axios.get('http://localhost:5000/template_names'),
          axios.get('http://localhost:5000/template_categories').catch(() => null)
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
      } catch (error) {
        console.error('Error fetching template names or categories:', error);
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
    if (categories['Paystubs & Earnings']?.includes(t)) return 'Paystub / Earning Statement';
    if (categories['Bank Statements']?.includes(t)) return 'Bank Statement';
    if (/adp|gusto|paycom|paycor|paystub|earning|intuit|ceridian|paychex/i.test(t)) return 'Paystub / Earning Statement';
    return 'Bank Statement';
  }, [selectedTemplate, searchTerm, categories]);

  const handleFileChange = (event) => {
    if (event.target.files && event.target.files[0]) {
      setFileName(event.target.files[0]);
    }
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
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFileName(e.dataTransfer.files[0]);
    }
  };

  const handleSubmit = () => {
    setLoading(true);
    setResponseMessage('');
    const formData = new FormData();
    formData.append('file', fileName);
    const templateToUse = selectedTemplate || searchTerm || (templateNames.length > 0 ? templateNames[0] : '');
    formData.append('template', templateToUse);

    axios.post('http://localhost:5000/validate_metadata', formData)
      .then(response => {
        setResponseMessage(JSON.stringify(response.data, null, 2));
        setLoading(false);
      })
      .catch(error => {
        console.error('Error uploading file:', error);
        setResponseMessage(JSON.stringify({ error: error.message || 'Failed to connect to backend server' }, null, 2));
        setLoading(false);
      });
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

    axios.post('http://localhost:5000/highlight_fonts', formData)
      .then(response => {
        console.log(response);
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

      const rulesList = [
        {
          key: 'template',
          title: 'Template Selection & Validation',
          status: primaryRule.template?.valid || finalRes.valid || 'Fail',
          msgCode: primaryRule.template?.validation_message_code || finalRes.validation_message_code || 'MSG_UNKNOWN',
          details: `Target: ${primaryRule.template?.name || selectedTemplate || 'N/A'} (Actual: ${primaryRule.template?.actual || 'N/A'})`
        },
        {
          key: 'producer',
          title: 'Producer Software Match',
          status: primaryRule.producer?.valid || 'Pass',
          msgCode: primaryRule.producer?.validation_message_code || 'MSG_PRODUCER_CHECK',
          details: `Allowed Pattern: "${primaryRule.producer?.name || '*'}" | Actual: "${primaryRule.producer?.actual || 'N/A'}"`
        },
        {
          key: 'creator',
          title: 'Creator Software Match',
          status: primaryRule.creator?.valid || 'Pass',
          msgCode: primaryRule.creator?.validation_message_code || 'MSG_CREATOR_CHECK',
          details: `Allowed Pattern: "${primaryRule.creator?.name || '*'}" | Actual: "${primaryRule.creator?.actual || 'N/A'}"`
        },
        {
          key: 'file_size',
          title: 'File Size Validation',
          status: primaryRule.file_size?.valid || 'Pass',
          msgCode: primaryRule.file_size?.validation_message_code || 'MSG_FILE_SIZE_CHECK',
          details: fsObj.algorithm && fsObj.algorithm !== 'Unknown'
            ? `Algorithm: ${fsObj.algorithm} (${fsObj.min || 0} KB - ${fsObj.max || '∞'} KB) | Actual: ${fsObj.actual || 'N/A'} KB`
            : `Actual Size: ${fsObj.actual || 'N/A'} KB | Validation Rule: ${fsObj.validation_message_code || 'MSG_VALID_FILE_SIZE_UNKNOWN'}`
        },
        {
          key: 'fonts',
          title: 'Font Multiplicity & Verification',
          status: primaryRule.fonts?.valid || 'Pass',
          msgCode: primaryRule.fonts?.validation_message_code || 'MSG_FONT_CHECK',
          details: primaryRule.fonts?.additional_fonts?.length > 0 
            ? `Additional Fonts Detected: ${primaryRule.fonts.additional_fonts.map(f => f.name).join(', ')}`
            : 'All required fonts verified cleanly'
        },
        {
          key: 'dates',
          title: 'Creation & Mod Date Verification',
          status: primaryRule.dates?.valid || 'Pass',
          msgCode: primaryRule.dates?.validation_message_code || 'MSG_DATE_CHECK',
          details: `Created: ${primaryRule.dates?.created?.state || 'Unknown'}, Modified: ${primaryRule.dates?.modified?.state || 'Unknown'}`
        }
      ];

      // Format raw text report
      let rawTextReport = `======================================================================\n`;
      rawTextReport += `SOCR DOCUMENT METADATA VALIDATION REPORT\n`;
      rawTextReport += `======================================================================\n`;
      rawTextReport += `Overall Status  : [${(finalRes.valid || 'FAIL').toUpperCase()}]\n`;
      rawTextReport += `Message Code    : ${finalRes.validation_message_code || 'N/A'}\n`;
      rawTextReport += `Target Template : ${selectedTemplate || primaryRule.template?.name || 'N/A'}\n`;
      rawTextReport += `File Name       : ${fileName ? fileName.name : 'N/A'}\n`;
      rawTextReport += `======================================================================\n\n`;
      rawTextReport += `INDIVIDUAL RULE EVALUATION BREAKDOWN:\n`;
      rawTextReport += `----------------------------------------------------------------------\n`;

      rulesList.forEach((r, i) => {
        rawTextReport += `${i + 1}. [${(r.status || 'PASS').toUpperCase()}] ${r.title}\n`;
        rawTextReport += `   - Code   : ${r.msgCode}\n`;
        rawTextReport += `   - Details: ${r.details}\n\n`;
      });
      rawTextReport += `----------------------------------------------------------------------\n`;
      rawTextReport += `END OF REPORT\n`;
      rawTextReport += `======================================================================\n`;

      const fontRule = rulesList.find(r => r.key === 'fonts');
      const dateRule = rulesList.find(r => r.key === 'dates');

      const fontsStatus = fontRule 
        ? `${fontRule.status} (${fontRule.msgCode})` 
        : 'N/A';

      const datesStatus = dateRule 
        ? `${dateRule.status} (${dateRule.msgCode})` 
        : 'N/A';

      return {
        validState: finalRes.valid || 'Fail',
        messageCode: finalRes.validation_message_code || 'MSG_UNKNOWN',
        templateName: primaryRule.template?.name || primaryRule.template?.actual || selectedTemplate || 'Unknown',
        producer: primaryRule.producer?.name || 'N/A',
        creator: primaryRule.creator?.name || 'N/A',
        fileSizeAlgo: fileSizeDisplay,
        fontsStatus,
        datesStatus,
        rulesList,
        rawTextReport
      };
    } catch (e) {
      return null;
    }
  }, [responseMessage, selectedTemplate, fileName]);

  return (
    <div className="app-container">
      <header className="app-header">
        <div className="brand-badge">
          <LightningIcon />
          <span>SOCR Metadata Engine</span>
        </div>
        <h1 className="app-title">Document Metadata Inspector</h1>
        <p className="app-subtitle">Automated metadata rule validation & fraud detection</p>
      </header>

      <main className="main-card">
        <div className="form-grid">
          {/* File Selection Dropzone */}
          <div className="input-section">
            <label htmlFor="file-input" className="section-label">
              <FileIcon />
              Select file:
            </label>
            <div 
              className={`file-upload-zone ${isDragOver ? 'drag-over' : ''}`}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => {
                const el = document.getElementById('file-input');
                if (el) el.click();
              }}
            >
              <input id="file-input" type="file" onChange={handleFileChange}/>
              <div className="upload-prompt">
                <div className="upload-icon-svg">
                  <UploadIcon />
                </div>
                {fileName ? (
                  <div className="selected-file-info">
                    <FileIcon />
                    <span>Selected: <strong>{fileName.name}</strong></span>
                    <span style={{ fontSize: '0.8rem', opacity: 0.8 }}>({(fileName.size / 1024).toFixed(1)} KB)</span>
                  </div>
                ) : (
                  <div>
                    <p style={{ fontWeight: 600, color: '#0f172a', marginBottom: 4 }}>Click or drag PDF document here</p>
                    <p style={{ fontSize: '0.85rem', color: '#64748b' }}>Select document statement for validation</p>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Template Autocomplete & Category Filter */}
          <div className="input-section">
            <div style={{ display: 'flex', gap: 8, marginBottom: 4, flexWrap: 'wrap' }}>
              <button 
                type="button"
                className={`tab-btn ${selectedCategory === 'All' ? 'active' : ''}`}
                style={{ flex: 'none', padding: '6px 14px', fontSize: '0.8rem' }}
                onClick={() => setSelectedCategory('All')}
              >
                All ({templateNames.length})
              </button>
              <button 
                type="button"
                className={`tab-btn ${selectedCategory === 'Bank Statements' ? 'active' : ''}`}
                style={{ flex: 'none', padding: '6px 14px', fontSize: '0.8rem' }}
                onClick={() => setSelectedCategory('Bank Statements')}
              >
                🏦 Bank Statements ({categories['Bank Statements']?.length || 0})
              </button>
              <button 
                type="button"
                className={`tab-btn ${selectedCategory === 'Paystubs & Earnings' ? 'active' : ''}`}
                style={{ flex: 'none', padding: '6px 14px', fontSize: '0.8rem' }}
                onClick={() => setSelectedCategory('Paystubs & Earnings')}
              >
                📄 Paystubs & Earnings ({categories['Paystubs & Earnings']?.length || 0})
              </button>
            </div>

            <Autocomplete 
              data-testid="autocomplete" 
              onChange={(_, newValue) => {
                const val = newValue || '';
                setSelectedTemplate(val);
                setSearchTerm(val);
              }}
              onInputChange={(_, newInputValue) => {
                const val = newInputValue || '';
                setSelectedTemplate(val);
                setSearchTerm(val);
              }}
              options={filteredTemplates} 
              value={searchTerm} 
              freeSolo
              renderInput={(params) => (
                <TextField 
                  {...params} 
                  label="Search:" 
                  placeholder={`Search in ${selectedCategory} (${docCategory})...`}
                  inputProps={{...params.inputProps, role: 'textbox' }}
                />
              )}
            />
            <span style={{ fontSize: '0.8rem', color: '#64748b', marginTop: 2 }}>
              Category: <strong>{docCategory}</strong>
            </span>
          </div>

          {/* Action Row */}
          <div className="actions-row">
            <button 
              className="btn-primary"
              disabled={!fileName || loading} 
              onClick={handleSubmit}
            >
              {loading ? (
                <span>Analyzing Document...</span>
              ) : (
                <>
                  <CheckIcon />
                  <span>Submit</span>
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

        {/* Validation Results Section */}
        {responseMessage && (
          <div className="results-card">
            {parsedDetails && (
              <>
                {/* Status Banner */}
                <div className={`status-banner ${parsedDetails.validState.toLowerCase()}`}>
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
                    <CheckIcon />
                    <span>Rule Checklist</span>
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
                {parsedDetails.rulesList.map((rule) => {
                  const itemStatus = (rule.status || 'Pass').toLowerCase();
                  return (
                    <div key={rule.key} className={`checklist-item ${itemStatus}`}>
                      <div className="rule-info">
                        <div className="rule-category-title">
                          {itemStatus === 'pass' && <CheckIcon />}
                          {itemStatus !== 'pass' && <AlertIcon />}
                          <span>{rule.title}</span>
                        </div>
                        <span className="rule-msg-code">{rule.msgCode}</span>
                        <p className="rule-details">{rule.details}</p>
                      </div>
                      <span className={`rule-badge ${itemStatus}`}>
                        {rule.status}
                      </span>
                    </div>
                  );
                })}
              </div>
            )}

            {/* TAB 2: Raw Text Area Report */}
            {viewMode === 'rawText' && parsedDetails && (
              <div className="raw-text-container">
                <div className="results-header">
                  <div className="results-title">
                    <FileIcon />
                    <span>Raw Text Validation Report</span>
                  </div>

                  <button 
                    onClick={() => handleCopyText(parsedDetails.rawTextReport)}
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
                    <span>{copied ? 'Copied!' : 'Copy Text'}</span>
                  </button>
                </div>
                <textarea 
                  className="raw-text-area"
                  readOnly
                  value={parsedDetails.rawTextReport}
                />
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



