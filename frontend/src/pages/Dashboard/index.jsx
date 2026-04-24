import React, { useEffect, useState } from 'react';
import { Row, Col, Card, Statistic, Table, List, Tag, Spin, Space, Badge } from 'antd';
import { ApiOutlined, AppstoreOutlined, LineChartOutlined, CheckCircleOutlined } from '@ant-design/icons';
import { Line, Bar } from '@ant-design/plots';
import { dashboardAPI } from '../../services/api';
import './Dashboard.css';

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [trendData, setTrendData] = useState([]);
  const [topTools, setTopTools] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [statsRes, trendRes, toolsRes] = await Promise.all([
          dashboardAPI.getStats(),
          dashboardAPI.getTrend(),
          dashboardAPI.getTopTools(),
        ]);
        setStats(statsRes.data);
        setTrendData(trendRes.data);
        setTopTools(toolsRes.data);
      } catch (error) {
        console.error('Failed to fetch dashboard data', error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading || !stats) {
    return <div className="loading-container"><Spin size="large" /></div>;
  }

  const lineConfig = {
    data: trendData,
    xField: 'time',
    yField: 'requests',
    point: { shape: 'circle' },
    color: '#1677ff',
  };

  const barConfig = {
    data: topTools,
    xField: 'count',
    yField: 'name',
    seriesField: 'name',
    color: '#52c41a',
    legend: false,
  };

  return (
    <div className="dashboard-container">
      <Row gutter={[16, 16]}>
        <Col span={6}>
          <Card bordered={false} className="stat-card">
            <Statistic title="在线微服务" value={stats.online_services} prefix={<ApiOutlined style={{ color: '#52c41a' }} />} />
          </Card>
        </Col>
        <Col span={6}>
          <Card bordered={false} className="stat-card">
            <Statistic title="注册工具总数" value={stats.total_tools} prefix={<AppstoreOutlined style={{ color: '#1677ff' }} />} />
          </Card>
        </Col>
        <Col span={6}>
          <Card bordered={false} className="stat-card">
            <Statistic title="今日请求量" value={stats.today_requests} prefix={<LineChartOutlined style={{ color: '#fa8c16' }} />} />
          </Card>
        </Col>
        <Col span={6}>
          <Card bordered={false} className="stat-card">
            <Statistic title="成功率" value={stats.success_rate} precision={2} suffix="%" prefix={<CheckCircleOutlined style={{ color: '#52c41a' }} />} />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col span={16}>
          <Card title="请求量趋势 (最近7天)" bordered={false} className="chart-card">
            <div style={{ height: 300 }}>
              <Line {...lineConfig} />
            </div>
          </Card>
        </Col>
        <Col span={8}>
          <Card title="工具调用排行 Top 10" bordered={false} className="chart-card">
            <div style={{ height: 300 }}>
              <Bar {...barConfig} />
            </div>
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col span={12}>
          <Card title="最近操作日志" bordered={false} className="log-card">
            <Table
              dataSource={[
                { key: '1', time: '2026-04-24 17:05:32', action: '同步微服务 [真实商城数据]', status: <Tag color="success">成功</Tag> },
                { key: '2', time: '2026-04-24 16:58:10', action: '修改工具配置 [check_inventory]', status: <Tag color="processing">已保存</Tag> },
                { key: '3', time: '2026-04-24 16:55:01', action: '连接微服务 [5001]', status: <Tag color="error">失败</Tag> },
                { key: '4', time: '2026-04-24 16:50:22', action: '创建微服务 [mock_mall_mcp]', status: <Tag color="success">成功</Tag> },
                { key: '5', time: '2026-04-24 10:22:15', action: '网关密钥更新', status: <Tag color="warning">安全提醒</Tag> },
              ]}
              columns={[
                { title: '时间', dataIndex: 'time', width: 160 },
                { title: '操作', dataIndex: 'action' },
                { title: '状态', dataIndex: 'status', width: 100 },
              ]}
              pagination={false}
              size="small"
            />
          </Card>
        </Col>
        <Col span={12}>
          <Card title="系统告警与状态" bordered={false} className="log-card">
            <List
              size="small"
              dataSource={[
                { type: 'warning', text: '微服务 [mock_mall_mcp] 响应时间超过 500ms' },
                { type: 'error', text: '数据库连接池占用率达到 85%' },
                { type: 'info', text: '系统版本 v1.2.4 已发布，请及时更新' },
                { type: 'success', text: '所有核心 MCP 节点运行状态：良好' },
              ]}
              renderItem={(item) => (
                <List.Item>
                  <Space>
                    <Badge status={item.type} />
                    <span>{item.text}</span>
                  </Space>
                </List.Item>
              )}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
}
