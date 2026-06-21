import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { Descriptions, Table, Card, Tag, Spin, message, Button } from 'antd';
import { SyncOutlined } from '@ant-design/icons';
import { servicesAPI } from '../../services/api';

export default function ServiceDetail() {
  const { id } = useParams();
  const [service, setService] = useState(null);
  const [tools, setTools] = useState([]);
  const [loading, setLoading] = useState(true);

  async function fetchDetail() {
    try {
      const [svcRes, toolsRes] = await Promise.all([
        servicesAPI.get(id),
        servicesAPI.getTools(id)
      ]);
      setService(svcRes.data);
      setTools(toolsRes.data);
    } catch {
      message.error('加载失败');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchDetail();
    // Re-fetch when the route id changes.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const onSyncTools = async () => {
    try {
      setLoading(true);
      await servicesAPI.syncTools(id);
      message.success('同步成功');
      fetchDetail();
    } catch {
      message.error('同步失败');
      setLoading(false);
    }
  };

  if (loading || !service) {
    return <Spin size="large" style={{ display: 'block', margin: '100px auto', textAlign: 'center' }} />;
  }

  return (
    <div>
      <Card 
        title="服务详情" 
        extra={<Button type="primary" icon={<SyncOutlined />} onClick={onSyncTools}>同步工具</Button>}
        bordered={false} 
        style={{ marginBottom: 24, borderRadius: 8 }}
      >
        <Descriptions column={2}>
          <Descriptions.Item label="名称">{service.name}</Descriptions.Item>
          <Descriptions.Item label="状态">
            <Tag color={service.status === 'online' ? 'green' : 'default'}>{service.status}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label="地址">{service.address}</Descriptions.Item>
          <Descriptions.Item label="健康检查间隔">{service.health_check_interval} 秒</Descriptions.Item>
          <Descriptions.Item label="最后心跳">{service.last_heartbeat ? new Date(service.last_heartbeat).toLocaleString() : '无'}</Descriptions.Item>
          <Descriptions.Item label="描述" span={2}>{service.description || '暂无描述'}</Descriptions.Item>
        </Descriptions>
      </Card>

      <Card title="挂载的工具列表" bordered={false} style={{ borderRadius: 8 }}>
        <Table 
          dataSource={tools}
          rowKey="id"
          columns={[
            { title: '工具名称', dataIndex: 'name' },
            { title: '描述', dataIndex: 'description' },
            { title: '状态', dataIndex: 'enabled', render: (val) => <Tag color={val ? 'blue' : 'default'}>{val ? '已启用' : '已禁用'}</Tag> }
          ]}
        />
      </Card>
    </div>
  );
}
