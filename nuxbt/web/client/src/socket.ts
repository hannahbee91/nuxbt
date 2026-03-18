import { io } from 'socket.io-client';

const URL = import.meta.env.PROD ? '/' : '/'; // Development proxy handles the URL

export const socket = io(URL, {
  transports: ['polling', 'websocket'],
  autoConnect: true,
});
