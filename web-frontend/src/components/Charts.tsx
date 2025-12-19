import React, { useEffect, useRef, useState } from 'react';
import { Card, Select, Spin, Empty, Tooltip, Switch, Space, Typography, Slider, Button } from 'antd';
import { DownloadOutlined, ZoomInOutlined, ZoomOutOutlined, FullscreenOutlined } from '@ant-design/icons';
import * as echarts from 'echarts';
import './Charts.scss';

const { Title, Text } = Typography;

interface ManhattanPlotData {
  chromosome: number;
  position: number;
  pValue: number;
  snpId: string;
}

interface ManhattanPlotProps {
  data: ManhattanPlotData[];
  threshold?: number;
  title?: string;
  loading?: boolean;
  onPointClick?: (point: ManhattanPlotData) => void;
}

// 染色体颜色配置
const CHROMOSOME_COLORS = [
  '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
  '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
  '#aec7e8', '#ffbb78', '#98df8a', '#ff9896', '#c5b0d5',
  '#c49c94', '#f7b6d2', '#c7c7c7', '#dbdb8d', '#9edae5',
  '#393b79', '#637939', '#8c6d31', '#843c39', '#7b4173',
  '#5254a3'
];

export const ManhattanPlot: React.FC<ManhattanPlotProps> = ({
  data,
  threshold = 5e-8,
  title = '曼哈顿图 Manhattan Plot',
  loading = false,
  onPointClick
}) => {
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<echarts.ECharts | null>(null);
  const [showLabels, setShowLabels] = useState(false);
  const [zoom, setZoom] = useState(100);

  useEffect(() => {
    if (!chartRef.current) return;

    chartInstance.current = echarts.init(chartRef.current);

    const handleResize = () => {
      chartInstance.current?.resize();
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chartInstance.current?.dispose();
    };
  }, []);

  useEffect(() => {
    if (!chartInstance.current || !data.length) return;

    // 按染色体分组数据
    const chromosomeData: { [key: number]: ManhattanPlotData[] } = {};
    data.forEach(point => {
      if (!chromosomeData[point.chromosome]) {
        chromosomeData[point.chromosome] = [];
      }
      chromosomeData[point.chromosome].push(point);
    });

    // 计算累积位置
    let cumulativePosition = 0;
    const processedData: any[] = [];
    const chromosomeTicks: { pos: number; label: string }[] = [];

    Object.keys(chromosomeData)
      .map(Number)
      .sort((a, b) => a - b)
      .forEach((chr) => {
        const chrData = chromosomeData[chr];
        const chrStart = cumulativePosition;
        const maxPos = Math.max(...chrData.map(d => d.position));

        chrData.forEach(point => {
          const negLogP = -Math.log10(point.pValue);
          processedData.push({
            value: [cumulativePosition + point.position, negLogP],
            itemStyle: {
              color: CHROMOSOME_COLORS[(chr - 1) % CHROMOSOME_COLORS.length],
              opacity: negLogP > -Math.log10(threshold) ? 1 : 0.6
            },
            emphasis: {
              itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0,0,0,0.3)' }
            },
            data: point
          });
        });

        chromosomeTicks.push({
          pos: chrStart + maxPos / 2,
          label: chr.toString()
        });

        cumulativePosition += maxPos + maxPos * 0.05;
      });

    const thresholdLine = -Math.log10(threshold);

    const option: echarts.EChartsOption = {
      title: {
        text: title,
        left: 'center',
        textStyle: { fontSize: 16, fontWeight: 600 }
      },
      tooltip: {
        trigger: 'item',
        formatter: (params: any) => {
          const d = params.data.data;
          return `
            <div style="padding: 8px;">
              <strong>${d.snpId}</strong><br/>
              染色体: ${d.chromosome}<br/>
              位置: ${d.position.toLocaleString()}<br/>
              P值: ${d.pValue.toExponential(2)}<br/>
              -log10(P): ${(-Math.log10(d.pValue)).toFixed(2)}
            </div>
          `;
        }
      },
      grid: {
        left: '8%',
        right: '5%',
        bottom: '15%',
        top: '15%'
      },
      xAxis: {
        type: 'value',
        name: '染色体 Chromosome',
        nameLocation: 'center',
        nameGap: 35,
        axisLabel: {
          formatter: (value: number) => {
            const tick = chromosomeTicks.find(t => Math.abs(t.pos - value) < cumulativePosition * 0.02);
            return tick ? tick.label : '';
          }
        },
        splitLine: { show: false }
      },
      yAxis: {
        type: 'value',
        name: '-log₁₀(P)',
        nameLocation: 'center',
        nameGap: 40,
        splitLine: { lineStyle: { type: 'dashed', opacity: 0.3 } }
      },
      series: [
        {
          type: 'scatter',
          symbolSize: 6,
          data: processedData,
          markLine: {
            silent: true,
            symbol: 'none',
            lineStyle: { color: '#ff4d4f', type: 'dashed', width: 2 },
            data: [{ yAxis: thresholdLine, name: 'Significance Threshold' }],
            label: { formatter: `P = ${threshold}`, position: 'end' }
          },
          label: {
            show: showLabels,
            formatter: (params: any) => params.data.data.snpId,
            position: 'top',
            fontSize: 10
          }
        }
      ],
      dataZoom: [
        { type: 'inside', xAxisIndex: 0, start: 0, end: zoom },
        { type: 'slider', xAxisIndex: 0, start: 0, end: zoom, height: 20 }
      ]
    };

    chartInstance.current.setOption(option);

    chartInstance.current.on('click', (params: any) => {
      if (params.data?.data && onPointClick) {
        onPointClick(params.data.data);
      }
    });
  }, [data, threshold, showLabels, zoom, title, onPointClick]);

  const handleExport = () => {
    if (!chartInstance.current) return;
    const url = chartInstance.current.getDataURL({ type: 'png', pixelRatio: 2 });
    const a = document.createElement('a');
    a.href = url;
    a.download = 'manhattan_plot.png';
    a.click();
  };

  if (loading) {
    return (
      <Card className="chart-card">
        <div className="chart-loading">
          <Spin size="large" tip="加载数据中..." />
        </div>
      </Card>
    );
  }

  if (!data.length) {
    return (
      <Card className="chart-card">
        <Empty description="暂无GWAS数据" />
      </Card>
    );
  }

  return (
    <Card 
      className="chart-card manhattan-chart"
      title={
        <Space>
          <Title level={5} style={{ margin: 0 }}>曼哈顿图</Title>
          <Text type="secondary">GWAS分析结果可视化</Text>
        </Space>
      }
      extra={
        <Space>
          <Tooltip title="显示标签">
            <Switch 
              checkedChildren="标签" 
              unCheckedChildren="标签" 
              checked={showLabels}
              onChange={setShowLabels}
            />
          </Tooltip>
          <Tooltip title="缩放">
            <Slider 
              style={{ width: 100 }} 
              min={10} 
              max={100} 
              value={zoom}
              onChange={setZoom}
            />
          </Tooltip>
          <Button icon={<DownloadOutlined />} onClick={handleExport}>
            导出图片
          </Button>
        </Space>
      }
    >
      <div ref={chartRef} className="chart-container" style={{ height: 400 }} />
    </Card>
  );
};

