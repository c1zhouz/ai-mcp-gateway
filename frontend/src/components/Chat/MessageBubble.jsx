import React from 'react';
import ReactMarkdown from 'react-markdown';
import ThinkingBlock from './ThinkingBlock';
import ToolCallCard from './ToolCallCard';
import { Avatar } from 'antd';
import { UserOutlined, RobotOutlined } from '@ant-design/icons';
import './Chat.css';

export default function MessageBubble({ message }) {
  const isUser = message.role === 'user';

  return (
    <div className={`message-wrapper ${isUser ? 'user' : 'assistant'}`}>
      {!isUser && (
        <Avatar className="avatar assistant-avatar" icon={<RobotOutlined />} />
      )}
      
      <div className="message-content" style={{ width: isUser ? 'auto' : '100%' }}>
        {!isUser && message.thinking && (
          <ThinkingBlock content={message.thinking} />
        )}
        
        {!isUser && message.toolCalls && message.toolCalls.map((tc, idx) => (
          <ToolCallCard key={tc.id || idx} toolCall={tc} />
        ))}
        
        {message.content && (
          <div className="message-bubble">
            <ReactMarkdown>{message.content}</ReactMarkdown>
          </div>
        )}
      </div>

      {isUser && (
        <Avatar className="avatar user-avatar" icon={<UserOutlined />} />
      )}
    </div>
  );
}
