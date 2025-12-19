import React, { useEffect, useState } from 'react';
import { Card, Table, Button, message, Modal, Form, Input, Select, Typography, Tag } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import { breedingValueAPI } from '../../api';

const BreedingAnalysis: React.FC = () => {
  const [runs, setRuns] = useState([]);
  const [modalVisible, setModalVisible] = useState(false);
  const [form] = Form.useForm();

  useEffect(() => {
    loadRuns();
  }, []);

  const loadRuns = async () => {
    try {
      const data = await breedingValueAPI.listRuns();
      setRuns(data || []);
    } catch (error) {
      console.error(error);
    }
  };

  const handleCreate = async () => {
    try {
      const values = await form.validateFields();
      await breedingValueAPI.createRun(values);
      message.success('创建成功');
      setModalVisible(false);
      loadRuns();
    } catch (error) {
      message.error('创建失败');
    }
  };

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id' },
    { title: '方法', dataIndex: 'method', key: 'method', render: (m: string) => <Tag>{m}</Tag> },
    { title: '性状', dataIndex: 'trait_name', key: 'trait_name' },
  ];

  return (
    <Card title={<Typography.Title level={3}>育种分析</Typography.Title>} extra={<Button type="primary" icon={<PlusOutlined />} onClick={() => setModalVisible(true)}>新建任务</Button>}>
      <Table columns={columns} dataSource={runs} rowKey="id" />
      <Modal title="新建育种任务" open={modalVisible} onOk={handleCreate} onCancel={() => setModalVisible(false)}>
        <Form form={form} layout="vertical">
          <Form.Item name="method" label="方法" rules={[{ required: true }]}>
            <Select>
              <Select.Option value="BLUP">BLUP</Select.Option>
              <Select.Option value="GBLUP">GBLUP</Select.Option>
              <Select.Option value="ssGBLUP">ssGBLUP</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="trait_name" label="性状" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  );
};

export default BreedingAnalysis;
