import React, { useState, useEffect } from 'react';
import {
  Table, Input, Select, Collapse, Switch, Button, Drawer,
  Descriptions, Tag, message, Form, Modal, Popconfirm, Space, Tooltip, Alert
} from 'antd';
import {
  PlusOutlined, EditOutlined, DeleteOutlined, CodeOutlined,
  DeploymentUnitOutlined, CheckCircleOutlined, LoadingOutlined
} from '@ant-design/icons';
import { toolsAPI, servicesAPI } from '../../services/api';
import './Tools.css';

const DEFAULT_SCHEMA = JSON.stringify({
  type: 'object',
  properties: {},
  required: []
}, null, 2);

const DEFAULT_CODE = `    # 在这里编写工具的 Python 函数体
    # 参数会根据上方 JSON Schema 自动生成函数签名
    # 示例：
    return {"status": "ok", "result": "your result here"}`;

export default function Tools() {
  const [tools, setTools] = useState([]);
  const [services, setServices] = useState([]);
  const [loading, setLoading] = useState(false);

  const [drawerVisible, setDrawerVisible] = useState(false);
  const [currentTool, setCurrentTool] = useState(null);

  const [modalVisible, setModalVisible] = useState(false);
  const [editingTool, setEditingTool] = useState(null);
  const [schemaText, setSchemaText] = useState(DEFAULT_SCHEMA);
  const [schemaError, setSchemaError] = useState('');
  const [codeText, setCodeText] = useState(DEFAULT_CODE);
  const [modalLoading, setModalLoading] = useState(false);
  const [form] = Form.useForm();

  const [deployingId, setDeployingId] = useState(null);

  const [searchText, setSearchText] = useState('');
  const [selectedService, setSelectedService] = useState(null);

  useEffect(() => {
    fetchData();
  }, [searchText, selectedService]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const params = {};
      if (searchText) params.search = searchText;
      if (selectedService) params.service_id = selectedService;
      const [toolsRes, svcsRes] = await Promise.all([toolsAPI.list(params), servicesAPI.list()]);
      setTools(toolsRes.data);
      setServices(svcsRes.data);
    } catch (e) {
      message.error('获取工具列表失败');
    } finally {
      setLoading(false);
    }
  };

  const onToggleEnable = async (id, enabled) => {
    try {
      await toolsAPI.updateStatus(id, enabled);
      message.success('状态已更新');
      fetchData();
    } catch (e) {
      message.error('操作失败');
    }
  };

  const showDetail = (tool) => {
    setCurrentTool(tool);
    setDrawerVisible(true);
  };

  const openCreate = () => {
    setEditingTool(null);
    form.resetFields();
    setSchemaText(DEFAULT_SCHEMA);
    setSchemaError('');
    setCodeText(DEFAULT_CODE);
    setModalVisible(true);
  };

  const openEdit = (tool) => {
    setEditingTool(tool);
    form.setFieldsValue({
      service_id: tool.service_id,
      name: tool.name,
      description: tool.description,
      enabled: tool.enabled === 1,
    });
    setSchemaText(JSON.stringify(tool.parameters_schema || {}, null, 2));
    setSchemaError('');
    setCodeText(tool.code || DEFAULT_CODE);
    setModalVisible(true);
  };

  const onSchemaChange = (text) => {
    setSchemaText(text);
    try {
      JSON.parse(text);
      setSchemaError('');
    } catch (e) {
      setSchemaError('JSON 格式错误：' + e.message);
    }
  };

  const onModalOk = async () => {
    if (schemaError) {
      message.error('请修正 JSON Schema 格式错误');
      return;
    }
    try {
      const values = await form.validateFields();
      let schema;
      try { schema = JSON.parse(schemaText); } catch {
        message.error('JSON Schema 格式不正确');
        return;
      }
      setModalLoading(true);
      const payload = {
        service_id: values.service_id,
        name: values.name,
        description: values.description || '',
        parameters_schema: schema,
        code: codeText,
        enabled: values.enabled !== false,
      };
      if (editingTool) {
        await toolsAPI.update(editingTool.id, payload);
        message.success('工具已更新');
      } else {
        await toolsAPI.create(payload);
        message.success('工具已创建，点击"部署"按钮将其注入微服务');
      }
      setModalVisible(false);
      fetchData();
    } catch (e) {
      if (e?.response?.data?.detail) message.error(e.response.data.detail);
    } finally {
      setModalLoading(false);
    }
  };

  const onDeploy = async (tool) => {
    setDeployingId(tool.id);
    try {
      const res = await toolsAPI.deploy(tool.id);
      message.success(res.data.message);
      fetchData();
    } catch (e) {
      const detail = e?.response?.data?.detail;
      message.error(detail || '部署失败，请检查服务配置');
    } finally {
      setDeployingId(null);
    }
  };

  const onDelete = async (id) => {
    try {
      await toolsAPI.delete(id);
      message.success('工具已删除');
      fetchData();
    } catch (e) {
      message.error('删除失败');
    }
  };

  const groupedTools = tools.reduce((acc, tool) => {
    const sName = tool.service_name || '未知服务';
    if (!acc[sName]) acc[sName] = [];
    acc[sName].push(tool);
    return acc;
  }, {});

  const columns = [
    { title: '工具名', dataIndex: 'name', width: '20%' },
    { title: '描述', dataIndex: 'description', width: '32%', ellipsis: true },
    {
      title: '参数数', width: '8%',
      render: (_, r) => Object.keys(r.parameters_schema?.properties || {}).length
    },
    {
      title: '有代码', width: '8%',
      render: (_, r) => r.code && r.code.trim()
        ? <Tag color="success" icon={<CheckCircleOutlined />}>已配置</Tag>
        : <Tag color="default">无</Tag>
    },
    {
      title: '状态', width: '8%',
      render: (_, r) => (
        <Switch checked={r.enabled === 1} onChange={(c) => onToggleEnable(r.id, c)} size="small" />
      )
    },
    {
      title: '操作', width: '24%',
      render: (_, r) => (
        <Space size={4}>
          <Tooltip title="查看详情">
            <Button type="link" size="small" icon={<CodeOutlined />} onClick={() => showDetail(r)} />
          </Tooltip>
          <Tooltip title="编辑工具">
            <Button type="link" size="small" icon={<EditOutlined />} onClick={() => openEdit(r)} />
          </Tooltip>
          <Tooltip title="部署到微服务（写入代码并重启）">
            <Button
              type="link"
              size="small"
              icon={deployingId === r.id ? <LoadingOutlined /> : <DeploymentUnitOutlined />}
              disabled={deployingId === r.id}
              style={{ color: r.code && r.code.trim() ? '#1677ff' : '#ccc' }}
              onClick={() => onDeploy(r)}
            />
          </Tooltip>
          <Popconfirm
            title="确认删除"
            description={`确定删除工具 "${r.name}"？`}
            onConfirm={() => onDelete(r.id)}
            okText="删除" cancelText="取消" okButtonProps={{ danger: true }}
          >
            <Tooltip title="删除工具">
              <Button type="link" size="small" danger icon={<DeleteOutlined />} />
            </Tooltip>
          </Popconfirm>
        </Space>
      )
    }
  ];

  const items = Object.entries(groupedTools).map(([serviceName, list]) => ({
    key: serviceName,
    label: `${serviceName} (${list.length} 个工具)`,
    children: <Table dataSource={list} columns={columns} rowKey="id" pagination={false} size="middle" />
  }));

  return (
    <div className="tools-container">
      <div className="tools-action-bar">
        <Input.Search
          placeholder="搜索工具名称/描述..."
          style={{ width: 300 }}
          onSearch={(val) => { setSearchText(val); fetchData(); }}
        />
        <Select
          placeholder="筛选服务"
          style={{ width: 200, marginLeft: 16 }}
          allowClear
          options={services.map(s => ({ value: s.id, label: s.name }))}
          onChange={(val) => { setSelectedService(val); }}
        />
        <div style={{ flex: 1 }} />
        <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
          新增工具
        </Button>
      </div>

      <div className="tools-list">
        <Collapse items={items} defaultActiveKey={Object.keys(groupedTools)} />
      </div>

      {/* Detail Drawer */}
      <Drawer
        title="工具详情"
        width={640}
        onClose={() => setDrawerVisible(false)}
        open={drawerVisible}
        extra={
          currentTool && (
            <Space>
              <Button icon={<EditOutlined />} onClick={() => { setDrawerVisible(false); openEdit(currentTool); }}>编辑</Button>
              <Button
                type="primary"
                icon={<DeploymentUnitOutlined />}
                loading={deployingId === currentTool?.id}
                onClick={() => onDeploy(currentTool)}
              >
                部署到微服务
              </Button>
            </Space>
          )
        }
      >
        {currentTool && (
          <div className="tool-detail">
            <Descriptions title="基础信息" column={1} bordered size="small">
              <Descriptions.Item label="名称">{currentTool.name}</Descriptions.Item>
              <Descriptions.Item label="所属服务"><Tag color="blue">{currentTool.service_name}</Tag></Descriptions.Item>
              <Descriptions.Item label="描述">{currentTool.description || '—'}</Descriptions.Item>
              <Descriptions.Item label="状态">
                <Tag color={currentTool.enabled === 1 ? 'success' : 'default'}>
                  {currentTool.enabled === 1 ? '已启用' : '已禁用'}
                </Tag>
              </Descriptions.Item>
            </Descriptions>
            <h4 style={{ marginTop: 24, marginBottom: 12 }}>参数定义 (JSON Schema)</h4>
            <div className="schema-view">
              <pre>{JSON.stringify(currentTool.parameters_schema, null, 2)}</pre>
            </div>
            {currentTool.code && currentTool.code.trim() && (
              <>
                <h4 style={{ marginTop: 20, marginBottom: 12 }}>函数体代码</h4>
                <div className="schema-view">
                  <pre style={{ background: '#1a1a2e', color: '#e0e0e0' }}>{currentTool.code}</pre>
                </div>
              </>
            )}
          </div>
        )}
      </Drawer>

      {/* Create / Edit Modal */}
      <Modal
        title={editingTool ? `编辑工具：${editingTool.name}` : '新增工具'}
        open={modalVisible}
        onOk={onModalOk}
        onCancel={() => setModalVisible(false)}
        confirmLoading={modalLoading}
        width={760}
        okText={editingTool ? '保存更改' : '创建工具'}
        cancelText="取消"
      >
        <Alert
          style={{ marginBottom: 16 }}
          message="创建或编辑工具后，点击列表中的「🚀 部署」按钮，即可将代码注入微服务并自动重启，工具将立即可用。"
          type="info"
          showIcon
        />
        <Form form={form} layout="vertical">
          <Form.Item name="service_id" label="所属微服务" rules={[{ required: true, message: '请选择微服务' }]}>
            <Select
              placeholder="选择所属微服务"
              options={services.map(s => ({ value: s.id, label: s.name }))}
              disabled={!!editingTool}
            />
          </Form.Item>
          <Form.Item name="name" label="工具名称（英文，将作为 Python 函数名）" rules={[
            { required: true, message: '请输入工具名称' },
            { pattern: /^[a-z_][a-z0-9_]*$/, message: '只能使用小写字母、数字和下划线' }
          ]}>
            <Input placeholder="例如：get_order_details" />
          </Form.Item>
          <Form.Item name="description" label="功能描述（LLM 会根据此描述决定是否调用此工具）">
            <Input.TextArea rows={2} placeholder="描述这个工具的功能..." />
          </Form.Item>
          <Form.Item
            label={<span>参数定义 (JSON Schema) <Tag color="blue" style={{ fontSize: 11 }}>JSON</Tag></span>}
          >
            <Input.TextArea
              rows={6}
              value={schemaText}
              onChange={(e) => onSchemaChange(e.target.value)}
              style={{ fontFamily: 'monospace', fontSize: 13, border: schemaError ? '1px solid #ff4d4f' : undefined }}
            />
            {schemaError && <div style={{ color: '#ff4d4f', fontSize: 12, marginTop: 4 }}>{schemaError}</div>}
          </Form.Item>
          <Form.Item
            label={
              <span>
                函数体代码 <Tag color="purple" style={{ fontSize: 11 }}>Python</Tag>
                <span style={{ color: '#999', fontSize: 12, fontWeight: 'normal', marginLeft: 8 }}>
                  函数签名会自动从 Schema 生成，只需写函数体
                </span>
              </span>
            }
          >
            <Input.TextArea
              rows={10}
              value={codeText}
              onChange={(e) => setCodeText(e.target.value)}
              style={{ fontFamily: 'monospace', fontSize: 13, background: '#1e1e2e', color: '#cdd6f4' }}
              placeholder="    return {'result': 'your data'}"
            />
          </Form.Item>
          <Form.Item name="enabled" label="是否启用" valuePropName="checked" initialValue={true}>
            <Switch />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
