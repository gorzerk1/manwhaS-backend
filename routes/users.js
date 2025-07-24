const express = require('express');
const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');
const router = express.Router();
const auth = require('../middleware/auth');
require('dotenv').config();

const SECRET_KEY = process.env.JWT_SECRET;
const { registerUser, getUserByUsername } = require('../db'); 

// === Register ===
router.post('/register', async (req, res) => {
  const { username, password } = req.body;

  getUserByUsername(username, async (existingUser) => {
    if (existingUser) {
      return res.status(400).json({ message: 'User already exists' });
    }

    const hashedPassword = await bcrypt.hash(password, 10);
    registerUser(username, hashedPassword);
    res.json({ message: 'User registered successfully' });
  });
});

// === Login ===
router.post('/login', async (req, res) => {
  const { username, password } = req.body;

  getUserByUsername(username, async (user) => {
    if (!user) {
      return res.status(400).json({ message: 'Invalid credentials' });
    }

    const valid = await bcrypt.compare(password, user.password);
    if (!valid) {
      return res.status(400).json({ message: 'Invalid credentials' });
    }

    const token = jwt.sign({ username: user.username }, SECRET_KEY, { expiresIn: '1h' });
    res.json({ token });
  });
});

// === Protected route (JWT token required) ===
router.get('/me', auth, (req, res) => {
  res.json({
    message: 'You are logged in!',
    user: req.user
  });
});

module.exports = router;
