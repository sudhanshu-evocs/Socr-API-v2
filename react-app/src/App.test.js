import { render, screen, fireEvent, waitFor, cleanup } from '@testing-library/react';
import "@testing-library/jest-dom"
import { act } from 'react';
import App from './App';
import axios from 'axios';

jest.mock('axios');


if (!window.URL.createObjectURL) {
  window.URL.createObjectURL = jest.fn(() => 'blob:http://localhost/dummy-pdf-id');
}
if (!window.URL.revokeObjectURL) {
  window.URL.revokeObjectURL = jest.fn();
}

var templateNames = []
beforeEach(async () => {
  jest.clearAllMocks();
  templateNames = ['Template1', 'Template2', 'Template3'];
  axios.get.mockImplementation((url) => Promise.resolve({
    data: url.endsWith('/template_categories')
      ? { 'Bank Statements': ['Template1', 'Template2'], 'Paystubs & Earnings': ['Template3'] }
      : templateNames
  }));
  axios.post.mockImplementation((url) => {
    if (url.endsWith('/detect_template')) {
      return Promise.resolve({
        data: {
          auto_select: true,
          detected: true,
          template_name: 'Template1',
          category: 'Bank Statements',
          document_class: 'Bank Statement',
          confidence: 92,
          confidence_margin: 30,
          matched_signals: ['producer', 'fonts']
        }
      });
    }
    return Promise.resolve({ data: {} });
  });

  await act( async() => render(<App />));
})

test('button is disabled when file input is empty', async () => {
  const fileInputElement = screen.getByLabelText(/select file/i);
  const buttonElement = screen.getByRole('button', { name: /submit/i });
  await waitFor(() => {
    fireEvent.change(fileInputElement, { target: { files: [] } });
  })

  expect(buttonElement).toBeDisabled();
});

test('no highlighted file button exists when nothing has happened yet', async () => {
  const button = screen.queryByRole('button', { name: /get highlighted file/i})
  if (button)
    expect(button).not.toBeVisible()
  else
    expect(button).not.toBeInTheDocument()
})

test('button is enabled when file input has file selected', async () => {


  const fileInputElement = screen.getByLabelText(/select file/i);
  const buttonElement = screen.getByRole('button', { name: /submit/i });

  const file = new File(['dummy content'], 'example.pdf', { type: 'application/pdf' });
  await waitFor(() => {
    fireEvent.change(fileInputElement, { target: { files: [file] } });
  })

  await screen.findByText(/auto-selected Template1/i);
  expect(buttonElement).toBeEnabled();
});

test('upload automatically selects the detected template and document class', async () => {
  const file = new File(['dummy content'], 'ally.pdf', { type: 'application/pdf' });
  fireEvent.change(screen.getByLabelText(/select file/i), { target: { files: [file] } });

  expect(await screen.findByText(/auto-selected Template1/i)).toBeInTheDocument();
  expect(screen.getByText(/Bank Statement · 92% fingerprint match/i)).toBeInTheDocument();
  expect(screen.getByRole('textbox', { name: /search/i })).toHaveValue('Template1');
  expect(screen.getByRole('button', { name: /bank statements/i })).toHaveClass('active');

  const detectionCall = axios.post.mock.calls.find(([url]) => url.endsWith('/detect_template'));
  expect(detectionCall).toBeDefined();
  expect(detectionCall[1].get('file')).toBe(file);
});

test('ambiguous detection keeps validation disabled until a manual template is selected', async () => {
  axios.post.mockImplementation((url) => {
    if (url.endsWith('/detect_template')) {
      return Promise.resolve({
        data: {
          auto_select: false,
          template_name: 'Template2',
          confidence: 55,
          reason: 'The closest fingerprint is ambiguous.'
        }
      });
    }
    return Promise.resolve({ data: {} });
  });
  const file = new File(['dummy content'], 'unknown.pdf', { type: 'application/pdf' });
  fireEvent.change(screen.getByLabelText(/select file/i), { target: { files: [file] } });

  expect(await screen.findByText(/manual confirmation needed/i)).toBeInTheDocument();
  expect(screen.getByText(/closest match: Template2 \(55%\)/i)).toBeInTheDocument();
  expect(screen.getByRole('button', { name: /submit metadata validation/i })).toBeDisabled();

  fireEvent.change(screen.getByRole('textbox', { name: /search/i }), { target: { value: 'Template1' } });
  fireEvent.click(await screen.findByText('Template1'));

  expect(screen.getByRole('button', { name: /submit metadata validation/i })).toBeEnabled();
  expect(screen.getByText(/manual selection/i)).toBeInTheDocument();
});

