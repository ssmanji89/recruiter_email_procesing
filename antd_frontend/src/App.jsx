import React, { useState } from 'react';
import { Layout, Menu } from 'antd';
import {
  DashboardOutlined,
  UserOutlined,
  CodeOutlined,
} from '@ant-design/icons';
import Dashboard from './pages/Dashboard';
import ProfileForm from './pages/ProfileForm';
import BackendOverview from './pages/BackendOverview';
import BackendStatus from './components/BackendStatus';

const { Header, Content, Sider } = Layout;

const App = () => {
  const [selectedKey, setSelectedKey] = useState('dashboard');

  const renderContent = () => {
    switch(selectedKey) {
      case 'dashboard':
        return <Dashboard />;
      case 'profile':
        return <ProfileForm />;
      case 'backend':
        return <BackendOverview />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider breakpoint="lg" collapsedWidth="0">
        <div style={{ height: '32px', margin: '16px', background: 'rgba(255, 255, 255, 0.3)' }} />
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[selectedKey]}
          onClick={({ key }) => setSelectedKey(key)}
        >
          <Menu.Item key="dashboard" icon={<DashboardOutlined />}>
            Dashboard
          </Menu.Item>
          <Menu.Item key="profile" icon={<UserOutlined />}>
            Profile
          </Menu.Item>
          <Menu.Item key="backend" icon={<CodeOutlined />}>
            Backend
          </Menu.Item>
        </Menu>
      </Sider>
      <Layout>
        <Header style={{ background: '#fff', padding: '0 16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ fontSize: '20px', fontWeight: 'bold' }}>Recruiter Email Processor</div>
          <BackendStatus />
        </Header>
        <Content style={{ margin: '24px 16px 0' }}>
          {renderContent()}
        </Content>
      </Layout>
    </Layout>
  );
};

export default App;
