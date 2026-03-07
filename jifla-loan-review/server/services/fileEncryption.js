// fileEncryption.js - AES-256-GCM encrypt/decrypt for stored files
// Required by GLBA Safeguards Rule and Georgia Data Breach Notification law.
// Encrypted files provide safe harbor under O.C.G.A. § 10-1-912.

import crypto from 'crypto';
import fs from 'fs';
import path from 'path';

const ALGORITHM = 'aes-256-gcm';
const KEY_LENGTH = 32; // 256 bits
const IV_LENGTH = 16;  // 128 bits
const AUTH_TAG_LENGTH = 16;

function getKey() {
  const keyHex = process.env.FILE_ENCRYPTION_KEY;
  if (!keyHex) {
    console.warn('FILE_ENCRYPTION_KEY not set - files stored unencrypted. This is a compliance risk.');
    return null;
  }
  return Buffer.from(keyHex, 'hex').slice(0, KEY_LENGTH);
}

/**
 * Encrypt a file in place, returning the encrypted file path.
 * Original file is securely overwritten and replaced with encrypted version.
 */
export async function encryptFile(filePath) {
  const key = getKey();
  if (!key) {
    // If no key configured, return original path (log warning above)
    return filePath;
  }

  const encPath = filePath + '.enc';
  const iv = crypto.randomBytes(IV_LENGTH);

  const cipher = crypto.createCipheriv(ALGORITHM, key, iv);
  const input = fs.readFileSync(filePath);
  const encrypted = Buffer.concat([cipher.update(input), cipher.final()]);
  const authTag = cipher.getAuthTag();

  // Write: [IV (16 bytes)] + [AuthTag (16 bytes)] + [Encrypted data]
  const output = Buffer.concat([iv, authTag, encrypted]);
  fs.writeFileSync(encPath, output);

  // Securely overwrite and delete original
  const zeros = Buffer.alloc(input.length, 0);
  fs.writeFileSync(filePath, zeros);
  fs.unlinkSync(filePath);

  return encPath;
}

/**
 * Decrypt a file, returning the decrypted buffer.
 */
export function decryptFile(encPath) {
  const key = getKey();
  if (!key) {
    // Return raw file if encryption not configured
    return fs.readFileSync(encPath);
  }

  const data = fs.readFileSync(encPath);
  const iv = data.slice(0, IV_LENGTH);
  const authTag = data.slice(IV_LENGTH, IV_LENGTH + AUTH_TAG_LENGTH);
  const encrypted = data.slice(IV_LENGTH + AUTH_TAG_LENGTH);

  const decipher = crypto.createDecipheriv(ALGORITHM, key, iv);
  decipher.setAuthTag(authTag);

  return Buffer.concat([decipher.update(encrypted), decipher.final()]);
}

/**
 * Securely delete a file (overwrite before unlink).
 */
export function secureDelete(filePath) {
  if (!fs.existsSync(filePath)) return;

  try {
    const stat = fs.statSync(filePath);
    // Single-pass zero-fill (minimum requirement)
    const zeros = Buffer.alloc(stat.size, 0);
    fs.writeFileSync(filePath, zeros);
    fs.unlinkSync(filePath);
  } catch (err) {
    console.error(`Secure delete failed for ${filePath}:`, err.message);
  }
}
