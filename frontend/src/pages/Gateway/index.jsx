import React, { useState, useEffect } from 'react';
import { Tabs, Form, Input, InputNumber, Button, Table, Modal, Tag, Switch, message, Popconfirm } from 'antd';
import { gatewayAPI } from '../../services/api';
import './Gateway.css';

export default function Gateway() {
  const [configForm] = Form.useForm();
  const [logForm] = Form.useForm();
  const [apiKeys, setApiKeys] = useState([]);
  const [routes, setRoutes] = useState([]);
  const [isKeyModalVisible, setIsKeyModalVisible] = useState(false);
  const [keyForm] = Form.useForm();

  useEffect(() => {
    fetchConfig();
    fetchApiKeys();
    fetchRoutes();
  }, []);

  const fetchConfig = async () => {
    try {
      const res = await gatewayAPI.getConfig();
      configForm.setFieldsValue(res.data);
      logForm.setFieldsValue(res.data);
    } catch (e) {
      message.error('获取配置失败');
    }
  };

  const fetchApiKeys = async () => {
    try {
      const res = await gatewayAPI.getApiKeys();
      setApiKeys(res.data);
    } catch (e) {
      message.error('获取API Key失败');
    }
  };

  const fetchRoutes = async () => {
    try {
      const res = await gatewayAPI.getRoutes();
      setRoutes(res.data);
    } catch (e) {
      message.error('获取路由失败');
    }
  };

  const onSaveConfig = async (values) => {
    try {
      await gatewayAPI.updateConfig(values);
      message.success('配置已保存');
    } catch (e) {
      message.error('保存失败');
    }
  };

  const onCreateKey = async (values) => {
    try {
      const res = await gatewayAPI.createApiKey(values);
      message.success(`创建成功，Key: ${res.data.key_value}`);
      setIsKeyModalVisible(false);
      keyForm.resetFields();
      fetchApiKeys();
    } catch (e) {
      message.error('创建失败');
    }
  };

  const onRevokeKey = async (id) => {
    try {
      await gatewayAPI.deleteApiKey(id);
      message.success('已吊销');
      fetchApiKeys();
    } catch (e) {
      message.error('操作失败');
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
                    record.status === 'active' && (
                      <Popconfirm title="确定吊销此 Key 吗？" onConfirm={() => onRevokeKey(record.id)}>
                        <Button type="link" danger>吊销</Button>
                      </Popconfirm>
                    )
                  )
                }
              ]}
            />
          </div>
        </Tabs.TabPane>

        <Tabs.TabPane tab="路由规则" key="3">
          <div className="tab-content">
            <Table
              dataSource={routes}
              rowKey="id"
              columns={[
                { title: '路径模式', dataIndex: 'path_pattern' },
                { title: '目标微服务', dataIndex: 'service_name' },
                { title: '优先级', dataIndex: 'priority' },
                { title: '状态', dataIndex: 'enabled', render: (val) => <Switch checked={val === 1} disabled /> },
              ]}
              locale={{ emptyText: '暂无路由规则' }}
            />
          </div>
        </Tabs.TabPane>

        <Tabs.TabPane tab="日志配置" key="4">
          <div className="tab-content">
            <Form form={logForm} layout="vertical" onFinish={onSaveConfig} style={{ maxWidth: 600 }}>
              <Form.Item label="日志级别" name="log_level"><Input /></Form.Item>
              <Form.Item label="保留天数" name="log_retention_days"><InputNumber style={{ width: '100%' }} /></Form.Item>
              <Form.Item>
                <Button type="primary" htmlType="submit">保存日志配置</Button>
              </Form.Item>
            </Form>
          </div>
        </Tabs.TabPane>
      </Tabs>

      <Modal
        title="创建 API Key"
        open={isKeyModalVisible}
        onCancel={() => setIsKeyModalVisible(false)}
        onOk={() => keyForm.submit()}
      >
        <Form form={keyForm} layout="vertical" onFinish={onCreateKey}>
          <Form.Item label="Key 名称" name="name" rules={[{ required: true }]}><Input /></Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
