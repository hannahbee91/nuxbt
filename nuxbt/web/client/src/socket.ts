import { io } from 'socket.io-client';

const URL = import.meta.env.PROD ? '/' : '/'; // Development proxy handles the URL

export const socket = io(URL, {
  // The webapp is served by uvicorn through a2wsgi.WSGIMiddleware, which
  // does not support WebSocket. Keep polling so the client does not loop
  // on a failed WebSocket upgrade (HTTP 403).
  transports: ['polling'],
  autoConnect: true,
});
