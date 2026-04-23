import React, { useState } from 'react';
import { Input, Button } from 'antd';
import { SendOutlined } from '@ant-design/icons';
import './Chat.css';

export default function ChatInput({ onSend, disabled }) {
  const [value, setValue] = useState('');

  const handleSend = () => {
    if (value.trim() && !disabled) {
      onSend(value);
      setValue('');
    }
  };

  const onKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="chat-input-wrapper">
      <Input.TextArea
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={onKeyDown}
        placeholder="输入消息，Enter 发送，Shift + Enter 换行..."
        autoSize={{ minRows: 2, maxRows: 6 }}
        disabled={disabled}
        className="chat-textarea"
      />
      <Button 
        type="primary" 
        icon={<SendOutlined />} 
        onClick={handleSend}
        disabled={!value.trim() || disabled}
        className="send-button"
      >
        发送
      </Button>
    </div>
  );
}
