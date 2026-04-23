import { create } from 'zustand';

const useChatStore = create((set, get) => ({
  messages: [],
  isConnected: false,
  isSending: false,
  config: {
    gatewayUrl: 'http://127.0.0.1:8777',
    gatewayApiKey: '',
    llmApiKey: '',
    llmBaseUrl: '',
    serviceId: '',
    model: 'gpt-4o',
  },
  tools: [],

  setConfig: (key, value) => set((s) => ({ config: { ...s.config, [key]: value } })),
  setTools: (tools) => set({ tools }),
  setConnected: (v) => set({ isConnected: v }),
  setSending: (v) => set({ isSending: v }),

  addUserMessage: (content) => set((s) => ({
    messages: [...s.messages, {
      id: Date.now().toString(),
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
    }],
  })),

  addAssistantMessage: () => {
    const id = Date.now().toString();
    set((s) => ({
      messages: [...s.messages, {
        id,
        role: 'assistant',
        content: '',
        thinking: null,
        toolCalls: [],
        timestamp: new Date().toISOString(),
      }],
    }));
    return id;
  },

  updateLastAssistant: (field, value) => set((s) => {
    const msgs = [...s.messages];
    const last = msgs.findLast((m) => m.role === 'assistant');
    if (last) last[field] = value;
    return { messages: msgs };
  }),

  appendToolCall: (tc) => set((s) => {
    const msgs = [...s.messages];
    const last = msgs.findLast((m) => m.role === 'assistant');
    if (last) {
      if (!last.toolCalls) last.toolCalls = [];
      last.toolCalls = [...last.toolCalls, tc];
    }
    return { messages: msgs };
  }),

  updateToolCall: (tcId, updates) => set((s) => {
    const msgs = [...s.messages];
    const last = msgs.findLast((m) => m.role === 'assistant');
    if (last && last.toolCalls) {
      last.toolCalls = last.toolCalls.map((tc) =>
        tc.id === tcId ? { ...tc, ...updates } : tc
      );
    }
    return { messages: msgs };
  }),

  clearMessages: () => set({ messages: [] }),
}));

export default useChatStore;
