import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import "@testing-library/jest-dom"
import { act } from 'react';
import App from './App';
import axios from 'axios';

jest.mock('axios');


var templateNames = []
beforeEach(async () => {
  templateNames = ['Template1', 'Template2', 'Template3'];
  axios.get.mockResolvedValue({ data: templateNames });

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

  const file = new File(['dummy content'], 'example.txt', { type: 'text/plain' });
  await waitFor(() => {
    fireEvent.change(fileInputElement, { target: { files: [file] } });
  })

  expect(buttonElement).toBeEnabled();
});

test('page contains a file input', () => {

  const fileInputElement = screen.getByLabelText(/select file/i);

  expect(fileInputElement).toBeInTheDocument();
  expect(fileInputElement.getAttribute('type')).toBe('file');
});

test('API endpoint is called with the selected file when the submit button is pressed', async () => {
  const searchInputElement = screen.getByRole('textbox', { name: /search/i });
  const fileInputElement = screen.getByLabelText(/select file/i);
  const buttonElement = screen.getByRole('button', { name: /submit/i });

  const file = new File(['dummy content'], 'example.txt', { type: 'text/plain' });
  await waitFor(() => {
    fireEvent.change(fileInputElement, { target: { files: [file] } });
  })

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
  const formData = axios.post.mock.calls[0][1];
  expect(formData.get('file')).toBe(file);
  expect(formData.get('template')).toBe("Template1")
});

test('API response is displayed on the page after file upload, and button to request highlighted fonts exists', async () => {

  const fileInputElement = screen.getByLabelText(/select file/i);
  const buttonElement = screen.getByRole('button', { name: /submit/i });

  const file = new File(['dummy content'], 'example.txt', { type: 'text/plain' });
  await waitFor(() => {
    fireEvent.change(fileInputElement, { target: { files: [file] } });
  })

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

  const file = new File(['dummy content'], 'example.txt', { type: 'text/plain' });
  await waitFor(() => {
    fireEvent.change(fileInputElement, { target: { files: [file] } });
  })
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

  const getHighlightedFileButton = screen.getByRole('button', { name: /get highlighted file/i });
  await waitFor(() => {
    fireEvent.click(getHighlightedFileButton)
  })


  expect(axios.post).toHaveBeenCalledWith('http://localhost:5000/highlight_fonts', expect.any(FormData));
  const formData = axios.post.mock.calls[1][1];
  expect(formData.get('file')).toBe(file);
  expect(formData.get('fonts')).toBe("Helvetica")
})

test('get highlighted file button makes request to get the highlighted file with the fonts in the response message and the same file', async () => {
  const searchInputElement = screen.getByRole('textbox', { name: /search/i });
  const fileInputElement = screen.getByLabelText(/select file/i);
  const submitButton = screen.getByRole('button', { name: /submit/i });

  const file = new File(['dummy content'], 'example.txt', { type: 'text/plain' });
  await waitFor(() => {
    fireEvent.change(fileInputElement, { target: { files: [file] } });
  })
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

  const getHighlightedFileButton = screen.getByRole('button', { name: /get highlighted file/i });
  await waitFor(() => {
    fireEvent.click(getHighlightedFileButton)
  })


  expect(axios.post).toHaveBeenCalledWith('http://localhost:5000/highlight_fonts', expect.any(FormData));
  const formData = axios.post.mock.calls[1][1];
  expect(formData.get('file')).toBe(file);
  expect(formData.get('fonts')).toBe("Arial")
})
