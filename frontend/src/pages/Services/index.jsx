import React, { useState, useEffect } from 'react';
import { Row, Col, Card, Badge, Tag, Button, Input, InputNumber, Select, Drawer, Form, message, Switch, Popconfirm, Spin } from 'antd';
import { CloudServerOutlined, ToolOutlined, DeleteOutlined, EditOutlined, RetweetOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { servicesAPI } from '../../services/api';
import './Services.css';

export default function Services() {
  const [services, setServices] = useState([]);
  const [loading, setLoading] = useState(false);
  const [drawerVisible, setDrawerVisible] = useState(false);
  const [form] = Form.useForm();
  const navigate = useNavigate();

  useEffect(() => {
    fetchServices();
  }, []);

  const fetchServices = async () => {
    setLoading(true);
    try {
      const res = await servicesAPI.list();
      setServices(res.data);
    } catch (e) {
      message.error('获取服务列表失败');
    } finally {
      setLoading(false);
    }
  };

  const onSaveService = async (values) => {
    try {
      await servicesAPI.create(values);
      message.success('服务创建成功');
      setDrawerVisible(false);
      form.resetFields();
      fetchServices();
    } catch (e) {
      message.error('服务创建失败');
    }
  };

  const onDelete = async (id) => {
    try {
      await servicesAPI.delete(id);
      message.success('已删除');
      fetchServices();
    } catch (e) {
      message.error('删除失败');
    }
  };

  const onHealthCheck = async (id) => {
    try {
      await servicesAPI.healthCheck(id);
      message.success('健康检查已触发');
      fetchServices();
    } catch (e) {
      message.error('健康检查失败');
    }
  };

  return (
    <div className="services-container">
      <div className="action-bar">
        <Button type="primary" onClick={() => setDrawerVisible(true)}>+ 添加服务</Button>
        <Input.Search placeholder="搜索服务..." style={{ width: 300, marginLeft: 16 }} />
        <Select defaultValue="all" style={{ width: 120, marginLeft: 16 }} options={[{ value: 'all', label: '全部状态' }, { value: 'online', label: '在线' }, { value: 'offline', label: '离线' }]} />
      </div>

      <Spin spinning={loading}>
        <Row gutter={[16, 16]}>
          {services.map(service => (
            <Col span={8} key={service.id}>
              <Card
                className="service-card"
                title={<span><CloudServerOutlined /> {service.name}</span>}
                extra={<Badge status={service.status === 'online' ? 'success' : 'default'} text={service.status === 'online' ? '在线' : '离线'} />}
                actions={[
                  <EditOutlined key="edit" onClick={() => navigate(`/services/${service.id}`)} />,
                  <RetweetOutlined key="check" onClick={() => onHealthCheck(service.id)} />,
                  <Popconfirm title="确定删除？" onConfirm={() => onDelete(service.id)}>
                    <DeleteOutlined key="delete" style={{ color: '#ff4d4f' }} />
                  </Popconfirm>
                ]}
              >
                <div className="card-meta">
                  <p><strong>地址：</strong> {service.address}</p>
                  <p>
                    <strong>工具：</strong> 
                    <Tag icon={<ToolOutlined />} color="blue">{service.tool_count} 个可用</Tag>
                  </p>
                  <p className="desc">{service.description || '暂无描述'}</p>
                </div>
              </Card>
            </Col>
          ))}
        </Row>
      </Spin>

      <Drawer title="添加微服务" width={400} onClose={() => setDrawerVisible(false)} open={drawerVisible}>
        <Form form={form} layout="vertical" onFinish={onSaveService}>
          <Form.Item name="name" label="服务名称" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="address" label="服务地址 (URL)" rules={[{ required: true }]}><Input placeholder="http://127.0.0.1:5000" /></Form.Item>
          <Form.Item name="description" label="描述"><Input.TextArea rows={3} /></Form.Item>
          <Form.Item name="health_check_interval" label="健康检查间隔 (秒)" initialValue={30}><InputNumber style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="auto_reconnect" label="自动重连" valuePropName="checked" initialValue={true}><Switch /></Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" block>提交保存</Button>
          </Form.Item>
        </Form>
      </Drawer>
    </div>
  );
}
