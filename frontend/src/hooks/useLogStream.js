import { useState, useEffect, useRef } from 'react';

/**
 * useLogStream Hook
 * 订阅后端的 SSE 日志流并管理本地日志状态
 */
export default function useLogStream() {
  const [logs, setLogs] = useState([]);
  const eventSourceRef = useRef(null);

  useEffect(() => {
    // 建立 SSE 连接
    const url = 'http://localhost:8000/api/gateway/logs/stream';
    const es = new EventSource(url);
    eventSourceRef.current = es;

    es.onmessage = (event) => {
      try {
        const logEntry = JSON.parse(event.data);
        setLogs((prev) => {
          const nextLogs = [...prev, logEntry];
          // 最多保留 200 条防止内存溢出
          return nextLogs.slice(-200);
        });
      } catch (err) {
        console.error('解析日志失败:', err);
      }
    };

    es.onerror = (err) => {
      console.error('SSE 连接错误:', err);
      es.close();
    };

    // 组件销毁时关闭连接
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  const clearLogs = () => setLogs([]);

  return { logs, clearLogs };
}
