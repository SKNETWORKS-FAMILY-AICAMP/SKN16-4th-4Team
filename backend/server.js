const express = require('express');
const cors = require('cors');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Health check endpoint
app.get('/health', (req, res) => {
  res.status(200).json({
    status: 'OK',
    message: '4th Project MVP is running',
    timestamp: new Date().toISOString()
  });
});

// API Routes
app.get('/api/hello', (req, res) => {
  res.json({
    message: '4차 프로젝트 MVP에 오신 것을 환영합니다!',
    version: '1.0.0'
  });
});

// Sample data endpoint
app.get('/api/data', (req, res) => {
  res.json({
    items: [
      { id: 1, name: 'Item 1', description: 'First sample item' },
      { id: 2, name: 'Item 2', description: 'Second sample item' },
      { id: 3, name: 'Item 3', description: 'Third sample item' }
    ]
  });
});

// POST endpoint example
app.post('/api/data', (req, res) => {
  const { name, description } = req.body;
  
  if (!name || !description) {
    return res.status(400).json({
      error: 'Name and description are required'
    });
  }
  
  res.status(201).json({
    message: 'Data created successfully',
    data: {
      id: Date.now(),
      name,
      description,
      createdAt: new Date().toISOString()
    }
  });
});

// 404 handler
app.use((req, res) => {
  res.status(404).json({
    error: 'Route not found'
  });
});

// Error handler
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({
    error: 'Internal server error'
  });
});

app.listen(PORT, () => {
  console.log(`🚀 Server is running on port ${PORT}`);
  console.log(`📍 Health check: http://localhost:${PORT}/health`);
});
