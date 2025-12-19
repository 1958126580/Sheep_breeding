import React, { useEffect, useState } from 'react';
import { 
  Card, Table, Button, message, Modal, Form, Input, Select, 
  Typography, Tag, Row, Col, Statistic, Progress, Space, Tabs,
  Tooltip, Badge, Spin, Empty, Divider
} from 'antd';
import { 
  PlusOutlined, PlayCircleOutlined, ExperimentOutlined,
  BarChartOutlined, LineChartOutlined, CheckCircleOutlined,
  ClockCircleOutlined, LoadingOutlined, EyeOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { breedingValueAPI } from '../../api';
import { ManhattanPlot, GeneticTrendChart } from '../../components/Charts';
import './BreedingAnalysis.scss';

const { Title, Text, Paragraph } = Typography;
const { TabPane } = Tabs;

interface BreedingRun {
  id: number;
  run_name: string;
  method: string;
  trait_id: number;
  trait_name?: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  started_at: string;
  completed_at?: string;
  n_animals?: number;
  n_records?: number;
}

const BreedingAnalysis: React.FC = () => {
  const [runs, setRuns] = useState<BreedingRun[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [resultModalVisible, setResultModalVisible] = useState(false);
  const [selectedRun, setSelectedRun] = useState<BreedingRun | null>(null);
  const [activeTab, setActiveTab] = useState('runs');
  const [form] = Form.useForm();

  // 模拟GWAS数据
  const [gwasData] = useState(() => {
    const data = [];
    for (let chr = 1; chr <= 26; chr++) {
      for (let i = 0; i < 50; i++) {
        data.push({
          chromosome: chr,
          position: Math.floor(Math.random() * 150000000),
          pValue: Math.pow(10, -1 * (Math.random() * 10)),
          snpId: `rs${chr}_${i}`,
        });
      }
    }
    return data;
  });

  // 模拟遗传趋势数据
  const [trendData] = useState(() => {
    const data = [];
    for (let year = 2015; year <= 2024; year++) {
      data.push({
        year,
        ebv: 0.5 + (year - 2015) * 0.15 + (Math.random() - 0.5) * 0.1,
        accuracy: 0.6 + (year - 2015) * 0.02,
        traitName: '断奶重',
      });
    }
    return data;
  });

  useEffect(() => {
    loadRuns();
  }, []);

  const loadRuns = async () => {
    setLoading(true);
    try {
      const data = await breedingValueAPI.listRuns();
      setRuns(data || []);
    } catch (error) {
      // 使用模拟数据
      setRuns([
        { id: 1, run_name: '2024年断奶重BLUP评估', method: 'BLUP', trait_id: 1, trait_name: '断奶重', status: 'completed', started_at: '2024-12-01T10:00:00', completed_at: '2024-12-01T10:05:30', n_animals: 1500, n_records: 3200 },
        { id: 2, run_name: '2024年日增重GBLUP评估', method: 'GBLUP', trait_id: 2, trait_name: '日增重', status: 'completed', started_at: '2024-12-10T14:00:00', completed_at: '2024-12-10T14:12:45', n_animals: 1200, n_records: 2800 },
        { id: 3, run_name: '2024年产羔数ssGBLUP评估', method: 'ssGBLUP', trait_id: 3, trait_name: '产羔数', status: 'running', started_at: '2024-12-19T08:00:00', n_animals: 800 },
        { id: 4, run_name: '多性状综合评估', method: 'GBLUP', trait_id: 4, trait_name: '综合指数', status: 'pending', started_at: '2024-12-19T09:00:00' },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    try {
      const values = await form.validateFields();
      const runData = {
        run_name: values.run_name,
        trait_id: values.trait_id,
        method: values.method,
        model_specification: {
          h2: values.h2 || 0.35,
          fixed_effects: ['sex', 'birth_type'],
        },
        use_gpu: values.use_gpu || false,
        num_threads: 4,
      };
      
      await breedingValueAPI.createRun(runData);
      message.success('任务创建成功，已开始后台计算');
      setModalVisible(false);
      form.resetFields();
      loadRuns();
    } catch (error: any) {
      if (error.errorFields) return;
      message.error('创建失败');
    }
  };

  const handleViewResults = (run: BreedingRun) => {
    setSelectedRun(run);
    setResultModalVisible(true);
  };

  // 统计数据
  const stats = {
    total: runs.length,
    completed: runs.filter(r => r.status === 'completed').length,
    running: runs.filter(r => r.status === 'running').length,
    pending: runs.filter(r => r.status === 'pending').length,
  };

  const columns: ColumnsType<BreedingRun> = [
    {
      title: '任务名称',
      dataIndex: 'run_name',
      key: 'run_name',
      render: (name, record) => (
        <Space>
          <ExperimentOutlined style={{ color: '#1890ff' }} />
          <Text strong>{name}</Text>
        </Space>
      ),
    },
    { 
      title: '方法', 
      dataIndex: 'method', 
      key: 'method', 
      render: (m: string) => {
        const colors: Record<string, string> = {
          BLUP: 'blue',
          GBLUP: 'green',
          ssGBLUP: 'purple',
          BayesA: 'orange',
          BayesB: 'red',
        };
        return <Tag color={colors[m] || 'default'}>{m}</Tag>;
      }
    },
    { 
      title: '性状', 
      dataIndex: 'trait_name', 
      key: 'trait_name',
      render: trait => trait || '-',
    },
    {
      title: '动物数',
      dataIndex: 'n_animals',
      key: 'n_animals',
      render: n => n ? n.toLocaleString() : '-',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: status => {
        const statusConfig: Record<string, { color: string; icon: React.ReactNode; text: string }> = {
          pending: { color: 'default', icon: <ClockCircleOutlined />, text: '等待中' },
          running: { color: 'processing', icon: <LoadingOutlined spin />, text: '计算中' },
          completed: { color: 'success', icon: <CheckCircleOutlined />, text: '已完成' },
          failed: { color: 'error', icon: <ClockCircleOutlined />, text: '失败' },
        };
        const cfg = statusConfig[status] || statusConfig.pending;
        return <Tag color={cfg.color} icon={cfg.icon}>{cfg.text}</Tag>;
      },
    },
    {
      title: '开始时间',
      dataIndex: 'started_at',
      key: 'started_at',
      render: time => time ? new Date(time).toLocaleString() : '-',
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space>
          <Tooltip title="查看结果">
            <Button 
              type="text" 
              icon={<EyeOutlined />}
              disabled={record.status !== 'completed'}
              onClick={() => handleViewResults(record)}
            />
          </Tooltip>
          <Tooltip title="重新运行">
            <Button 
              type="text" 
              icon={<PlayCircleOutlined />}
              disabled={record.status === 'running'}
            />
          </Tooltip>
        </Space>
      ),
    },
  ];

  return (
    <div className="breeding-analysis-page">
      {/* 统计卡片 */}
      <Row gutter={16} className="stats-row">
        <Col xs={12} sm={6}>
          <Card>
            <Statistic title="总任务数" value={stats.total} prefix={<ExperimentOutlined />} />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card>
            <Statistic 
              title="已完成" 
              value={stats.completed} 
              valueStyle={{ color: '#52c41a' }}
              prefix={<CheckCircleOutlined />}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card>
            <Statistic 
              title="运行中" 
              value={stats.running}
              valueStyle={{ color: '#1890ff' }}
              prefix={<LoadingOutlined />}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card>
            <Statistic 
              title="等待中" 
              value={stats.pending}
              prefix={<ClockCircleOutlined />}
            />
          </Card>
        </Col>
      </Row>

      {/* 主内容 */}
      <Card className="main-card">
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          <TabPane 
            tab={<span><ExperimentOutlined /> 评估任务</span>} 
            key="runs"
          >
            <div className="table-toolbar">
              <Button 
                type="primary" 
                icon={<PlusOutlined />} 
                onClick={() => setModalVisible(true)}
              >
                新建评估任务
              </Button>
            </div>
            <Table 
              columns={columns} 
              dataSource={runs} 
              rowKey="id" 
              loading={loading}
              pagination={{ pageSize: 10 }}
            />
          </TabPane>

          <TabPane 
            tab={<span><BarChartOutlined /> 曼哈顿图</span>} 
            key="manhattan"
          >
            <ManhattanPlot 
              data={gwasData}
              threshold={5e-8}
              title="GWAS 分析结果"
            />
          </TabPane>

          <TabPane 
            tab={<span><LineChartOutlined /> 遗传趋势</span>} 
            key="trend"
          >
            <GeneticTrendChart 
              data={trendData}
              traits={['断奶重', '日增重', '产羔数']}
              title="遗传进展趋势"
            />
          </TabPane>
        </Tabs>
      </Card>

      {/* 新建任务弹窗 */}
      <Modal 
        title="新建育种值评估任务" 
        open={modalVisible} 
        onOk={handleCreate} 
        onCancel={() => setModalVisible(false)}
        width={600}
        okText="开始评估"
        cancelText="取消"
      >
        <Form form={form} layout="vertical">
          <Form.Item 
            name="run_name" 
            label="任务名称" 
            rules={[{ required: true, message: '请输入任务名称' }]}
          >
            <Input placeholder="例如: 2024年断奶重GBLUP评估" />
          </Form.Item>
          
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item 
                name="method" 
                label="评估方法" 
                rules={[{ required: true, message: '请选择方法' }]}
              >
                <Select placeholder="选择评估方法">
                  <Select.Option value="BLUP">
                    <Space>
                      <Tag color="blue">BLUP</Tag>
                      <span>基于系谱</span>
                    </Space>
                  </Select.Option>
                  <Select.Option value="GBLUP">
                    <Space>
                      <Tag color="green">GBLUP</Tag>
                      <span>基因组BLUP</span>
                    </Space>
                  </Select.Option>
                  <Select.Option value="ssGBLUP">
                    <Space>
                      <Tag color="purple">ssGBLUP</Tag>
                      <span>单步基因组</span>
                    </Space>
                  </Select.Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item 
                name="trait_id" 
                label="目标性状" 
                rules={[{ required: true, message: '请选择性状' }]}
              >
                <Select placeholder="选择目标性状">
                  <Select.Option value={1}>断奶重</Select.Option>
                  <Select.Option value={2}>日增重</Select.Option>
                  <Select.Option value={3}>产羔数</Select.Option>
                  <Select.Option value={4}>胴体重</Select.Option>
                  <Select.Option value={5}>眼肌面积</Select.Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="h2" label="遗传力估计" initialValue={0.35}>
            <Select>
              <Select.Option value={0.25}>0.25 (低)</Select.Option>
              <Select.Option value={0.35}>0.35 (中)</Select.Option>
              <Select.Option value={0.45}>0.45 (高)</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item name="use_gpu" label="使用GPU加速" initialValue={true}>
            <Select>
              <Select.Option value={true}>是 (推荐)</Select.Option>
              <Select.Option value={false}>否</Select.Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>

      {/* 结果查看弹窗 */}
      <Modal
        title={`评估结果 - ${selectedRun?.run_name || ''}`}
        open={resultModalVisible}
        onCancel={() => setResultModalVisible(false)}
        footer={null}
        width={800}
      >
        {selectedRun && (
          <div className="result-content">
            <Row gutter={16} style={{ marginBottom: 24 }}>
              <Col span={8}>
                <Statistic title="评估动物数" value={selectedRun.n_animals || 0} />
              </Col>
              <Col span={8}>
                <Statistic title="表型记录数" value={selectedRun.n_records || 0} />
              </Col>
              <Col span={8}>
                <Statistic 
                  title="计算时间" 
                  value={selectedRun.completed_at ? 
                    Math.round((new Date(selectedRun.completed_at).getTime() - 
                    new Date(selectedRun.started_at).getTime()) / 1000) : 0
                  } 
                  suffix="秒"
                />
              </Col>
            </Row>
            <Divider />
            <Paragraph>
              <Text strong>评估方法:</Text> {selectedRun.method}
            </Paragraph>
            <Paragraph>
              <Text strong>目标性状:</Text> {selectedRun.trait_name}
            </Paragraph>
            <Paragraph type="secondary">
              详细结果可通过API接口 <Text code>/api/v1/breeding-values/runs/{selectedRun.id}/results</Text> 获取
            </Paragraph>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default BreedingAnalysis;
