import { useEffect, useState } from 'react';
import {
  Table, Input, Select, Collapse, Switch, Button, Drawer,
  Descriptions, Tag, message, Popconfirm, Space, Tooltip, Spin
} from 'antd';
import { DeleteOutlined, EyeOutlined } from '@ant-design/icons';
import { toolsAPI, servicesAPI } from '../../services/api';
import './Tools.css';

export default function Tools() {
  const [tools, setTools] = useState([]);
  const [services, setServices] = useState([]);
  const [loading, setLoading] = useState(false);

  const [drawerVisible, setDrawerVisible] = useState(false);
  const [currentTool, setCurrentTool] = useState(null);

  const [searchText, setSearchText] = useState('');
  const [selectedService, setSelectedService] = useState(null);

  async function fetchData() {
    setLoading(true);
    try {
      const params = {};
      if (searchText) params.search = searchText;
      if (selectedService) params.service_id = selectedService;
      const [toolsRes, svcsRes] = await Promise.all([toolsAPI.list(params), servicesAPI.list()]);
      setTools(toolsRes.data);
      setServices(svcsRes.data);
    } catch {
      message.error('获取工具列表失败');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchData();
    // Re-fetch when list filters change.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchText, selectedService]);

  const onToggleEnable = async (id, enabled) => {
    try {
      await toolsAPI.updateStatus(id, enabled);
      message.success('状态已更新');
      fetchData();
    } catch {
      message.error('操作失败');
    }
  };

  const showDetail = (tool) => {
    setCurrentTool(tool);
    setDrawerVisible(true);
  };

  const onDelete = async (id) => {
    try {
      await toolsAPI.delete(id);
      message.success('工具已删除');
      fetchData();
    } catch {
      message.error('删除失败');
    }
  };

  const groupedTools = tools.reduce((acc, tool) => {
    const serviceName = tool.service_name || '未知服务';
    if (!acc[serviceName]) acc[serviceName] = [];
    acc[serviceName].push(tool);
    return acc;
  }, {});

  const columns = [
    { title: '工具名', dataIndex: 'name', width: '24%' },
    { title: '描述', dataIndex: 'description', width: '38%', ellipsis: true },
    {
      title: '参数数',
      width: '10%',
      render: (_, record) => Object.keys(record.parameters_schema?.properties || {}).length,
    },
    {
      title: '状态',
      width: '10%',
      render: (_, record) => (
        <Switch
          checked={record.enabled === 1}
          onChange={(checked) => onToggleEnable(record.id, checked)}
          size="small"
        />
      ),
    },
    {
      title: '操作',
      width: '18%',
      render: (_, record) => (
        <Space size={4}>
          <Tooltip title="查看详情">
            <Button type="link" size="small" icon={<EyeOutlined />} onClick={() => showDetail(record)} />
          </Tooltip>
          <Popconfirm
            title="确认删除"
            description={`确定删除工具 "${record.name}"？`}
            onConfirm={() => onDelete(record.id)}
            okText="删除"
            cancelText="取消"
            okButtonProps={{ danger: true }}
          >
            <Tooltip title="删除工具">
              <Button type="link" size="small" danger icon={<DeleteOutlined />} />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  const items = Object.entries(groupedTools).map(([serviceName, list]) => ({
    key: serviceName,
    label: `${serviceName} (${list.length} 个工具)`,
    children: <Table dataSource={list} columns={columns} rowKey="id" pagination={false} size="middle" />,
  }));

  return (
    <div className="tools-container">
      <div className="tools-action-bar">
        <Input.Search
          placeholder="搜索工具名称/描述..."
          style={{ width: 300 }}
          onSearch={(value) => setSearchText(value)}
          allowClear
        />
        <Select
          placeholder="筛选服务"
          style={{ width: 200, marginLeft: 16 }}
          allowClear
          options={services.map((service) => ({ value: service.id, label: service.name }))}
          onChange={(value) => setSelectedService(value)}
        />
      </div>

      <Spin spinning={loading}>
        <div className="tools-list">
          <Collapse items={items} defaultActiveKey={Object.keys(groupedTools)} />
        </div>
      </Spin>

      <Drawer
        title="工具详情"
        width={640}
        onClose={() => setDrawerVisible(false)}
        open={drawerVisible}
      >
        {currentTool && (
          <div className="tool-detail">
            <Descriptions title="基础信息" column={1} bordered size="small">
              <Descriptions.Item label="名称">{currentTool.name}</Descriptions.Item>
              <Descriptions.Item label="所属服务">
                <Tag color="blue">{currentTool.service_name}</Tag>
              </Descriptions.Item>
              <Descriptions.Item label="描述">{currentTool.description || '-'}</Descriptions.Item>
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
          </div>
        )}
      </Drawer>
    </div>
  );
}
