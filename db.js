const sqlite3 = require('sqlite3').verbose();
const db = new sqlite3.Database('./users.db');

// Register user (insert)
function registerUser(email, password) {
  const query = `INSERT INTO users (email, password) VALUES (?, ?)`;
  db.run(query, [email, password], function (err) {
    if (err) {
      console.error("❌ Register failed:", err.message);
    } else {
      console.log("✅ User registered with ID:", this.lastID);
    }
  });
}

// Get user by email (for login)
function getUserByEmail(email, callback) {
  const query = `SELECT * FROM users WHERE email = ?`;
  db.get(query, [email], (err, row) => {
    if (err) {
      console.error("❌ Query failed:", err.message);
      callback(null);
    } else {
      callback(row);
    }
  });
}

module.exports = { registerUser, getUserByEmail };
