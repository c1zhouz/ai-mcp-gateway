import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { DownOutlined, RightOutlined } from '@ant-design/icons';
import '../../pages/Chat/Chat.css';

export default function ThinkingBlock({ content }) {
  const [expanded, setExpanded] = useState(false);

  if (!content) return null;

  return (
    <div className={`thinking-block ${expanded ? 'expanded' : ''}`}>
      <div 
        className="thinking-header" 
        onClick={() => setExpanded(!expanded)}
      >
        <span className="icon">{expanded ? <DownOutlined /> : <RightOutlined />}</span>
        <span className="title">📋 思考过程</span>
      </div>
      {expanded && (
        <div className="thinking-content">
          <ReactMarkdown>{content}</ReactMarkdown>
        </div>
      )}
    </div>
  );
}
