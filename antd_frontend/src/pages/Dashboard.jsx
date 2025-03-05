import React, { useState, useEffect } from 'react';
import { Layout, Card, Table, Tag, Input, Button, notification } from 'antd';

const { Content } = Layout;
const { Search } = Input;

const Dashboard = () => {
  const [searchText, setSearchText] = useState('');
  const [data, setData] = useState([]);
  const [filteredData, setFilteredData] = useState([]);
  const [loading, setLoading] = useState(true);

  // Function to fetch recruiter emails from backend
  const fetchRecruiterEmails = () => {
    setLoading(true);
    fetch('/api/recruiter_emails')
      .then(response => {
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        return response.json();
      })
      .then(emails => {
        // Expected emails should be an array of objects with keys: key, name, email, status
        setData(emails);
        setFilteredData(emails);
        setLoading(false);
      })
      .catch(err => {
        console.error('Error fetching recruiter emails:', err);
        notification.error({
          message: 'Data Reload Failed',
          description: 'Failed to reload recruiter email data. Please try again.'
        });
        setData([]);
        setFilteredData([]);
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchRecruiterEmails();
  }, []);

  const handleSearch = value => {
    setSearchText(value);
    const filtered = data.filter(item =>
      item.name.toLowerCase().includes(value.toLowerCase()) ||
      item.email.toLowerCase().includes(value.toLowerCase())
    );
    setFilteredData(filtered);
  };

  const reloadData = () => {
    fetchRecruiterEmails();
    notification.info({
      message: 'Data Reloading',
      description: 'Recruiter email data is being refreshed.'
    });
  };

  const handleProcessEmails = () => {
    setLoading(true);
    fetch('/api/process_emails', { method: 'POST' })
      .then(response => {
        if (!response.ok) {
          throw new Error('Error processing emails');
        }
        return response.json();
      })
      .then(processedEmails => {
        // Assume processedEmails is an array similar to recruiter emails
        setData(processedEmails);
        setFilteredData(processedEmails);
        setLoading(false);
        notification.success({
          message: 'Emails Processed',
          description: 'Recruiter emails have been processed successfully.'
        });
      })
      .catch(err => {
        console.error('Error processing emails:', err);
        notification.error({
          message: 'Processing Failed',
          description: 'Failed to process recruiter emails. Please try again.'
        });
        setLoading(false);
      });
  };

  const columns = [
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
      sorter: (a, b) => a.name.localeCompare(b.name)
    },
    {
      title: 'Email',
      dataIndex: 'email',
      key: 'email',
      sorter: (a, b) => a.email.localeCompare(b.email)
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: status => {
        const color = status === 'Pending' ? 'volcano' : 'green';
        return <Tag color={color}>{status.toUpperCase()}</Tag>;
      },
      filters: [
        { text: 'Processed', value: 'Processed' },
        { text: 'Pending', value: 'Pending' }
      ],
      onFilter: (value, record) => record.status === value
    }
  ];

  return (
    <Layout>
      <Content style={{ padding: '24px' }}>
        <Card title="Recruiter Emails" bordered={false}>
          <div style={{ marginBottom: '16px', display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap' }}>
            <Search
              placeholder="Search by name or email"
              onSearch={handleSearch}
              style={{ maxWidth: '300px' }}
              allowClear
            />
            <div>
              <Button type="primary" onClick={reloadData} style={{ marginRight: '8px' }}>
                Reload Data
              </Button>
              <Button type="default" onClick={handleProcessEmails}>
                Process Emails
              </Button>
            </div>
          </div>
          <Table 
            dataSource={filteredData} 
            columns={columns} 
            pagination={{ pageSize: 10 }} 
            loading={loading}
          />
        </Card>
      </Content>
    </Layout>
  );
};

export default Dashboard;
