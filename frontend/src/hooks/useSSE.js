import useChatStore from '../stores/chatStore';

export default function useSSE() {
  const store = useChatStore();

  const sendMessage = async (message) => {
    const { config } = useChatStore.getState();
    if (!config.llmApiKey) {
      alert('请先配置 LLM API Key');
      return;
    }

    store.addUserMessage(message);
    store.setSending(true);
    store.addAssistantMessage();

    try {
      const response = await fetch('/api/chat/send', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message,
          gateway_url: config.gatewayUrl,
          gateway_api_key: config.gatewayApiKey,
          llm_api_key: config.llmApiKey,
          llm_base_url: config.llmBaseUrl || undefined,
          service_id: config.serviceId || undefined,
          model: config.model,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        let eventType = '';
        for (const line of lines) {
          if (line.startsWith('event: ')) {
            eventType = line.slice(7).trim();
          } else if (line.startsWith('data: ') && eventType) {
            const data = JSON.parse(line.slice(6));
            switch (eventType) {
              case 'thinking':
                store.updateLastAssistant('thinking', data.content);
                break;
              case 'tool_call':
                store.appendToolCall(data);
                break;
              case 'tool_result':
                store.updateToolCall(data.id, { result: data.result, status: data.status, duration_ms: data.duration_ms });
                break;
              case 'message':
                store.updateLastAssistant('content', (useChatStore.getState().messages.findLast(m => m.role === 'assistant')?.content || '') + data.content);
                break;
              case 'session':
                break;
              case 'error':
                store.updateLastAssistant('content', `❌ Error: ${data.message}`);
                break;
              case 'done':
                break;
            }
            eventType = '';
          }
        }
      }
    } catch (err) {
      store.updateLastAssistant('content', `❌ 请求失败: ${err.message}`);
    } finally {
      store.setSending(false);
    }
  };

  return { sendMessage };
}
