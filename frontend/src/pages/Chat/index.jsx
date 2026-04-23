import React, { useEffect, useRef } from 'react';
import { Layout, Input, Select, Button, Form, message, Tag, Space, Spin } from 'antd';
import { SettingOutlined, LinkOutlined, DisconnectOutlined } from '@ant-design/icons';
import useChatStore from '../../stores/chatStore';
import useSSE from '../../hooks/useSSE';
import MessageBubble from '../../components/Chat/MessageBubble';
import ChatInput from '../../components/Chat/ChatInput';
import { servicesAPI, toolsAPI } from '../../services/api';
import './Chat.css';

const { Sider, Content } = Layout;

export default function Chat() {
  const { 
    messages, 
    isConnected, 
    isSending, 
    config, 
    tools,
    setConfig, 
    setConnected, 
    setTools,
    clearMessages 
  } = useChatStore();
  
  const { sendMessage } = useSSE();
  const [form] = Form.useForm();
  const messagesEndRef = useRef(null);
  const [services, setServices] = React.useState([]);

  useEffect(() => {
    servicesAPI.list().then(res => setServices(res.data)).catch(console.error);
    form.setFieldsValue(config);
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const onConnect = async () => {
    try {
      const values = await form.validateFields();
      Object.keys(values).forEach(k => setConfig(k, values[k]));
      
      if (values.serviceId) {
        const toolsRes = await servicesAPI.getTools(values.serviceId);
        setTools(toolsRes.data.filter(t => t.enabled));
      } else {
        setTools([]);
      }
      
      setConnected(true);
      message.success('配置已保存并连接');
    } catch (e) {
      console.error(e);
    }
  };

  const onDisconnect = () => {
    setConnected(false);
    clearMessages();
    setTools([]);
  };

  return (
    <Layout className="chat-layout">
      <Sider width={320} className="chat-sider" theme="light">
        <div className="sider-header">
          <SettingOutlined /> <span style={{ fontWeight: 600, marginLeft: 8 }}>对话配置</span>
        </div>
        <div className="sider-body">
          <Form form={form} layout="vertical" disabled={isConnected}>
            <Form.Item name="llmApiKey" label="LLM API Key" rules={[{ required: true }]}>
              <Input.Password placeholder="sk-..." />
            </Form.Item>
            <Form.Item name="model" label="模型" initialValue="gpt-4o">
              <Select options={[
                { value: 'gpt-4o', label: 'gpt-4o' },
                { value: 'gpt-4-turbo', label: 'gpt-4-turbo' },
                { value: 'gpt-3.5-turbo', label: 'gpt-3.5-turbo' }
              ]} />
            </Form.Item>
            <Form.Item name="llmBaseUrl" label="LLM Base URL (可选)">
              <Input placeholder="https://api.openai.com/v1" />
            </Form.Item>
            
            <div className="divider">网关与服务配置</div>
            
            <Form.Item name="serviceId" label="挂载微服务">
              <Select 
                allowClear 
                placeholder="选择微服务以挂载工具"
                options={services.map(s => ({ value: s.id, label: s.name }))} 
              />
            </Form.Item>
          </Form>

          <div style={{ marginTop: 24, textAlign: 'center' }}>
            {isConnected ? (
              <Button type="primary" danger block icon={<DisconnectOutlined />} onClick={onDisconnect}>
                断开连接
              </Button>
            ) : (
              <Button type="primary" block icon={<LinkOutlined />} onClick={onConnect}>
                连接并开始测试
              </Button>
            )}
          </div>

          {isConnected && tools.length > 0 && (
            <div className="tools-indicator">
              <div style={{ marginBottom: 12, color: '#666' }}>已挂载工具 ({tools.length})</div>
              <Space size={[0, 8]} wrap>
                {tools.map((t, i) => (
                  <Tag key={t.id} color={i % 2 === 0 ? 'blue' : 'green'}>{t.name}</Tag>
                ))}
              </Space>
            </div>
          )}
        </div>
      </Sider>
      
      <Content className="chat-content">
        <div className="messages-area">
          {messages.length === 0 ? (
            <div className="empty-state">
              <div className="icon">💬</div>
              <h2>AI MCP 网关对话测试</h2>
              <p>配置右侧参数后，即可开始测试大模型工具调用能力。</p>
            </div>
          ) : (
            <div className="messages-list">
              {messages.map(msg => (
                <MessageBubble key={msg.id} message={msg} />
              ))}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>
        <div className="input-area">
          <ChatInput onSend={sendMessage} disabled={!isConnected || isSending} />
        </div>
      </Content>
    </Layout>
  );
}