test('page contains a file input', () => {

  const fileInputElement = screen.getByLabelText(/select file/i);

  expect(fileInputElement).toBeInTheDocument();
  expect(fileInputElement.getAttribute('type')).toBe('file');
  expect(fileInputElement).toHaveAttribute('multiple');
});

test('selected documents can be removed from the analysis queue', async () => {
  const first = new File(['one'], 'one.pdf', { type: 'application/pdf' });
  const second = new File(['two'], 'two.pdf', { type: 'application/pdf' });
  fireEvent.change(screen.getByLabelText(/select files/i), { target: { files: [first, second] } });

  expect(await screen.findByText(/2 pdfs selected/i)).toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: /remove one\.pdf/i }));

  expect(await screen.findByText(/1 pdf selected/i)).toBeInTheDocument();
  expect(screen.queryByText('one.pdf', { exact: true })).not.toBeInTheDocument();
  expect(screen.getByText('two.pdf', { exact: true })).toBeInTheDocument();
});

test('multiple PDFs can be selected and validated as an independent batch', async () => {
  axios.post.mockImplementation((url, formData) => {
    if (url.endsWith('/detect_template')) {
      const file = formData.get('file');
      const isPaystub = file.name.includes('two');
      return Promise.resolve({ data: {
        auto_select: true,
        template_name: isPaystub ? 'Template3' : 'Template1',
        category: isPaystub ? 'Paystubs & Earnings' : 'Bank Statements',
        document_class: isPaystub ? 'Paystub / Earning Statement' : 'Bank Statement',
        confidence: 92
      } });
    }
    if (url.endsWith('/validate_metadata')) {
      const file = formData.get('file');
      return Promise.resolve({ data: { final_validation_results: { valid: file.name.includes('one') ? 'Pass' : 'FDR' }, template_rule_set_validation_results: [] } });
    }
    return Promise.resolve({ data: {} });
  });

  const first = new File(['one'], 'one.pdf', { type: 'application/pdf' });
  const second = new File(['two'], 'two.pdf', { type: 'application/pdf' });
  fireEvent.change(screen.getByLabelText(/select files/i), { target: { files: [first, second] } });

  expect(await screen.findByText(/2 pdfs selected/i)).toBeInTheDocument();
  await waitFor(() => {
    expect(screen.getByLabelText(/template for one\.pdf/i)).toHaveValue('Template1');
    expect(screen.getByLabelText(/template for two\.pdf/i)).toHaveValue('Template3');
  });
  fireEvent.click(screen.getByRole('button', { name: /validate 2 documents/i }));

  expect(await screen.findByRole('tab', { name: /one\.pdf.*socr: pass/i })).toBeInTheDocument();
  const secondResult = screen.getByRole('tab', { name: /two\.pdf.*socr: fdr/i });
  expect(secondResult).toBeInTheDocument();
  fireEvent.click(secondResult);
  expect(secondResult).toHaveAttribute('aria-selected', 'true');

  const validationCalls = axios.post.mock.calls.filter(([url]) => url.endsWith('/validate_metadata'));
  expect(validationCalls).toHaveLength(2);
  expect(validationCalls[0][1].get('template')).toBe('Template1');
  expect(validationCalls[1][1].get('template')).toBe('Template3');
});

test('an ambiguous batch item requires manual selection only for that PDF', async () => {
  axios.post.mockImplementation((url, formData) => {
    if (url.endsWith('/detect_template')) {
      const file = formData.get('file');
      if (file.name.includes('unknown')) {
        return Promise.resolve({ data: { auto_select: false, template_name: 'Template2', confidence: 51, reason: 'Ambiguous fingerprint.' } });
      }
      return Promise.resolve({ data: { auto_select: true, template_name: 'Template1', category: 'Bank Statements', document_class: 'Bank Statement', confidence: 92 } });
    }
    if (url.endsWith('/validate_metadata')) {
      return Promise.resolve({ data: { final_validation_results: { valid: 'Pass' }, template_rule_set_validation_results: [] } });
    }
    return Promise.resolve({ data: {} });
  });

  const known = new File(['known'], 'known.pdf', { type: 'application/pdf' });
  const unknown = new File(['unknown'], 'unknown.pdf', { type: 'application/pdf' });
  fireEvent.change(screen.getByLabelText(/select files/i), { target: { files: [known, unknown] } });

  await waitFor(() => expect(screen.getByLabelText(/template for known\.pdf/i)).toHaveValue('Template1'));
  expect(screen.getByLabelText(/template for unknown\.pdf/i)).toHaveValue('');
  expect(screen.getByText(/manual selection required/i)).toBeInTheDocument();
  expect(screen.getByRole('button', { name: /validate 2 documents/i })).toBeDisabled();

  fireEvent.change(screen.getByLabelText(/template for unknown\.pdf/i), { target: { value: 'Template3' } });
  expect(screen.getByRole('button', { name: /validate 2 documents/i })).toBeEnabled();
});

