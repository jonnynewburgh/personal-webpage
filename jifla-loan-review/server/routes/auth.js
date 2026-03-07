// auth.js - Login, session management
import express from 'express';
import bcrypt from 'bcryptjs';
import db from '../db.js';

const router = express.Router();

router.post('/login', async (req, res) => {
  const { username, password } = req.body;

  if (!username || !password) {
    return res.status(400).json({ error: 'Username and password required' });
  }

  const user = db.prepare('SELECT id, username, password_hash FROM users WHERE username = ?').get(username);

  if (!user) {
    // Constant-time comparison to prevent username enumeration
    await bcrypt.compare(password, '$2b$12$invalidhashtopreventtimingattack.......invalid');
    return res.status(401).json({ error: 'Invalid credentials' });
  }

  const valid = await bcrypt.compare(password, user.password_hash);
  if (!valid) {
    return res.status(401).json({ error: 'Invalid credentials' });
  }

  // Update last login
  db.prepare('UPDATE users SET last_login = datetime(\'now\') WHERE id = ?').run(user.id);

  req.session.userId = user.id;
  req.session.username = user.username;

  return res.json({ success: true, username: user.username });
});

router.post('/logout', (req, res) => {
  req.session.destroy((err) => {
    if (err) return res.status(500).json({ error: 'Logout failed' });
    res.clearCookie('connect.sid');
    return res.json({ success: true });
  });
});

router.get('/me', (req, res) => {
  if (req.session?.userId) {
    return res.json({ authenticated: true, username: req.session.username });
  }
  return res.json({ authenticated: false });
});

export default router;
