import React, { useEffect, useState } from 'react';
import { Row, Col, Card, Statistic, Table, List, Tag, Spin } from 'antd';
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
          <Card title="请求量趋势 (最近7天)" bordered={false}>
            <div style={{ height: 300 }}>
              <Line {...lineConfig} />
            </div>
          </Card>
        </Col>
        <Col span={8}>
          <Card title="工具调用排行 Top 10" bordered={false}>
            <div style={{ height: 300 }}>
              <Bar {...barConfig} />
            </div>
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col span={12}>
          <Card title="最近操作日志" bordered={false}>
            <Table
              dataSource={[]}
              columns={[
                { title: '时间', dataIndex: 'time' },
                { title: '操作', dataIndex: 'action' },
                { title: '状态', dataIndex: 'status' },
              ]}
              pagination={false}
              size="small"
              locale={{ emptyText: '暂无日志' }}
            />
          </Card>
        </Col>
        <Col span={12}>
          <Card title="系统告警" bordered={false}>
            <List
              size="small"
              locale={{ emptyText: '暂无告警' }}
              dataSource={[]}
              renderItem={(item) => <List.Item>{item}</List.Item>}
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
}
