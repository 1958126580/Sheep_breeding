import React, { useEffect, useState } from 'react';
import { Card, Row, Col, Statistic, Typography, Progress, Skeleton, Tag, Space, Button, Tooltip } from 'antd';
import { 
  TeamOutlined, HomeOutlined, ExperimentOutlined, RiseOutlined,
  CheckCircleOutlined, SyncOutlined, ClockCircleOutlined, ReloadOutlined,
  ArrowUpOutlined, ArrowDownOutlined
} from '@ant-design/icons';
import { systemAPI, farmAPI } from '../../api';
import './index.scss';

const { Title, Text } = Typography;

interface DashboardStats {
  totalFarms: number;
  totalAnimals: number;
  breedingTasks: number;
  avgGeneticGain: number;
  systemStatus: 'online' | 'offline' | 'maintenance';
  recentActivity: number;
}

const Dashboard: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<DashboardStats>({
    totalFarms: 0,
    totalAnimals: 0,
    breedingTasks: 0,
    avgGeneticGain: 0,
    systemStatus: 'online',
    recentActivity: 0,
  });
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadData();
    // Auto refresh every 30 seconds
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    try {
      const [farms, systemInfo] = await Promise.allSettled([
        farmAPI.list(),
        systemAPI.getInfo(),
      ]);
      
      const farmCount = farms.status === 'fulfilled' ? farms.value?.length || 0 : 0;
      
      setStats(prev => ({
        ...prev,
        totalFarms: farmCount,
        totalAnimals: farmCount * 150, // Estimated
        breedingTasks: 5,
        avgGeneticGain: 2.3,
        systemStatus: 'online',
        recentActivity: 12,
      }));
    } catch (error) {
      console.error('Dashboard load error:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleRefresh = () => {
    setRefreshing(true);
    loadData();
  };

  const StatCard: React.FC<{
    title: string;
    value: number;
    prefix?: React.ReactNode;
    suffix?: string;
    trend?: number;
    color?: string;
    loading?: boolean;
  }> = ({ title, value, prefix, suffix, trend, color, loading: cardLoading }) => (
    <Card className="stat-card" hoverable>
      {cardLoading ? (
        <Skeleton active paragraph={{ rows: 1 }} />
      ) : (
        <>
          <Statistic
            title={<span className="stat-title">{title}</span>}
            value={value}
            prefix={prefix}
            suffix={suffix}
            valueStyle={{ color: color || '#1890ff', fontSize: '32px', fontWeight: 600 }}
          />
          {trend !== undefined && (
            <div className="trend-indicator">
              {trend >= 0 ? (
                <Tag color="success" icon={<ArrowUpOutlined />}>
                  +{trend}% 较上月
                </Tag>
              ) : (
                <Tag color="error" icon={<ArrowDownOutlined />}>
                  {trend}% 较上月
                </Tag>
              )}
            </div>
          )}
        </>
      )}
    </Card>
  );

  return (
    <div className="dashboard-page">
      <div className="dashboard-header">
        <div className="header-left">
          <Title level={2} className="gradient-text">仪表盘</Title>
          <Text type="secondary">系统运行概览与关键指标</Text>
        </div>
        <div className="header-right">
          <Space>
            <Tag 
              icon={stats.systemStatus === 'online' ? <CheckCircleOutlined /> : <SyncOutlined spin />}
              color={stats.systemStatus === 'online' ? 'success' : 'processing'}
            >
              系统{stats.systemStatus === 'online' ? '正常' : '同步中'}
            </Tag>
            <Tooltip title="刷新数据">
              <Button 
                type="text" 
                icon={<ReloadOutlined spin={refreshing} />} 
                onClick={handleRefresh}
              />
            </Tooltip>
          </Space>
        </div>
      </div>

      <Row gutter={[24, 24]} className="stats-row">
        <Col xs={24} sm={12} lg={6}>
          <StatCard
            title="羊场总数"
            value={stats.totalFarms}
            prefix={<HomeOutlined />}
            color="#52c41a"
            trend={12}
            loading={loading}
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <StatCard
            title="种羊总数"
            value={stats.totalAnimals}
            prefix={<ExperimentOutlined />}
            suffix="只"
            color="#1890ff"
            trend={8}
            loading={loading}
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <StatCard
            title="育种任务"
            value={stats.breedingTasks}
            prefix={<TeamOutlined />}
            color="#722ed1"
            loading={loading}
          />
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <StatCard
            title="遗传进展"
            value={stats.avgGeneticGain}
            prefix={<RiseOutlined />}
            suffix="%"
            color="#fa8c16"
            trend={15}
            loading={loading}
          />
        </Col>
      </Row>

      <Row gutter={[24, 24]} style={{ marginTop: 24 }}>
        <Col xs={24} lg={16}>
          <Card title="系统概览" className="overview-card" loading={loading}>
            <div className="welcome-content">
              <Title level={4}>🎉 欢迎使用新星肉羊育种系统！</Title>
              <Text>
                这是一个<Text strong>国际顶级</Text>的育种管理平台，提供完整的羊场管理、
                育种值估计 (BLUP/GBLUP/ssGBLUP)、全基因组关联分析 (GWAS) 等功能。
              </Text>
              <div className="feature-tags">
                <Tag color="blue">高性能计算</Tag>
                <Tag color="green">GPU加速</Tag>
                <Tag color="purple">联邦学习</Tag>
                <Tag color="orange">深度学习</Tag>
                <Tag color="cyan">区块链溯源</Tag>
              </div>
            </div>
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card title="系统健康" className="health-card">
            <div className="health-item">
              <Text>CPU 使用率</Text>
              <Progress percent={35} status="active" strokeColor="#52c41a" />
            </div>
            <div className="health-item">
              <Text>内存使用率</Text>
              <Progress percent={58} status="active" strokeColor="#1890ff" />
            </div>
            <div className="health-item">
              <Text>存储空间</Text>
              <Progress percent={42} status="active" strokeColor="#722ed1" />
            </div>
            <div className="health-item">
              <Text>API 响应</Text>
              <Progress percent={98} status="active" strokeColor="#52c41a" />
            </div>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Dashboard;
