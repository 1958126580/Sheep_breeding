import React, { useEffect, useState } from 'react';
import { Card, Table, Button, Space, message, Modal, Form, Input, Select, Typography } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { farmAPI, Farm } from '../../api';

const { Title } = Typography;

const FarmList: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [farms, setFarms] = useState<Farm[]>([]);
  const [modalVisible, setModalVisible] = useState(false);
  const [form] = Form.useForm();

  useEffect(() => {
    loadFarms();
  }, []);

  const loadFarms = async () => {
    setLoading(true);
    try {
      const data = await farmAPI.list();
      setFarms(data || []);
    } catch (error) {
      message.error('加载失败');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      await farmAPI.create(values);
      message.success('创建成功');
      setModalVisible(false);
      loadFarms();
    } catch (error) {
      message.error('操作失败');
    }
  };

  const columns = [
    { title: '编号', dataIndex: 'code', key: 'code' },
    { title: '名称', dataIndex: 'name', key: 'name' },
    { title: '类型', dataIndex: 'farm_type', key: 'farm_type' },
    { title: '容量', dataIndex: 'capacity', key: 'capacity' },
  ];

  return (
    <Card title={<Title level={3}>羊场管理</Title>} extra={<Button type="primary" icon={<PlusOutlined />} onClick={() => setModalVisible(true)}>新建</Button>}>
      <Table columns={columns} dataSource={farms} loading={loading} rowKey="id" />
      <Modal title="新建羊场" open={modalVisible} onOk={handleSubmit} onCancel={() => setModalVisible(false)}>
        <Form form={form} layout="vertical">
          <Form.Item name="code" label="编号" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="name" label="名称" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="farm_type" label="类型" rules={[{ required: true }]}>
            <Select>
              <Select.Option value="breeding">育种场</Select.Option>
              <Select.Option value="commercial">商业场</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="capacity" label="容量" rules={[{ required: true }]}>
            <Input type="number" />
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  );
};

export default FarmList;
