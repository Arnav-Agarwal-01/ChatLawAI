import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000',
});

export const startConsultation = async (query) => {
  try {
    const response = await api.post('/consult/start', {
      query,
      max_turns: 7,
    });
    return response.data;
  } catch (error) {
    console.log('Error starting consultation:', error);
    throw error;
  }
};

export const sendAnswer = async (sessionId, answer) => {
  try {
    console.log('Sending to backend:', { session_id: sessionId, answer });
    const response = await api.post('/consult/answer', {
      session_id: sessionId,
      answer,
    });
    console.log('Backend responded with:', response.data);
    return response.data;
  } catch (error) {
    console.log('Error sending answer:', error);
    throw error;
  }
};

