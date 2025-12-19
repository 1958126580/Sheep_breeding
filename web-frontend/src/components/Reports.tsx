import React, { useState, useEffect } from 'react';
import {
  Card, Table, Button, Modal, Form, Select, DatePicker, Space,
  Typography, Tag, Tabs, message, Progress, Divider, Row, Col,
  Statistic, Timeline, Descriptions, Empty, Spin
} from 'antd';
import {
  DownloadOutlined, FileTextOutlined, BarChartOutlined,
  CalendarOutlined, ClockCircleOutlined, CheckCircleOutlined,
  FilePdfOutlined, FileExcelOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import moment from 'moment';
import { useTranslation } from 'react-i18next';
import './Reports.scss';

const { Title, Text, Paragraph } = Typography;
const { TabPane } = Tabs;
const { RangePicker } = DatePicker;

interface ReportConfig {
  id: string;
  name: string;
  description: string;
  icon: React.ReactNode;
  type: 'breeding' | 'health' | 'production' | 'genetic';
  fields: string[];
}

interface GeneratedReport {
  id: number;
  name: string;
  type: string;
  period: string;
  status: 'pending' | 'generating' | 'completed' | 'failed';
  createdAt: string;
  fileUrl?: string;
  fileSize?: string;
}

// 报表类型配置
const REPORT_CONFIGS: ReportConfig[] = [
  {
    id: 'breeding',
    name: '育种分析报告',
    description: '包含育种值统计、遗传进展、选配建议等',
    icon: <BarChartOutlined style={{ fontSize: 32, color: '#1890ff' }} />,
    type: 'breeding',
    fields: ['育种值分布', '遗传进展趋势', 'Top育种动物', '近交系数分析', '选配建议'],
  },
  {
    id: 'health',
    name: '健康管理报告',
    description: '疫苗接种、疾病统计、治疗记录汇总',
    icon: <FileTextOutlined style={{ fontSize: 32, color: '#52c41a' }} />,
    type: 'health',
    fields: ['疫苗接种统计', '疾病发生率', '治疗效果分析', '健康预警'],
  },
  {
    id: 'production',
    name: '生产报告',
    description: '繁殖率、生长性能、产量统计',
    icon: <FileTextOutlined style={{ fontSize: 32, color: '#fa8c16' }} />,
    type: 'production',
    fields: ['繁殖率统计', '产羔率分析', '生长曲线', '饲料转化率'],
  },
  {
    id: 'genetic',
    name: '遗传分析报告',
    description: 'GWAS结果、基因型分析、分子标记报告',
    icon: <BarChartOutlined style={{ fontSize: 32, color: '#722ed1' }} />,
    type: 'genetic',
    fields: ['GWAS显著SNP', '基因型频率', 'ROH分析', '群体结构'],
  },
];

export const ReportCenter: React.FC = () => {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState('generate');
  const [generatingReport, setGeneratingReport] = useState<string | null>(null);
  const [reports, setReports] = useState<GeneratedReport[]>([]);
  const [modalVisible, setModalVisible] = useState(false);
  const [selectedReport, setSelectedReport] = useState<ReportConfig | null>(null);
  const [progress, setProgress] = useState(0);
  const [form] = Form.useForm();

  useEffect(() => {
    loadReports();
  }, []);

  const loadReports = async () => {
    // 模拟加载历史报表
    setReports([
      { id: 1, name: '2024年Q4育种分析报告', type: 'breeding', period: '2024-10 ~ 2024-12', status: 'completed', createdAt: '2024-12-15', fileUrl: '/reports/breeding_2024q4.pdf', fileSize: '2.5 MB' },
      { id: 2, name: '2024年12月健康管理报告', type: 'health', period: '2024-12', status: 'completed', createdAt: '2024-12-10', fileUrl: '/reports/health_202412.pdf', fileSize: '1.8 MB' },
      { id: 3, name: '2024年度遗传进展报告', type: 'genetic', period: '2024', status: 'completed', createdAt: '2024-12-01', fileUrl: '/reports/genetic_2024.pdf', fileSize: '5.2 MB' },
    ]);
  };

  const handleGenerateReport = (config: ReportConfig) => {
    setSelectedReport(config);
    form.resetFields();
    setModalVisible(true);
  };

  const handleSubmitGenerate = async () => {
    try {
      const values = await form.validateFields();
      setModalVisible(false);
      setGeneratingReport(selectedReport?.id || null);
      setProgress(0);

      // 模拟生成进度
      const interval = setInterval(() => {
        setProgress(prev => {
          if (prev >= 100) {
            clearInterval(interval);
            setGeneratingReport(null);
            message.success('报告生成成功！');
            
            // 添加新报告到列表
            const newReport: GeneratedReport = {
              id: Date.now(),
              name: `${selectedReport?.name} - ${moment().format('YYYY-MM-DD')}`,
              type: selectedReport?.type || '',
              period: values.period ? `${values.period[0].format('YYYY-MM')} ~ ${values.period[1].format('YYYY-MM')}` : moment().format('YYYY-MM'),
              status: 'completed',
              createdAt: moment().format('YYYY-MM-DD HH:mm'),
              fileUrl: '/reports/new_report.pdf',
              fileSize: '3.1 MB',
            };
            setReports(prev => [newReport, ...prev]);
            
            return 100;
          }
          return prev + Math.random() * 15;
        });
      }, 500);
    } catch (error) {
      // validation error
    }
  };

  const handleDownload = (report: GeneratedReport) => {
    if (report.fileUrl) {
      message.success(`正在下载: ${report.name}`);
      // window.open(report.fileUrl, '_blank');
    }
  };

  const reportColumns: ColumnsType<GeneratedReport> = [
    {
      title: '报告名称',
      dataIndex: 'name',
      key: 'name',
      render: (name, record) => (
        <Space>
          <FilePdfOutlined style={{ color: '#ff4d4f' }} />
          <Text strong>{name}</Text>
        </Space>
      ),
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      render: type => {
        const typeConfig: Record<string, { color: string; label: string }> = {
          breeding: { color: 'blue', label: '育种分析' },
          health: { color: 'green', label: '健康管理' },
          production: { color: 'orange', label: '生产报告' },
          genetic: { color: 'purple', label: '遗传分析' },
        };
        const cfg = typeConfig[type];
        return <Tag color={cfg?.color}>{cfg?.label}</Tag>;
      },
    },
    {
      title: '报告周期',
      dataIndex: 'period',
      key: 'period',
      render: period => (
        <Space>
          <CalendarOutlined />
          <Text>{period}</Text>
        </Space>
      ),
    },
    {
      title: '生成时间',
      dataIndex: 'createdAt',
      key: 'createdAt',
      render: time => (
        <Space>
          <ClockCircleOutlined />
          <Text type="secondary">{time}</Text>
        </Space>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: status => {
        const statusConfig: Record<string, { color: string; icon: React.ReactNode; label: string }> = {
          pending: { color: 'default', icon: <ClockCircleOutlined />, label: '等待中' },
          generating: { color: 'processing', icon: <Spin size="small" />, label: '生成中' },
          completed: { color: 'success', icon: <CheckCircleOutlined />, label: '已完成' },
          failed: { color: 'error', icon: <ClockCircleOutlined />, label: '失败' },
        };
        const cfg = statusConfig[status];
        return <Tag color={cfg?.color} icon={cfg?.icon}>{cfg?.label}</Tag>;
      },
    },
    {
      title: '文件大小',
      dataIndex: 'fileSize',
      key: 'fileSize',
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Button
          type="primary"
          icon={<DownloadOutlined />}
          disabled={record.status !== 'completed'}
          onClick={() => handleDownload(record)}
        >
          下载
        </Button>
      ),
    },
  ];

  return (
    <div className="report-center">
      <Card>
        <div className="page-header">
          <div>
            <Title level={3}>
              <FileTextOutlined /> 报表中心
            </Title>
            <Text type="secondary">自动生成育种报告、健康报告、生产报告等</Text>
          </div>
        </div>

        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          <TabPane tab="生成报告" key="generate">
            <Row gutter={[24, 24]}>
              {REPORT_CONFIGS.map(config => (
                <Col xs={24} sm={12} lg={6} key={config.id}>
                  <Card 
                    className={`report-card ${generatingReport === config.id ? 'generating' : ''}`}
                    hoverable
                    onClick={() => !generatingReport && handleGenerateReport(config)}
                  >
                    <div className="report-icon">{config.icon}</div>
                    <Title level={5}>{config.name}</Title>
                    <Paragraph type="secondary" ellipsis={{ rows: 2 }}>
                      {config.description}
                    </Paragraph>
                    <div className="report-fields">
                      {config.fields.slice(0, 3).map((field, i) => (
                        <Tag key={i} color="default" style={{ marginBottom: 4 }}>{field}</Tag>
                      ))}
                      {config.fields.length > 3 && (
                        <Tag>+{config.fields.length - 3}</Tag>
                      )}
                    </div>
                    {generatingReport === config.id && (
                      <Progress percent={Math.round(progress)} size="small" status="active" />
                    )}
                  </Card>
                </Col>
              ))}
            </Row>
          </TabPane>

          <TabPane tab="历史报告" key="history">
            {reports.length > 0 ? (
              <Table
                columns={reportColumns}
                dataSource={reports}
                rowKey="id"
                pagination={{ pageSize: 10 }}
              />
            ) : (
              <Empty description="暂无历史报告" />
            )}
          </TabPane>

          <TabPane tab="定时报告" key="scheduled">
            <Empty 
              description="定时报告功能开发中" 
              image={Empty.PRESENTED_IMAGE_SIMPLE}
            />
          </TabPane>
        </Tabs>
      </Card>

      {/* 生成报告弹窗 */}
      <Modal
        title={`生成${selectedReport?.name || '报告'}`}
        open={modalVisible}
        onOk={handleSubmitGenerate}
        onCancel={() => setModalVisible(false)}
        okText="开始生成"
        cancelText="取消"
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="period"
            label="报告周期"
            rules={[{ required: true, message: '请选择报告周期' }]}
          >
            <RangePicker picker="month" style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item
            name="format"
            label="导出格式"
            initialValue="pdf"
          >
            <Select>
              <Select.Option value="pdf">
                <FilePdfOutlined /> PDF 格式
              </Select.Option>
              <Select.Option value="xlsx">
                <FileExcelOutlined /> Excel 格式
              </Select.Option>
            </Select>
          </Form.Item>
          <Form.Item
            name="farms"
            label="选择羊场"
          >
            <Select mode="multiple" placeholder="留空表示全部羊场">
              <Select.Option value="all">全部羊场</Select.Option>
            </Select>
          </Form.Item>
        </Form>

        <Divider />
        
        <Title level={5}>报告内容预览</Title>
        <div className="report-preview">
          {selectedReport?.fields.map((field, i) => (
            <Tag key={i} color="blue" style={{ margin: 4 }}>{field}</Tag>
          ))}
        </div>
      </Modal>
    </div>
  );
};

export default ReportCenter;
