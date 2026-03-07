// documentParser.js - PDF and DOCX text extraction
import fs from 'fs';
import path from 'path';

export async function extractTextFromFile(filePath, originalName) {
  const ext = path.extname(originalName || filePath).toLowerCase();

  if (ext === '.pdf') {
    return extractFromPDF(filePath);
  } else if (ext === '.docx' || ext === '.doc') {
    return extractFromDocx(filePath);
  } else {
    return null; // Images and other formats don't get text extraction
  }
}

async function extractFromPDF(filePath) {
  try {
    // Dynamic import to handle ESM/CJS compatibility
    const pdfParse = (await import('pdf-parse/lib/pdf-parse.js')).default;
    const buffer = fs.readFileSync(filePath);
    const data = await pdfParse(buffer);
    return data.text;
  } catch (err) {
    console.error('PDF extraction error:', err.message);
    return `[PDF text extraction failed: ${err.message}]`;
  }
}

async function extractFromDocx(filePath) {
  try {
    const mammoth = await import('mammoth');
    const result = await mammoth.extractRawText({ path: filePath });
    return result.value;
  } catch (err) {
    console.error('DOCX extraction error:', err.message);
    return `[DOCX text extraction failed: ${err.message}]`;
  }
}
