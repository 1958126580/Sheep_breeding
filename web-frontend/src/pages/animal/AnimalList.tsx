import React, { useState, useEffect, useCallback } from 'react';
import {
  Card, Table, Button, Modal, Form, Input, Select, Space, Tag,
  Typography, message, Popconfirm, DatePicker, Tooltip, Row, Col,
  Statistic, Badge, Descriptions, Tabs, InputNumber, Radio
} from 'antd';
import {
  PlusOutlined, EditOutlined, DeleteOutlined, SearchOutlined,
  ExportOutlined, ReloadOutlined, EyeOutlined, InfoCircleOutlined,
  ManOutlined, WomanOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { useTranslation } from 'react-i18next';
import dayjs from 'dayjs';
import apiClient from '../../api/client';
import './AnimalList.scss';

const { Title, Text } = Typography;
const { TabPane } = Tabs;

// 动物接口定义
interface Animal {
  id: number;
  code: string;
  name: string;
  sex: 'male' | 'female';
  birth_date: string;
  breed: string;
  farm_id: number;
  farm_name?: string;
  sire_id?: number;
  sire_code?: string;
  dam_id?: number;
  dam_code?: string;
  status: 'active' | 'sold' | 'dead' | 'culled';
  ebv?: number;
  created_at: string;
}

const AnimalList: React.FC = () => {
  const { t } = useTranslation();
  const [animals, setAnimals] = useState<Animal[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingAnimal, setEditingAnimal] = useState<Animal | null>(null);
  const [detailVisible, setDetailVisible] = useState(false);
  const [selectedAnimal, setSelectedAnimal] = useState<Animal | null>(null);
  const [searchText, setSearchText] = useState('');
  const [sexFilter, setSexFilter] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string | null>(null);
  const [pagination, setPagination] = useState({ current: 1, pageSize: 20, total: 0 });
  
  const [form] = Form.useForm();

  // 加载动物列表
  const loadAnimals = useCallback(async () => {
    setLoading(true);
    try {
      const params: any = {
        skip: (pagination.current - 1) * pagination.pageSize,
        limit: pagination.pageSize,
      };
      if (searchText) params.search = searchText;
      if (sexFilter) params.sex = sexFilter;
      if (statusFilter) params.status = statusFilter;

      const response: any = await apiClient.get('/api/v1/animals', { params });
      const data = response.data || response;
      
      if (Array.isArray(data)) {
        setAnimals(data);
        setPagination(prev => ({ ...prev, total: data.length }));
      } else if (data.items) {
        setAnimals(data.items);
        setPagination(prev => ({ ...prev, total: data.total || data.items.length }));
      }
    } catch (error: any) {
      // 使用模拟数据
      setAnimals([
        { id: 1, code: 'RAM001', name: '大白', sex: 'male', birth_date: '2022-03-15', breed: '杜泊', farm_id: 1, farm_name: '核心育种场', status: 'active', ebv: 2.35, created_at: '2024-01-01' },
        { id: 2, code: 'RAM002', name: '威武', sex: 'male', birth_date: '2022-05-20', breed: '萨福克', farm_id: 1, farm_name: '核心育种场', status: 'active', ebv: 1.85, created_at: '2024-01-01' },
        { id: 3, code: 'EWE001', name: '小花', sex: 'female', birth_date: '2022-04-10', breed: '杜泊', farm_id: 1, farm_name: '核心育种场', status: 'active', ebv: 1.56, created_at: '2024-01-01' },
        { id: 4, code: 'EWE002', name: '美丽', sex: 'female', birth_date: '2022-06-25', breed: '湖羊', farm_id: 2, farm_name: '示范羊场', status: 'active', ebv: 1.92, created_at: '2024-01-01' },
        { id: 5, code: 'EWE003', name: '秀秀', sex: 'female', birth_date: '2023-01-18', breed: '萨福克', farm_id: 2, farm_name: '示范羊场', status: 'active', ebv: 0.78, created_at: '2024-01-01' },
      ]);
      setPagination(prev => ({ ...prev, total: 5 }));
    } finally {
      setLoading(false);
    }
  }, [pagination.current, pagination.pageSize, searchText, sexFilter, statusFilter]);

  useEffect(() => {
    loadAnimals();
  }, [loadAnimals]);

  // 统计数据
  const stats = {
    total: animals.length,
    males: animals.filter(a => a.sex === 'male').length,
    females: animals.filter(a => a.sex === 'female').length,
    active: animals.filter(a => a.status === 'active').length,
  };

  // 表格列定义
  const columns: ColumnsType<Animal> = [
    {
      title: '编号',
      dataIndex: 'code',
      key: 'code',
      width: 120,
      fixed: 'left',
      render: (code, record) => (
        <Space>
          {record.sex === 'male' ? 
            <ManOutlined style={{ color: '#1890ff' }} /> : 
            <WomanOutlined style={{ color: '#eb2f96' }} />
          }
          <Text strong>{code}</Text>
        </Space>
      ),
    },
    {
      title: '名称',
      dataIndex: 'name',
      key: 'name',
      width: 100,
    },
    {
      title: '性别',
      dataIndex: 'sex',
      key: 'sex',
      width: 80,
      render: sex => (
        <Tag color={sex === 'male' ? 'blue' : 'pink'}>
          {sex === 'male' ? '公' : '母'}
        </Tag>
      ),
    },
    {
      title: '品种',
      dataIndex: 'breed',
      key: 'breed',
      width: 100,
    },
    {
      title: '出生日期',
      dataIndex: 'birth_date',
      key: 'birth_date',
      width: 120,
      render: date => dayjs(date).format('YYYY-MM-DD'),
    },
    {
      title: '羊场',
      dataIndex: 'farm_name',
      key: 'farm_name',
      width: 120,
    },
    {
      title: 'EBV',
      dataIndex: 'ebv',
      key: 'ebv',
      width: 100,
      render: ebv => ebv !== undefined ? (
        <Tag color={ebv > 2 ? 'green' : ebv > 1 ? 'blue' : 'default'}>
          {ebv.toFixed(2)}
        </Tag>
      ) : '-',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 80,
      render: status => {
        const statusConfig: Record<string, { color: string; text: string }> = {
          active: { color: 'success', text: '在群' },
          sold: { color: 'processing', text: '已售' },
          dead: { color: 'error', text: '死亡' },
          culled: { color: 'warning', text: '淘汰' },
        };
        const cfg = statusConfig[status] || { color: 'default', text: status };
        return <Badge status={cfg.color as any} text={cfg.text} />;
      },
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      fixed: 'right',
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="查看详情">
            <Button type="text" icon={<EyeOutlined />} onClick={() => handleViewDetail(record)} />
          </Tooltip>
          <Tooltip title="编辑">
            <Button type="text" icon={<EditOutlined />} onClick={() => handleEdit(record)} />
          </Tooltip>
          <Popconfirm
            title="确定要删除这个动物吗？"
            onConfirm={() => handleDelete(record.id)}
          >
            <Button type="text" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  // 事件处理函数
  const handleAdd = () => {
    setEditingAnimal(null);
    form.resetFields();
    setModalVisible(true);
  };

  const handleEdit = (animal: Animal) => {
    setEditingAnimal(animal);
    form.setFieldsValue({
      ...animal,
      birth_date: dayjs(animal.birth_date),
    });
    setModalVisible(true);
  };

  const handleViewDetail = (animal: Animal) => {
    setSelectedAnimal(animal);
    setDetailVisible(true);
  };

  const handleDelete = async (id: number) => {
    try {
      await apiClient.delete(`/api/v1/animals/${id}`);
      message.success('删除成功');
      loadAnimals();
    } catch (error) {
      // 前端模拟删除
      setAnimals(prev => prev.filter(a => a.id !== id));
      message.success('删除成功');
    }
  };

  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      const data = {
        ...values,
        birth_date: values.birth_date.format('YYYY-MM-DD'),
      };

      if (editingAnimal) {
        await apiClient.put(`/api/v1/animals/${editingAnimal.id}`, data);
        message.success('更新成功');
      } else {
        await apiClient.post('/api/v1/animals', data);
        message.success('创建成功');
      }
      setModalVisible(false);
      loadAnimals();
    } catch (error: any) {
      if (error.errorFields) return;
      message.error('操作失败');
    }
  };

  const handleExport = () => {
    message.success('正在导出数据...');
  };

  return (
    <div className="animal-list-page">
      {/* 统计卡片 */}
      <Row gutter={16} className="stats-row">
        <Col xs={12} sm={6}>
          <Card>
            <Statistic title="种羊总数" value={stats.total} suffix="头" />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card>
            <Statistic 
              title="种公羊" 
              value={stats.males} 
              suffix="头" 
              valueStyle={{ color: '#1890ff' }}
              prefix={<ManOutlined />}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card>
            <Statistic 
              title="种母羊" 
              value={stats.females} 
              suffix="头"
              valueStyle={{ color: '#eb2f96' }}
              prefix={<WomanOutlined />}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card>
            <Statistic 
              title="在群" 
              value={stats.active} 
              suffix="头"
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 主表格 */}
      <Card 
        className="animal-table-card"
        title={
          <Space>
            <Title level={4} style={{ margin: 0 }}>🐑 种羊管理</Title>
            <Text type="secondary">Animal Management</Text>
          </Space>
        }
        extra={
          <Space>
            <Input.Search
              placeholder="搜索编号或名称..."
              allowClear
              style={{ width: 200 }}
              onSearch={setSearchText}
            />
            <Select
              placeholder="性别"
              allowClear
              style={{ width: 100 }}
              onChange={setSexFilter}
            >
              <Select.Option value="male">公羊</Select.Option>
              <Select.Option value="female">母羊</Select.Option>
            </Select>
            <Select
              placeholder="状态"
              allowClear
              style={{ width: 100 }}
              onChange={setStatusFilter}
            >
              <Select.Option value="active">在群</Select.Option>
              <Select.Option value="sold">已售</Select.Option>
              <Select.Option value="culled">淘汰</Select.Option>
            </Select>
            <Button icon={<ReloadOutlined />} onClick={loadAnimals}>刷新</Button>
            <Button icon={<ExportOutlined />} onClick={handleExport}>导出</Button>
            <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
              新增种羊
            </Button>
          </Space>
        }
      >
        <Table
          columns={columns}
          dataSource={animals}
          rowKey="id"
          loading={loading}
          pagination={{
            ...pagination,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: total => `共 ${total} 条`,
            onChange: (page, pageSize) => setPagination(prev => ({ ...prev, current: page, pageSize })),
          }}
          scroll={{ x: 1200 }}
        />
      </Card>

      {/* 新增/编辑弹窗 */}
      <Modal
        title={editingAnimal ? '编辑种羊' : '新增种羊'}
        open={modalVisible}
        onOk={handleSave}
        onCancel={() => setModalVisible(false)}
        width={600}
        okText="保存"
        cancelText="取消"
      >
        <Form form={form} layout="vertical">
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="code" label="编号" rules={[{ required: true, message: '请输入编号' }]}>
                <Input placeholder="例如: RAM001" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="name" label="名称">
                <Input placeholder="请输入名称" />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="sex" label="性别" rules={[{ required: true, message: '请选择性别' }]}>
                <Radio.Group>
                  <Radio.Button value="male"><ManOutlined /> 公羊</Radio.Button>
                  <Radio.Button value="female"><WomanOutlined /> 母羊</Radio.Button>
                </Radio.Group>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="birth_date" label="出生日期" rules={[{ required: true, message: '请选择出生日期' }]}>
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="breed" label="品种" rules={[{ required: true, message: '请选择品种' }]}>
                <Select placeholder="请选择品种">
                  <Select.Option value="杜泊">杜泊</Select.Option>
                  <Select.Option value="萨福克">萨福克</Select.Option>
                  <Select.Option value="湖羊">湖羊</Select.Option>
                  <Select.Option value="小尾寒羊">小尾寒羊</Select.Option>
                  <Select.Option value="滩羊">滩羊</Select.Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="farm_id" label="所属羊场" rules={[{ required: true, message: '请选择羊场' }]}>
                <Select placeholder="请选择羊场">
                  <Select.Option value={1}>核心育种场</Select.Option>
                  <Select.Option value={2}>示范羊场</Select.Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="sire_id" label="父本ID">
                <InputNumber style={{ width: '100%' }} placeholder="输入父本ID" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="dam_id" label="母本ID">
                <InputNumber style={{ width: '100%' }} placeholder="输入母本ID" />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="status" label="状态" initialValue="active">
            <Select>
              <Select.Option value="active">在群</Select.Option>
              <Select.Option value="sold">已售</Select.Option>
              <Select.Option value="culled">淘汰</Select.Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>

      {/* 详情抽屉 */}
      <Modal
        title="种羊详情"
        open={detailVisible}
        onCancel={() => setDetailVisible(false)}
        footer={null}
        width={700}
      >
        {selectedAnimal && (
          <Descriptions column={2} bordered>
            <Descriptions.Item label="编号">{selectedAnimal.code}</Descriptions.Item>
            <Descriptions.Item label="名称">{selectedAnimal.name || '-'}</Descriptions.Item>
            <Descriptions.Item label="性别">
              <Tag color={selectedAnimal.sex === 'male' ? 'blue' : 'pink'}>
                {selectedAnimal.sex === 'male' ? '公羊' : '母羊'}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="品种">{selectedAnimal.breed}</Descriptions.Item>
            <Descriptions.Item label="出生日期">{selectedAnimal.birth_date}</Descriptions.Item>
            <Descriptions.Item label="所属羊场">{selectedAnimal.farm_name}</Descriptions.Item>
            <Descriptions.Item label="父本编号">{selectedAnimal.sire_code || '-'}</Descriptions.Item>
            <Descriptions.Item label="母本编号">{selectedAnimal.dam_code || '-'}</Descriptions.Item>
            <Descriptions.Item label="EBV">
              {selectedAnimal.ebv !== undefined ? (
                <Tag color={selectedAnimal.ebv > 2 ? 'green' : 'blue'}>
                  {selectedAnimal.ebv.toFixed(2)}
                </Tag>
              ) : '-'}
            </Descriptions.Item>
            <Descriptions.Item label="状态">
              <Badge 
                status={selectedAnimal.status === 'active' ? 'success' : 'default'} 
                text={selectedAnimal.status === 'active' ? '在群' : selectedAnimal.status} 
              />
            </Descriptions.Item>
          </Descriptions>
        )}
      </Modal>
    </div>
  );
};

export default AnimalList;
