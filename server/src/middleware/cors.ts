import cors from 'cors';

const ALLOWED_ORIGINS = [
  'http://localhost:5174',  // Vite dev
  'http://localhost:8081',  // Docker nginx frontend
];

const corsMiddleware = cors({
  origin: (origin, callback) => {
    // Allow requests with no origin (curl, server-to-server)
    if (!origin || ALLOWED_ORIGINS.includes(origin)) {
      callback(null, true);
    } else {
      callback(new Error(`CORS blocked: ${origin}`));
    }
  },
  credentials: true,
});

export default corsMiddleware;
