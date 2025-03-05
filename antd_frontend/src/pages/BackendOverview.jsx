import React, { useState, useEffect } from 'react';
import { Layout, Card, Collapse, Spin, Alert } from 'antd';
import { CodeOutlined } from '@ant-design/icons';

const { Content } = Layout;
const { Panel } = Collapse;

const BackendOverview = () => {
  const [backendData, setBackendData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Fetch backend information from the API endpoint
    fetch('/api/backend_info')
      .then(response => {
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        return response.json();
      })
      .then(data => {
        setBackendData(data);
        setLoading(false);
      })
      .catch(err => {
        console.error('Error fetching backend info:', err);
        setError('Could not fetch backend info, showing default overview.');
        setLoading(false);
        // Fallback to static data
        setBackendData([
          {
            title: "Controllers",
            description: "The EmailController in app/controllers/email_controller.py orchestrates email processing by interfacing with GmailService and OpenAIService for tailored resume generation and user profile management."
          },
          {
            title: "Models",
            description: "Defined in app/models/email_model.py, the models (Email, Resume, UserProfile) represent recruiter email data, generated resumes, and candidate profiles."
          },
          {
            title: "Services",
            description: "GmailService and OpenAIService (in app/services/) manage external integrations: Gmail API interactions and generating tailored resumes using OpenAI's capabilities."
          },
          {
            title: "Views",
            description: "EmailView in app/views/email_view.py handles the rendering of processed email results, user profile forms, and resume download functionalities."
          }
        ]);
      });
  }, []);

  return (
    <Layout>
      <Content style={{ padding: '24px' }}>
        <Card title={<span><CodeOutlined /> Backend Overview</span>} bordered={false}>
          {loading ? (
            <Spin />
          ) : error ? (
            <Alert message={error} type="error" style={{ marginBottom: '16px' }} />
          ) : null}
          <Collapse defaultActiveKey={['0']}>
            {backendData.map((item, index) => (
              <Panel header={item.title} key={index}>
                <p>{item.description}</p>
              </Panel>
            ))}
          </Collapse>
        </Card>
      </Content>
    </Layout>
  );
};

export default BackendOverview;