test('workspace is SOCR-only and includes the metadata validator', () => {
  expect(screen.getByText(/socr api v2 rule engine metadata inspector/i)).toBeInTheDocument();
  expect(screen.getByText(/metadata validator/i)).toBeInTheDocument();
  expect(screen.queryByText(/fraudguard/i)).not.toBeInTheDocument();
  expect(screen.queryByText(/socr vs/i)).not.toBeInTheDocument();
});


test('API endpoint is called with the selected file when the submit button is pressed', async () => {
  const searchInputElement = screen.getByRole('textbox', { name: /search/i });
  const fileInputElement = screen.getByLabelText(/select file/i);
  const buttonElement = screen.getByRole('button', { name: /submit/i });

  const file = new File(['dummy content'], 'example.pdf', { type: 'application/pdf' });
  await waitFor(() => {
    fireEvent.change(fileInputElement, { target: { files: [file] } });
  })
  await screen.findByText(/auto-selected Template1/i);

  await waitFor(() => {
    fireEvent.change(searchInputElement, { target: { value: 'Tem' } });
  })

  await waitFor(() => {
    fireEvent.click(screen.getByText("Template1"))
  })


  axios.post.mockResolvedValue({ data: 'success' });

  await waitFor(() => {
    fireEvent.click(buttonElement);
  })


  expect(axios.post).toHaveBeenCalledWith('http://localhost:5000/validate_metadata', expect.any(FormData));
  const validationCall = axios.post.mock.calls.find(([url]) => url.endsWith('/validate_metadata'));
  const formData = validationCall[1];
  expect(formData.get('file')).toBe(file);
  expect(formData.get('template')).toBe("Template1")
});

test('API response is displayed on the page after file upload, and button to request highlighted fonts exists', async () => {

  const fileInputElement = screen.getByLabelText(/select file/i);
  const buttonElement = screen.getByRole('button', { name: /submit/i });

  const file = new File(['dummy content'], 'example.pdf', { type: 'application/pdf' });
  await waitFor(() => {
    fireEvent.change(fileInputElement, { target: { files: [file] } });
  })
  await screen.findByText(/auto-selected Template1/i);

  const apiResponse = { "template_rule_set_results": 'File uploaded successfully', "final_validation_results":{} };
  axios.post.mockResolvedValue({ data: apiResponse });

  await waitFor(() => {
    fireEvent.click(buttonElement);
  })

  await waitFor(() => {
    const responseElement = screen.getByText(/final_validation_results/i);
    expect(responseElement).toBeInTheDocument();
    const highlightFontsButton = screen.getByRole('button', { name: /get highlighted file/i})
    expect(highlightFontsButton).toBeInTheDocument();
  });
});

test('page contains a search textbox that autocompletes based on a list of strings from an API call', async () => {
  const searchInputElement = screen.getByRole('textbox', { name: /search/i });
  expect(searchInputElement).toBeInTheDocument();

  await waitFor(() => {
    fireEvent.change(searchInputElement, { target: { value: 'Tem' } });
  })

  await waitFor(() => {
    templateNames.forEach(name => {
      expect(screen.getByText(name)).toBeInTheDocument();
    });
  });
  expect(axios.get).toHaveBeenCalledWith('http://localhost:5000/template_names');
});


test('page contains a search textbox, that once an item is clicked, that item becomes selected', async () => {
  const searchInputElement = screen.getByRole('textbox', { name: /search/i });
  expect(searchInputElement).toBeInTheDocument();

  await waitFor(() => {
    fireEvent.change(searchInputElement, { target: { value: 'Tem' } });
  })

  await waitFor(() => {
    fireEvent.click(screen.getByText("Template1"))
  })

  await waitFor(() => {
    expect(screen.queryByText("Template2")).not.toBeInTheDocument();
    expect(screen.queryByText("Template3")).not.toBeInTheDocument();
    expect(searchInputElement.value).toBe("Template1");
  });
})


