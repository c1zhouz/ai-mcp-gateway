import React, { useState, useEffect } from 'react';
import { Table, Input, Select, Collapse, Switch, Button, Drawer, Descriptions, Tag, message } from 'antd';
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

  useEffect(() => {
    fetchData();
  }, [searchText, selectedService]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const params = {};
      if (searchText) params.search = searchText;
      if (selectedService) params.service_id = selectedService;

      const [toolsRes, svcsRes] = await Promise.all([
        toolsAPI.list(params),
        servicesAPI.list()
      ]);
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

  // Group tools by service
  const groupedTools = tools.reduce((acc, tool) => {
    const sName = tool.service_name || '未知服务';
    if (!acc[sName]) acc[sName] = [];
    acc[sName].push(tool);
    return acc;
  }, {});

  const columns = [
    { title: '工具名', dataIndex: 'name', width: '20%' },
    { title: '描述', dataIndex: 'description', width: '40%' },
    { title: '参数个数', render: (_, record) => Object.keys(record.parameters_schema?.properties || {}).length },
    { 
      title: '状态', 
      render: (_, record) => (
        <Switch 
          checked={record.enabled === 1} 
          onChange={(checked) => onToggleEnable(record.id, checked)} 
        />
      ) 
    },
    {
      title: '操作',
      render: (_, record) => <Button type="link" onClick={() => showDetail(record)}>查看详情</Button>
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
      </div>

      <div className="tools-list">
        <Collapse items={items} defaultActiveKey={Object.keys(groupedTools)} />
      </div>

      <Drawer
        title="工具详情"
        width={600}
        onClose={() => setDrawerVisible(false)}
        open={drawerVisible}
      >
        {currentTool && (
          <div className="tool-detail">
            <Descriptions title="基础信息" column={1} bordered size="small">
              <Descriptions.Item label="名称">{currentTool.name}</Descriptions.Item>
              <Descriptions.Item label="所属服务"><Tag color="blue">{currentTool.service_name}</Tag></Descriptions.Item>
              <Descriptions.Item label="描述">{currentTool.description}</Descriptions.Item>
            </Descriptions>

            <h4 style={{ marginTop: 24, marginBottom: 16 }}>参数定义 (JSON Schema)</h4>
            <div className="schema-view">
              <pre>{JSON.stringify(currentTool.parameters_schema, null, 2)}</pre>
            </div>
          </div>
        )}
      </Drawer>
    </div>
  );
}
