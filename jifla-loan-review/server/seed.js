// seed.js - Create initial admin user via CLI
// Usage: node server/seed.js
import 'dotenv/config';
import bcrypt from 'bcryptjs';
import db from './db.js';
import readline from 'readline';

const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
const ask = (q) => new Promise((resolve) => rl.question(q, resolve));

async function seed() {
  console.log('JIFLA Loan Review Tool - User Setup');
  console.log('=====================================');

  const username = await ask('Enter username: ');
  const password = await ask('Enter password (min 12 characters): ');

  if (password.length < 12) {
    console.error('Password must be at least 12 characters.');
    process.exit(1);
  }

  const hash = await bcrypt.hash(password, 12);

  try {
    const existing = db.prepare('SELECT id FROM users WHERE username = ?').get(username);
    if (existing) {
      db.prepare('UPDATE users SET password_hash = ? WHERE username = ?').run(hash, username);
      console.log(`User "${username}" password updated.`);
    } else {
      db.prepare('INSERT INTO users (username, password_hash) VALUES (?, ?)').run(username, hash);
      console.log(`User "${username}" created successfully.`);
    }
  } catch (err) {
    console.error('Error creating user:', err.message);
    process.exit(1);
  }

  rl.close();
  process.exit(0);
}

seed();