test('get highlighted file button makes request to get the highlighted file with the fonts in the response message and the same file', async () => {
  const searchInputElement = screen.getByRole('textbox', { name: /search/i });
  const fileInputElement = screen.getByLabelText(/select file/i);
  const submitButton = screen.getByRole('button', { name: /submit/i });

  const file = new File(['dummy content'], 'example.pdf', { type: 'application/pdf' });
  await waitFor(() => {
    fireEvent.change(fileInputElement, { target: { files: [file] } });
  })
  await screen.findByText(/auto-selected Template1/i);
  await waitFor(() => {
    fireEvent.change(searchInputElement, { target: { value: 'Tem' } });
  })
  await waitFor(() => {
    fireEvent.click(screen.getByText("Template1"))
  })


  const apiResponse = { "template_rule_set_validation_results": [{"fonts":{"additional_fonts":[{"name":"Helvetica"}]}}], "final_validation_results":{} };
  axios.post.mockResolvedValue({ data: apiResponse });

  await waitFor(() => {
    fireEvent.click(submitButton);
  })

  const getHighlightedFileButton = await screen.findByRole('button', { name: /get highlighted file/i });
  await waitFor(() => {
    fireEvent.click(getHighlightedFileButton)
  })


  expect(axios.post).toHaveBeenCalledWith('http://localhost:5000/highlight_fonts', expect.any(FormData), { responseType: 'blob' });
  const highlightCall = axios.post.mock.calls.find(([url]) => url.endsWith('/highlight_fonts'));
  const formData = highlightCall[1];
  expect(formData.get('file')).toBe(file);
  expect(formData.get('fonts')).toBe("Helvetica")
})

test('get highlighted file button makes request to get the highlighted file with the fonts in the response message and the same file', async () => {
  const searchInputElement = screen.getByRole('textbox', { name: /search/i });
  const fileInputElement = screen.getByLabelText(/select file/i);
  const submitButton = screen.getByRole('button', { name: /submit/i });

  const file = new File(['dummy content'], 'example.pdf', { type: 'application/pdf' });
  await waitFor(() => {
    fireEvent.change(fileInputElement, { target: { files: [file] } });
  })
  await screen.findByText(/auto-selected Template1/i);
  await waitFor(() => {
    fireEvent.change(searchInputElement, { target: { value: 'Tem' } });
  })
  await waitFor(() => {
    fireEvent.click(screen.getByText("Template1"))
  })


  const apiResponse = { "template_rule_set_validation_results": [{"fonts":{"additional_fonts":[{"name":"Arial"}]}}], "final_validation_results":{} };
  axios.post.mockResolvedValue({ data: apiResponse });

  await waitFor(() => {
    fireEvent.click(submitButton);
  })

  const getHighlightedFileButton = await screen.findByRole('button', { name: /get highlighted file/i });
  await waitFor(() => {
    fireEvent.click(getHighlightedFileButton)
  })


  expect(axios.post).toHaveBeenCalledWith('http://localhost:5000/highlight_fonts', expect.any(FormData), { responseType: 'blob' });
  const highlightCall = axios.post.mock.calls.find(([url]) => url.endsWith('/highlight_fonts'));
  const formData = highlightCall[1];
  expect(formData.get('file')).toBe(file);
  expect(formData.get('fonts')).toBe("Arial")
})

test('rejects non-PDF files before validation', async () => {
  const fileInputElement = screen.getByLabelText(/select file/i);
  const buttonElement = screen.getByRole('button', { name: /submit/i });
  const file = new File(['plain text'], 'notes.txt', { type: 'text/plain' });

  fireEvent.change(fileInputElement, { target: { files: [file] } });

  expect(await screen.findByRole('alert')).toHaveTextContent(/please select a pdf/i);
  expect(buttonElement).toBeDisabled();
});

test('raw data text uses a simple report without decorative separator lines', async () => {
  const file = new File(['dummy content'], 'example.pdf', { type: 'application/pdf' });
  fireEvent.change(screen.getByLabelText(/select file/i), { target: { files: [file] } });
  await screen.findByText(/auto-selected Template1/i);
  axios.post.mockResolvedValue({
    data: {
      final_validation_results: {
        valid: 'Pass',
        validation_message_code: 'MSG_VALID_FILE'
      },
      template_rule_set_validation_results: []
    }
  });

  fireEvent.click(screen.getByRole('button', { name: /submit metadata validation/i }));
  await screen.findByText(/metadata validated successfully/i);
  fireEvent.click(screen.getByRole('button', { name: /raw data text/i }));

  const report = screen.getByText(/document metadata validation report/i);
  expect(report).toHaveTextContent(/overall status: pass/i);
  expect(report.textContent).not.toMatch(/={3,}|-{3,}/);
});

