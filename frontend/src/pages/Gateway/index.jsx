import { useEffect, useRef, useState } from 'react';
import { Tabs, Form, Input, InputNumber, Button, Table, Modal, Tag, Switch, message, Popconfirm, Select, Checkbox, DatePicker, Typography } from 'antd';
import { gatewayAPI } from '../../services/api';
import useLogStream from '../../hooks/useLogStream';
import './Gateway.css';

export default function Gateway() {
  const [configForm] = Form.useForm();
  const [logForm] = Form.useForm();
  const [apiKeys, setApiKeys] = useState([]);
  const [routes, setRoutes] = useState([]);
  const [isKeyModalVisible, setIsKeyModalVisible] = useState(false);
  const [isRouteModalVisible, setIsRouteModalVisible] = useState(false);
  const [keyForm] = Form.useForm();
  const [routeForm] = Form.useForm();
  const [services, setServices] = useState([]);
  const { logs } = useLogStream();
  const logEndRef = useRef(null);

  useEffect(() => {
    if (logEndRef.current) {
      logEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs]);

  useEffect(() => {
    fetchConfig();
    fetchApiKeys();
    fetchRoutes();
    fetchServices();
    // Run once when the gateway page mounts.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function fetchConfig() {
    try {
      const res = await gatewayAPI.getConfig();
      configForm.setFieldsValue(res.data);
      logForm.setFieldsValue(res.data);
    } catch {
      message.error('获取配置失败');
    }
  }

  async function fetchApiKeys() {
    try {
      const res = await gatewayAPI.getApiKeys();
      setApiKeys(res.data);
    } catch {
      message.error('获取API Key失败');
    }
  }

  async function fetchRoutes() {
    try {
      const res = await gatewayAPI.getRoutes();
      setRoutes(res.data);
    } catch {
      message.error('获取路由失败');
    }
  }

  async function fetchServices() {
    try {
      const { servicesAPI } = await import('../../services/api');
      const res = await servicesAPI.list();
      setServices(res.data);
    } catch (error) {
      console.error(error);
    }
  }

  const onSaveConfig = async (values) => {
    try {
      await gatewayAPI.updateConfig(values);
      message.success('配置已保存');
    } catch {
      message.error('保存失败');
    }
  };

  const onCreateKey = async (values) => {
    try {
      const payload = {
        ...values,
        expires_at: values.expires_at ? values.expires_at.toISOString() : null,
      };
      const res = await gatewayAPI.createApiKey(payload);
      
      Modal.success({
        title: 'API Key 创建成功',
        content: (
          <div>
            <p>请妥善保管您的 API Key，关闭此窗口后将无法再次查看完整密钥。</p>
            <div style={{ background: '#f5f5f5', padding: '12px', borderRadius: '4px', marginTop: '16px' }}>
              <Typography.Text copyable style={{ fontFamily: 'monospace', wordBreak: 'break-all' }}>
                {res.data.key_value}
              </Typography.Text>
            </div>
          </div>
        ),
      });
      
      setIsKeyModalVisible(false);
      keyForm.resetFields();
      fetchApiKeys();
    } catch {
      message.error('创建失败');
    }
  };

  const onRevokeKey = async (id) => {
    try {
      await gatewayAPI.deleteApiKey(id);
      message.success('已吊销');
      fetchApiKeys();
    } catch {
      message.error('操作失败');
    }
  };

  const onCreateRoute = async (values) => {
    try {
      await gatewayAPI.createRoute(values);
      message.success('路由创建成功');
      setIsRouteModalVisible(false);
      routeForm.resetFields();
      fetchRoutes();
    } catch {
      message.error('路由创建失败');
    }
  };

  const onDeleteRoute = async (id) => {
    try {
      await gatewayAPI.deleteRoute(id);
      message.success('路由已删除');
      fetchRoutes();
    } catch {
      message.error('删除失败');
    }
  };

  return (
    <div className="gateway-container">
      <Tabs defaultActiveKey="1" type="card">
        <Tabs.TabPane tab="基础配置" key="1">
          <div className="tab-content">
            <Form form={configForm} layout="vertical" onFinish={onSaveConfig} style={{ maxWidth: 600 }}>
              <Form.Item label="网关名称" name="name"><Input /></Form.Item>
              <Form.Item label="监听地址" name="listen_address"><Input /></Form.Item>
              <Form.Item label="端口" name="port"><InputNumber style={{ width: '100%' }} /></Form.Item>
              <Form.Item label="超时时间 (ms)" name="timeout_ms"><InputNumber style={{ width: '100%' }} /></Form.Item>
              <Form.Item label="最大并发数" name="max_concurrency"><InputNumber style={{ width: '100%' }} /></Form.Item>
              <Form.Item>
                <Button type="primary" htmlType="submit">保存配置</Button>
              </Form.Item>
            </Form>
          </div>
        </Tabs.TabPane>
        
        <Tabs.TabPane tab="API Key 管理" key="2">
          <div className="tab-content">
            <Button type="primary" onClick={() => setIsKeyModalVisible(true)} style={{ marginBottom: 16 }}>
              + 创建 API Key
            </Button>
            <Table
              dataSource={apiKeys}
              rowKey="id"
              columns={[
                { title: '名称', dataIndex: 'name' },
                { title: 'Key 值', dataIndex: 'key_value', render: (text) => <code>{text}</code> },
                { title: '权限', dataIndex: 'permissions', render: (perms) => perms.map(p => <Tag key={p} color="blue">{p}</Tag>) },
                { title: '状态', dataIndex: 'status', render: (status) => <Tag color={status === 'active' ? 'green' : 'red'}>{status}</Tag> },
                { title: '创建时间', dataIndex: 'created_at', render: (t) => new Date(t).toLocaleString() },
                {
                  title: '操作',
                  render: (_, record) => (
                    <div style={{ display: 'flex', gap: 8 }}>
                      {record.status === 'active' ? (
                        <Popconfirm title="确定吊销此 Key 吗？" onConfirm={() => onRevokeKey(record.id)}>
                          <Button type="link" danger>吊销</Button>
                        </Popconfirm>
                      ) : (
                        <Popconfirm title="确定彻底删除此历史记录吗？" onConfirm={async () => {
                          try {
                            await gatewayAPI.deleteApiKey(record.id);
                            message.success('历史记录已删除');
                            fetchApiKeys();
                          } catch {
                            message.error('删除失败');
                          }
                        }}>
                          <Button type="link" style={{ color: '#999' }}>删除记录</Button>
                        </Popconfirm>
                      )}
                    </div>
                  )
                }
              ]}
            />
          </div>
        </Tabs.TabPane>

        <Tabs.TabPane tab="路由规则" key="3">
          <div className="tab-content">
            <Button type="primary" onClick={() => setIsRouteModalVisible(true)} style={{ marginBottom: 16 }}>
              + 新增路由规则
            </Button>
            <Table
              dataSource={routes}
              rowKey="id"
              columns={[
                { title: '路径模式', dataIndex: 'path_pattern' },
                { title: '目标微服务', dataIndex: 'service_name' },
                { title: '优先级', dataIndex: 'priority' },
                { title: '状态', dataIndex: 'enabled', render: (val) => <Switch checked={val === 1} disabled /> },
                {
                  title: '操作',
                  render: (_, record) => (
                    <Popconfirm title="确定删除此路由吗？" onConfirm={() => onDeleteRoute(record.id)}>
                      <Button type="link" danger>删除</Button>
                    </Popconfirm>
                  )
                }
              ]}
              locale={{ emptyText: '暂无路由规则' }}
            />
          </div>
        </Tabs.TabPane>

        <Tabs.TabPane tab="日志配置" key="4">
          <div className="tab-content" style={{ display: 'flex', gap: 24 }}>
            <div style={{ flex: 1, maxWidth: 400 }}>
              <Form form={logForm} layout="vertical" onFinish={onSaveConfig}>
                <Form.Item label="日志级别" name="log_level"><Input /></Form.Item>
                <Form.Item label="保留天数" name="log_retention_days"><InputNumber style={{ width: '100%' }} /></Form.Item>
                <Form.Item>
                  <Button type="primary" htmlType="submit">保存配置</Button>
                </Form.Item>
              </Form>
            </div>
            <div style={{ flex: 2 }}>
              <div style={{ marginBottom: 8, fontWeight: 500 }}>实时网关日志 (Console)</div>
              <div className="log-viewer premium-card">
                {logs.length === 0 ? (
                  <div style={{ color: '#666' }}>等待日志流连接...</div>
                ) : logs.map((log, idx) => (
                  <div key={idx} style={{ marginBottom: 4, display: 'flex', gap: 8 }}>
                    <span style={{ color: '#6a9955' }}>[{log.time}]</span>
                    <span style={{ 
                      color: log.level === 'ERROR' ? '#f44747' : 
                             log.level === 'TOOL' ? '#ce9178' : '#569cd6',
                      fontWeight: 'bold',
                      minWidth: 50
                    }}>{log.level}:</span>
                    <span>{log.message}</span>
                  </div>
                ))}
                <div ref={logEndRef} />
              </div>
            </div>
          </div>
        </Tabs.TabPane>
      </Tabs>

      <Modal
        title="创建 API Key"
        open={isKeyModalVisible}
        onCancel={() => setIsKeyModalVisible(false)}
        onOk={() => keyForm.submit()}
        width={500}
      >
        <Form form={keyForm} layout="vertical" onFinish={onCreateKey}>
          <Form.Item label="Key 名称" name="name" rules={[{ required: true }]}><Input placeholder="例如: 内部系统调用 Key" /></Form.Item>
          <Form.Item label="权限分配" name="permissions" initialValue={['read']}>
            <Checkbox.Group options={[
              { label: '只读 (Read)', value: 'read' },
              { label: '写入 (Write)', value: 'write' },
              { label: '管理 (Admin)', value: 'admin' },
            ]} />
          </Form.Item>
          <Form.Item label="过期时间" name="expires_at" tooltip="留空表示永久有效">
            <DatePicker showTime style={{ width: '100%' }} placeholder="选择过期日期和时间" />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="新增路由规则"
        open={isRouteModalVisible}
        onCancel={() => setIsRouteModalVisible(false)}
        onOk={() => routeForm.submit()}
      >
        <Form form={routeForm} layout="vertical" onFinish={onCreateRoute}>
          <Form.Item label="路径模式 (例如: /api/v1/user/*)" name="path_pattern" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item label="目标微服务" name="target_service_id" rules={[{ required: true }]}>
            <Select options={services.map(s => ({ value: s.id, label: s.name }))} placeholder="选择转发的目标服务" />
          </Form.Item>
          <Form.Item label="优先级" name="priority" initialValue={10}><InputNumber style={{ width: '100%' }} /></Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
