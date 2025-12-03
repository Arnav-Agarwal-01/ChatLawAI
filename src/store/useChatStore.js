import { create } from 'zustand';

const useChatStore = create((set) => ({
  sessionId: null,
  messages: [],
  partialReport: '',
  isLoading: false,
  questionCount: 0,

  startSession: (id) => set({ sessionId: id }),

  addMessage: (role, text) =>
    set((state) => {
      // Increment question count when adding a bot message
      const newQuestionCount = role === 'bot' ? state.questionCount + 1 : state.questionCount;
      console.log(`Adding ${role} message. Question count: ${newQuestionCount}`);
      
      return {
        messages: [...state.messages, { role, text }],
        questionCount: newQuestionCount,
      };
    }),

  setPartialReport: (text) => set({ partialReport: text }),

  setLoading: (bool) => set({ isLoading: bool }),

  reset: () =>
    set({
      sessionId: null,
      messages: [],
      partialReport: '',
      isLoading: false,
      questionCount: 0,
    }),
}));

export default useChatStore;