test('explainability preview shows expected, found, why, severity, and decisive rules', async () => {
  const file = new File(['dummy content'], 'example.pdf', { type: 'application/pdf' });
  fireEvent.change(screen.getByLabelText(/select file/i), { target: { files: [file] } });
  await screen.findByText(/auto-selected Template1/i);
  axios.post.mockResolvedValue({
    data: {
      final_validation_results: {
        valid: 'Fail',
        validation_message_code: 'MSG_PRODUCER_DOES_NOT_MATCH'
      },
      template_rule_set_validation_results: [{
        template: {
          valid: 'Pass',
          name: 'Template1',
          actual: 'Template1',
          validation_message_code: 'MSG_TEMPLATE_TYPE_MATCH'
        },
        producer: {
          valid: 'Fail',
          name: '^Adobe PDF Library.*',
          actual: 'Microsoft Print to PDF',
          validation_message_code: 'MSG_PRODUCER_DOES_NOT_MATCH'
        }
      }]
    }
  });

  fireEvent.click(screen.getByRole('button', { name: /submit metadata validation/i }));

  expect(await screen.findByText(/explainability preview/i)).toBeInTheDocument();
  expect(screen.getAllByText('Expected').length).toBeGreaterThan(0);
  expect(screen.getAllByText('Found').length).toBeGreaterThan(0);
  expect(screen.getAllByText('Why').length).toBeGreaterThan(0);
  expect(screen.getAllByText('^Adobe PDF Library.*', { exact: true }).length).toBeGreaterThan(0);
  expect(screen.getByText('Microsoft Print to PDF', { exact: true })).toBeInTheDocument();
  expect(screen.getByText(/high severity/i)).toBeInTheDocument();
  expect(screen.getByText(/final decision is driven by: Producer Software Match/i)).toBeInTheDocument();
  expect(screen.getByLabelText(/testing risk score preview/i)).toBeInTheDocument();
  expect(screen.getByLabelText(/risk score 60 out of 100/i)).toBeInTheDocument();
  expect(screen.getByRole('heading', { name: /high risk/i })).toBeInTheDocument();
  expect(screen.getByText(/priority manual review/i)).toBeInTheDocument();
  expect(screen.getByText(/not a fraud probability/i)).toBeInTheDocument();
});

test('document preview tab displays embedded PDF iframe when a PDF is selected', async () => {
  const file = new File(['pdf content'], 'sample_bank_statement.pdf', { type: 'application/pdf' });
  fireEvent.change(screen.getByLabelText(/select file/i), { target: { files: [file] } });
  await screen.findByText(/auto-selected Template1/i);
  axios.post.mockResolvedValue({
    data: {
      final_validation_results: { valid: 'Pass', validation_message_code: 'MSG_VALID_FILE' },
      template_rule_set_validation_results: []
    }
  });
  fireEvent.click(screen.getByRole('button', { name: /submit metadata validation/i }));
  await screen.findByText(/metadata validated successfully/i);

  const previewTabBtn = await screen.findByRole('button', { name: /pdf preview/i });
  fireEvent.click(previewTabBtn);

  expect(await screen.findByText(/document preview — sample_bank_statement\.pdf/i)).toBeInTheDocument();
});

test('document preview tab displays image element when an image file is selected', async () => {
  const file = new File(['image content'], 'sample_paystub.png', { type: 'image/png' });
  fireEvent.change(screen.getByLabelText(/select file/i), { target: { files: [file] } });
  await screen.findByText(/auto-selected Template1/i);
  axios.post.mockResolvedValue({
    data: {
      final_validation_results: { valid: 'Pass', validation_message_code: 'MSG_VALID_FILE' },
      template_rule_set_validation_results: []
    }
  });
  fireEvent.click(screen.getByRole('button', { name: /submit metadata validation/i }));
  await screen.findByText(/metadata validated successfully/i);

  const previewTabBtn = await screen.findByRole('button', { name: /pdf preview/i });
  fireEvent.click(previewTabBtn);

  expect(await screen.findByText(/document preview — sample_paystub\.png/i)).toBeInTheDocument();
});

