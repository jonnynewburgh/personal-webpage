// accessLogger.js - GLBA-required audit trail for data access
import db from '../db.js';

export function logAccess({ userId, applicationId, action, ipAddress }) {
  try {
    db.prepare(`
      INSERT INTO access_log (user_id, application_id, action, ip_address)
      VALUES (?, ?, ?, ?)
    `).run(userId || null, applicationId || null, action, ipAddress || null);
  } catch (err) {
    // Log errors shouldn't crash the app, but we should note them
    console.error('Access log error:', err.message);
  }
}

export function getAccessLog(applicationId) {
  return db.prepare(`
    SELECT al.id, al.action, al.accessed_at, al.ip_address, u.username
    FROM access_log al
    LEFT JOIN users u ON al.user_id = u.id
    WHERE al.application_id = ?
    ORDER BY al.accessed_at DESC
  `).all(applicationId);
}
