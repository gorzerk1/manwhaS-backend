const jwt = require('jsonwebtoken');
require('dotenv').config();

const SECRET_KEY = process.env.JWT_SECRET;

function authMiddleware(req, res, next) {
  const authHeader = req.headers.authorization;

  if (!authHeader) return res.status(401).json({ message: 'Missing token' });

  const token = authHeader.split(' ')[1]; // Expecting "Bearer <token>"

  try {
    const decoded = jwt.verify(token, SECRET_KEY);
    req.user = decoded; // so we can access req.user.email
    next(); // continue
  } catch (err) {
    res.status(401).json({ message: 'Invalid or expired token' });
  }
}

module.exports = authMiddleware;
