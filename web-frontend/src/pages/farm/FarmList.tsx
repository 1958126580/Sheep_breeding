import React, { useEffect, useState } from 'react';
import { 
  Card, Table, Button, Space, message, Modal, Form, Input, Select, 
  Typography, Tag, Tooltip, Dropdown, Badge, Row, Col, Statistic
} from 'antd';
import { 
  PlusOutlined, EditOutlined, DeleteOutlined, EyeOutlined,
  MoreOutlined, SearchOutlined, ExportOutlined, ImportOutlined,
  HomeOutlined, EnvironmentOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { farmAPI, Farm } from '../../api';
import './FarmList.scss';

const { Title, Text } = Typography;
const { Search } = Input;

const FarmList: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [farms, setFarms] = useState<Farm[]>([]);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingFarm, setEditingFarm] = useState<Farm | null>(null);
  const [searchText, setSearchText] = useState('');
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
      message.error('加载羊场列表失败');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleAdd = () => {
    setEditingFarm(null);
    form.resetFields();
    setModalVisible(true);
  };

  const handleEdit = (record: Farm) => {
    setEditingFarm(record);
    form.setFieldsValue(record);
    setModalVisible(true);
  };

  const handleDelete = (record: Farm) => {
    Modal.confirm({
      title: '确认删除',
      content: (
        <div>
          <p>确定要删除羊场 "<strong>{record.name}</strong>" 吗？</p>
          <Text type="secondary">此操作不可恢复</Text>
        </div>
      ),
      okText: '确认删除',
      okType: 'danger',
      cancelText: '取消',
      onOk: async () => {
        try {
          await farmAPI.delete(record.id!);
          message.success('删除成功');
          loadFarms();
        } catch (error) {
          message.error('删除失败');
        }
      },
    });
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      if (editingFarm) {
        await farmAPI.update(editingFarm.id!, values);
        message.success('更新成功');
      } else {
        await farmAPI.create(values);
        message.success('创建成功');
      }
      setModalVisible(false);
      loadFarms();
    } catch (error) {
      message.error('操作失败，请检查输入');
    }
  };

  const filteredFarms = farms.filter(farm => 
    farm.name?.toLowerCase().includes(searchText.toLowerCase()) ||
    farm.code?.toLowerCase().includes(searchText.toLowerCase())
  );

  const columns: ColumnsType<Farm> = [
    {
      title: '羊场编号',
      dataIndex: 'code',
      key: 'code',
      width: 120,
      render: (code: string) => (
        <Tag icon={<HomeOutlined />} color="blue">{code}</Tag>
      ),
    },
    {
      title: '羊场名称',
      dataIndex: 'name',
      key: 'name',
      render: (name: string, record: Farm) => (
        <Space direction="vertical" size={0}>
          <Text strong>{name}</Text>
          {record.address && (
            <Text type="secondary" style={{ fontSize: 12 }}>
              <EnvironmentOutlined /> {record.address}
            </Text>
          )}
        </Space>
      ),
    },
    {
      title: '类型',
      dataIndex: 'farm_type',
      key: 'farm_type',
      width: 100,
      render: (type: string) => {
        const typeConfig: Record<string, { color: string; label: string }> = {
          breeding: { color: 'purple', label: '育种场' },
          commercial: { color: 'green', label: '商业场' },
          research: { color: 'blue', label: '研究场' },
        };
        const config = typeConfig[type] || { color: 'default', label: type };
        return <Tag color={config.color}>{config.label}</Tag>;
      },
    },
    {
      title: '容量',
      dataIndex: 'capacity',
      key: 'capacity',
      width: 100,
      render: (capacity: number) => (
        <Badge 
          count={`${capacity || 0}只`} 
          style={{ backgroundColor: '#52c41a' }} 
        />
      ),
    },
    {
      title: '联系人',
      dataIndex: 'contact_person',
      key: 'contact_person',
      width: 100,
    },
    {
      title: '联系电话',
      dataIndex: 'contact_phone',
      key: 'contact_phone',
      width: 130,
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      fixed: 'right',
      render: (_, record) => (
        <Space>
          <Tooltip title="查看详情">
            <Button type="text" size="small" icon={<EyeOutlined />} />
          </Tooltip>
          <Tooltip title="编辑">
            <Button 
              type="text" 
              size="small" 
              icon={<EditOutlined />}
              onClick={() => handleEdit(record)}
            />
          </Tooltip>
          <Tooltip title="删除">
            <Button
              type="text"
              size="small"
              danger
              icon={<DeleteOutlined />}
              onClick={() => handleDelete(record)}
            />
          </Tooltip>
        </Space>
      ),
    },
  ];

  return (
    <div className="farm-list-page">
      <div className="page-header">
        <div className="header-left">
          <Title level={2} className="page-title">羊场管理</Title>
          <Text type="secondary">管理所有羊场信息，包括基本资料、容量和联系方式</Text>
        </div>
        <div className="header-right">
          <Space>
            <Button icon={<ImportOutlined />}>导入</Button>
            <Button icon={<ExportOutlined />}>导出</Button>
            <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
              新建羊场
            </Button>
          </Space>
        </div>
      </div>

      <Row gutter={[16, 16]} className="stats-summary">
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic title="羊场总数" value={farms.length} prefix={<HomeOutlined />} />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic 
              title="总容量" 
              value={farms.reduce((sum, f) => sum + (f.capacity || 0), 0)} 
              suffix="只" 
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic title="育种场" value={farms.filter(f => f.farm_type === 'breeding').length} />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card size="small">
            <Statistic title="商业场" value={farms.filter(f => f.farm_type === 'commercial').length} />
          </Card>
        </Col>
      </Row>

      <Card className="table-card">
        <div className="table-toolbar">
          <Search
            placeholder="搜索羊场名称或编号..."
            allowClear
            style={{ width: 300 }}
            prefix={<SearchOutlined />}
            onChange={(e) => setSearchText(e.target.value)}
          />
        </div>
        <Table
          columns={columns}
          dataSource={filteredFarms}
          loading={loading}
          rowKey="id"
          pagination={{
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条记录`,
          }}
          scroll={{ x: 900 }}
        />
      </Card>

      <Modal
        title={editingFarm ? '编辑羊场' : '新建羊场'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => setModalVisible(false)}
        width={640}
        okText={editingFarm ? '保存' : '创建'}
        cancelText="取消"
      >
        <Form form={form} layout="vertical" className="farm-form">
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="code"
                label="羊场编号"
                rules={[{ required: true, message: '请输入羊场编号' }]}
              >
                <Input placeholder="例如: FARM001" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="name"
                label="羊场名称"
                rules={[{ required: true, message: '请输入羊场名称' }]}
              >
                <Input placeholder="请输入羊场名称" />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="farm_type"
                label="羊场类型"
                rules={[{ required: true, message: '请选择羊场类型' }]}
              >
                <Select placeholder="请选择羊场类型">
                  <Select.Option value="breeding">
                    <Tag color="purple">育种场</Tag>
                  </Select.Option>
                  <Select.Option value="commercial">
                    <Tag color="green">商业场</Tag>
                  </Select.Option>
                  <Select.Option value="research">
                    <Tag color="blue">研究场</Tag>
                  </Select.Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="capacity"
                label="设计容量"
                rules={[{ required: true, message: '请输入容量' }]}
              >
                <Input type="number" placeholder="请输入容量" suffix="只" />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="address" label="详细地址">
            <Input.TextArea rows={2} placeholder="请输入详细地址" />
          </Form.Item>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="contact_person" label="联系人">
                <Input placeholder="请输入联系人姓名" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="contact_phone" label="联系电话">
                <Input placeholder="请输入联系电话" />
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Modal>
    </div>
  );
};

export default FarmList;