// 遗传趋势图组件
interface GeneticTrendData {
  year: number;
  ebv: number;
  accuracy: number;
  traitName: string;
}

interface GeneticTrendChartProps {
  data: GeneticTrendData[];
  traits?: string[];
  title?: string;
  loading?: boolean;
}

export const GeneticTrendChart: React.FC<GeneticTrendChartProps> = ({
  data,
  traits = [],
  title = '遗传趋势图 Genetic Trend',
  loading = false
}) => {
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<echarts.ECharts | null>(null);
  const [selectedTrait, setSelectedTrait] = useState<string>(traits[0] || '');

  useEffect(() => {
    if (!chartRef.current) return;

    chartInstance.current = echarts.init(chartRef.current);
    window.addEventListener('resize', () => chartInstance.current?.resize());

    return () => chartInstance.current?.dispose();
  }, []);

  useEffect(() => {
    if (!chartInstance.current || !data.length) return;

    const filteredData = selectedTrait 
      ? data.filter(d => d.traitName === selectedTrait)
      : data;

    const years = [...new Set(filteredData.map(d => d.year))].sort();
    const ebvValues = years.map(year => {
      const yearData = filteredData.filter(d => d.year === year);
      return yearData.length ? yearData.reduce((sum, d) => sum + d.ebv, 0) / yearData.length : 0;
    });
    const accuracyValues = years.map(year => {
      const yearData = filteredData.filter(d => d.year === year);
      return yearData.length ? yearData.reduce((sum, d) => sum + d.accuracy, 0) / yearData.length * 100 : 0;
    });

    const option: echarts.EChartsOption = {
      title: {
        text: title,
        subtext: selectedTrait ? `性状: ${selectedTrait}` : '所有性状',
        left: 'center'
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'cross' }
      },
      legend: {
        data: ['育种值 EBV', '准确性 Accuracy'],
        bottom: 0
      },
      grid: { left: '10%', right: '10%', bottom: '15%', top: '20%' },
      xAxis: {
        type: 'category',
        name: '年份 Year',
        data: years,
        axisLabel: { rotate: 45 }
      },
      yAxis: [
        {
          type: 'value',
          name: '育种值 EBV',
          position: 'left',
          splitLine: { lineStyle: { type: 'dashed' } }
        },
        {
          type: 'value',
          name: '准确性 (%)',
          position: 'right',
          min: 0,
          max: 100,
          splitLine: { show: false }
        }
      ],
      series: [
        {
          name: '育种值 EBV',
          type: 'line',
          data: ebvValues,
          smooth: true,
          symbol: 'circle',
          symbolSize: 8,
          lineStyle: { width: 3 },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(24, 144, 255, 0.3)' },
              { offset: 1, color: 'rgba(24, 144, 255, 0.05)' }
            ])
          },
          itemStyle: { color: '#1890ff' }
        },
        {
          name: '准确性 Accuracy',
          type: 'bar',
          yAxisIndex: 1,
          data: accuracyValues,
          barWidth: '40%',
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: '#52c41a' },
              { offset: 1, color: '#95de64' }
            ])
          }
        }
      ]
    };

    chartInstance.current.setOption(option);
  }, [data, selectedTrait, title]);

  if (loading) {
    return (
      <Card className="chart-card">
        <div className="chart-loading">
          <Spin size="large" tip="加载数据中..." />
        </div>
      </Card>
    );
  }

  return (
    <Card 
      className="chart-card"
      title="遗传趋势分析"
      extra={
        traits.length > 0 && (
          <Select
            value={selectedTrait}
            onChange={setSelectedTrait}
            style={{ width: 150 }}
            placeholder="选择性状"
          >
            <Select.Option value="">所有性状</Select.Option>
            {traits.map(trait => (
              <Select.Option key={trait} value={trait}>{trait}</Select.Option>
            ))}
          </Select>
        )
      }
    >
      <div ref={chartRef} className="chart-container" style={{ height: 400 }} />
    </Card>
  );
};

export default { ManhattanPlot, GeneticTrendChart };
