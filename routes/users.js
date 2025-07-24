const express = require('express');
const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');
const router = express.Router();
const auth = require('../middleware/auth');

require('dotenv').config();
const SECRET_KEY = process.env.JWT_SECRET;

// TEMP in-memory user "database"
const users = [];


router.post('/register', async (req, res) => {
  const { email, password } = req.body;

  const exists = users.find(user => user.email === email);
  if (exists) return res.status(400).json({ message: 'User already exists' });

  const hashedPassword = await bcrypt.hash(password, 10);
  users.push({ email, password: hashedPassword });

  res.json({ message: 'User registered successfully' });
});

router.post('/login', async (req, res) => {
  const { email, password } = req.body;

  const user = users.find(user => user.email === email);
  if (!user) return res.status(400).json({ message: 'Invalid credentials' });

  const valid = await bcrypt.compare(password, user.password);
  if (!valid) return res.status(400).json({ message: 'Invalid credentials' });

  const token = jwt.sign({ email: user.email }, SECRET_KEY, { expiresIn: '1h' });
  res.json({ token });
});

router.get('/me', auth, (req, res) => {
  res.json({
    message: 'You are logged in!',
    user: req.user
  });
});

module.exports = router;
