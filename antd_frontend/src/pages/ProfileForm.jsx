import React from 'react';
import { Layout, Card, Form, Input, Button, notification } from 'antd';

const { Content } = Layout;

const ProfileForm = () => {
  const [form] = Form.useForm();

  const onFinish = async (values) => {
    try {
      const response = await fetch('/api/save_profile', {
         method: 'POST',
         headers: {
           'Content-Type': 'application/json',
         },
         body: JSON.stringify(values),
      });
      if (!response.ok) {
         notification.error({
           message: 'Profile Update Failed',
           description: 'Could not save your profile data. Please try again.',
         });
         return;
      }
      notification.success({
          message: 'Profile Updated',
          description: 'Your profile has been updated successfully.',
      });
    } catch (error) {
       notification.error({
         message: 'Error',
         description: 'An error occurred while saving the profile.',
       });
    }
  };

  return (
    <Layout>
      <Content style={{ padding: '24px' }}>
        <Card title="Profile" bordered={false}>
          <Form form={form} layout="vertical" onFinish={onFinish}>
            <Form.Item
              label="Name"
              name="name"
              rules={[{ required: true, message: 'Please input your name' }]}
            >
              <Input placeholder="Enter your name" />
            </Form.Item>
            <Form.Item
              label="Email"
              name="email"
              rules={[
                { 
                  required: true, 
                  type: 'email', 
                  message: 'Please enter a valid email address' 
                }
              ]}
            >
              <Input placeholder="Enter your email" />
            </Form.Item>
            <Form.Item>
              <Button type="primary" htmlType="submit">
                Update Profile
              </Button>
            </Form.Item>
          </Form>
        </Card>
      </Content>
    </Layout>
  );
};

export default ProfileForm;
