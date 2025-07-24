const express = require('express');
const router = express.Router();
const auth = require('../middleware/auth');
const sqlite3 = require('sqlite3').verbose();

const db = new sqlite3.Database('users.db');

// GET all visited chapters for the user
router.get('/', auth, (req, res) => {
  const email = req.user.email;
  db.all('SELECT chapterId FROM visited WHERE email = ?', [email], (err, rows) => {
    if (err) return res.status(500).json({ message: 'DB error' });
    const chapters = rows.map(row => row.chapterId);
    res.json({ visited: chapters });
  });
});

// POST a new visited chapter
router.post('/', auth, (req, res) => {
  const email = req.user.email;
  const { chapterId } = req.body;

  if (!chapterId) return res.status(400).json({ message: 'chapterId required' });

  db.run(
    'INSERT OR IGNORE INTO visited (email, chapterId) VALUES (?, ?)',
    [email, chapterId],
    (err) => {
      if (err) return res.status(500).json({ message: 'Insert failed' });
      res.json({ message: 'Chapter marked as visited' });
    }
  );
});

module.exports = router;
