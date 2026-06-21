import ReactMarkdown from 'react-markdown';
import ThinkingBlock from './ThinkingBlock';
import ToolCallCard from './ToolCallCard';
import { Avatar } from 'antd';
import { UserOutlined, RobotOutlined } from '@ant-design/icons';
import '../../pages/Chat/Chat.css';

export default function MessageBubble({ message, isSending }) {
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
        
        {message.content ? (
          <div className="message-bubble">
            <ReactMarkdown>{message.content}</ReactMarkdown>
          </div>
        ) : (
          isSending && !isUser && (
            (!message.toolCalls || message.toolCalls.length === 0 || message.toolCalls[message.toolCalls.length - 1].status === 'completed') && (
              <div className="message-bubble thinking-indicator">
                <span className="dot"></span>
                <span className="dot"></span>
                <span className="dot"></span>
                <span style={{ marginLeft: 8, fontSize: '0.9em', color: '#888' }}>思考中...</span>
              </div>
            )
          )
        )}
      </div>

      {isUser && (
        <Avatar className="avatar user-avatar" icon={<UserOutlined />} />
      )}
    </div>
  );
}
