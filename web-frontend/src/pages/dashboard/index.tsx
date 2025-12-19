import React, { useEffect, useState } from 'react';
import { Card, Row, Col, Statistic, Typography } from 'antd';
import { TeamOutlined, HomeOutlined, ExperimentOutlined, RiseOutlined } from '@ant-design/icons';
import { systemAPI, farmAPI } from '../../api';

const { Title } = Typography;

const Dashboard: React.FC = () => {
  const [stats, setStats] = useState({ totalFarms: 0, totalAnimals: 0 });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const farms = await farmAPI.list();
      setStats({ ...stats, totalFarms: farms?.length || 0 });
    } catch (error) {
      console.error(error);
    }
  };

  return (
    <div>
      <Title level={2}>仪表盘</Title>
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic title="羊场总数" value={stats.totalFarms} prefix={<HomeOutlined />} />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic title="种羊总数" value={stats.totalAnimals} prefix={<ExperimentOutlined />} />
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Dashboard;
