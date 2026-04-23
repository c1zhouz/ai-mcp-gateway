import React, { useState } from 'react';
import { Layout, Menu, Avatar, Dropdown, Badge, Space } from 'antd';
import {
  HomeOutlined,
  ApiOutlined,
  CloudServerOutlined,
  ToolOutlined,
  MessageOutlined,
  BellOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
} from '@ant-design/icons';
import { useNavigate, useLocation, Outlet } from 'react-router-dom';
import './AppLayout.css';

const { Header, Sider, Content } = Layout;

const menuItems = [
  { key: '/', icon: <HomeOutlined />, label: '首页' },
  { key: '/gateway', icon: <ApiOutlined />, label: '网关管理' },
  { key: '/services', icon: <CloudServerOutlined />, label: '微服务管理' },
  { key: '/tools', icon: <ToolOutlined />, label: '工具管理' },
  { key: '/chat', icon: <MessageOutlined />, label: '对话测试' },
];

export default function AppLayout() {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  const selectedKey = menuItems
    .map((item) => item.key)
    .filter((key) => key !== '/')
    .find((key) => location.pathname.startsWith(key)) || '/';

  return (
    <Layout className="app-layout">
      <Sider
        trigger={null}
        collapsible
        collapsed={collapsed}
        className="app-sider"
        width={240}
        collapsedWidth={80}
      >
        <div className="app-logo">
          <ApiOutlined className="logo-icon" />
          {!collapsed && <span className="logo-text">AI MCP Gateway</span>}
        </div>
        <Menu
          theme="light"
          mode="inline"
          selectedKeys={[selectedKey]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>
      <Layout>
        <Header className="app-header">
          <span
            className="collapse-trigger"
            onClick={() => setCollapsed(!collapsed)}
          >
            {collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
          </span>
          <h2 className="page-title">
            {menuItems.find((item) => item.key === selectedKey)?.label || '首页'}
          </h2>
          <Space className="header-right" size={20}>
            <Badge count={3} size="small">
              <BellOutlined style={{ fontSize: 18 }} />
            </Badge>
            <Dropdown
              menu={{
                items: [
                  { key: 'profile', label: '个人设置' },
                  { key: 'logout', label: '退出登录' },
                ],
              }}
            >
              <Space style={{ cursor: 'pointer' }}>
                <Avatar style={{ backgroundColor: '#1677ff' }}>管</Avatar>
                <span>管理员</span>
              </Space>
            </Dropdown>
          </Space>
        </Header>
        <Content className="app-content">
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
}
