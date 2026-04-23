import React from 'react';
import { Tag, Spin } from 'antd';
import { ToolOutlined, CheckCircleOutlined, SyncOutlined } from '@ant-design/icons';
import './Chat.css';

export default function ToolCallCard({ toolCall }) {
  const { name, arguments: args, result, status, duration_ms } = toolCall;

  return (
    <div className={`tool-call-card ${status}`}>
      <div className="tool-call-header">
        <div className="title">
          <ToolOutlined className="icon" /> 
          <strong>工具调用</strong> 
          <Tag color="blue" className="name-tag">{name}</Tag>
        </div>
        <div className="status">
          {status === 'calling' ? (
            <Tag icon={<SyncOutlined spin />} color="processing">调用中...</Tag>
          ) : (
            <Tag icon={<CheckCircleOutlined />} color="success">完成 {duration_ms && `(${duration_ms}ms)`}</Tag>
          )}
        </div>
      </div>
      
      <div className="tool-call-body">
        <div className="section parameters">
          <div className="section-title">参数:</div>
          <pre><code>{JSON.stringify(args, null, 2)}</code></pre>
        </div>
        
        {result && (
          <div className="section result">
            <div className="section-title">结果:</div>
            <pre><code>{JSON.stringify(result, null, 2)}</code></pre>
          </div>
        )}
      </div>
    </div>
  );
}
