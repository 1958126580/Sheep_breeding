import React, { useState, useCallback } from 'react';
import { 
  Card, Upload, Button, Table, Progress, message, Modal, 
  Select, Radio, Space, Typography, Alert, Tabs, Tag,
  Checkbox, Descriptions, Spin
} from 'antd';
import { 
  UploadOutlined, DownloadOutlined, FileExcelOutlined, 
  FileTextOutlined, CheckCircleOutlined, CloseCircleOutlined,
  InfoCircleOutlined
} from '@ant-design/icons';
import type { UploadFile, UploadProps } from 'antd/es/upload/interface';
import { useTranslation } from 'react-i18next';
import apiClient from '../api/client';
import './DataIO.scss';

const { Title, Text, Paragraph } = Typography;
const { Dragger } = Upload;
const { TabPane } = Tabs;

interface ImportResult {
  success: number;
  failed: number;
  errors: { row: number; error: string }[];
}

interface DataIOProps {
  entityType: 'farms' | 'animals' | 'phenotypes' | 'genotypes';
  onImportComplete?: (result: ImportResult) => void;
}

export const DataImportExport: React.FC<DataIOProps> = ({ 
  entityType, 
  onImportComplete 
}) => {
  const { t } = useTranslation();
  const [fileList, setFileList] = useState<UploadFile[]>([]);
  const [importing, setImporting] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [progress, setProgress] = useState(0);
  const [importResult, setImportResult] = useState<ImportResult | null>(null);
  const [previewData, setPreviewData] = useState<any[]>([]);
  const [selectedColumns, setSelectedColumns] = useState<string[]>([]);
  const [exportFormat, setExportFormat] = useState<'xlsx' | 'csv'>('xlsx');

  // 实体类型配置
  const entityConfig = {
    farms: {
      name: '羊场',
      requiredColumns: ['code', 'name', 'farm_type', 'capacity'],
      templateUrl: '/templates/farms_template.xlsx',
    },
    animals: {
      name: '种羊',
      requiredColumns: ['animal_id', 'farm_id', 'birth_date', 'gender'],
      templateUrl: '/templates/animals_template.xlsx',
    },
    phenotypes: {
      name: '表型数据',
      requiredColumns: ['animal_id', 'trait_code', 'value', 'measure_date'],
      templateUrl: '/templates/phenotypes_template.xlsx',
    },
    genotypes: {
      name: '基因型数据',
      requiredColumns: ['animal_id', 'snp_id', 'genotype'],
      templateUrl: '/templates/genotypes_template.xlsx',
    },
  };

  const config = entityConfig[entityType];

  // 文件上传前的检查
  const beforeUpload = (file: File) => {
    const isValidType = file.name.endsWith('.xlsx') || file.name.endsWith('.csv');
    if (!isValidType) {
      message.error('只支持 Excel (.xlsx) 或 CSV (.csv) 格式！');
      return false;
    }
    const isLt10M = file.size / 1024 / 1024 < 10;
    if (!isLt10M) {
      message.error('文件大小不能超过 10MB！');
      return false;
    }
    return true;
  };

  // 处理文件上传
  const handleUpload: UploadProps['onChange'] = async (info) => {
    setFileList(info.fileList);
    
    if (info.file.status === 'done') {
      // 预览文件内容
      try {
        const formData = new FormData();
        formData.append('file', info.file.originFileObj!);
        const response: any = await apiClient.post(`/api/v1/import/preview/${entityType}`, formData);
        setPreviewData(response.data || []);
        setSelectedColumns(config.requiredColumns);
      } catch (error) {
        message.error('文件解析失败');
      }
    }
  };

  // 执行导入
  const handleImport = async () => {
    if (!fileList.length) {
      message.warn('请先选择要导入的文件');
      return;
    }

    setImporting(true);
    setProgress(0);

    try {
      const formData = new FormData();
      formData.append('file', fileList[0].originFileObj!);
      formData.append('columns', JSON.stringify(selectedColumns));

      // 模拟进度
      const progressInterval = setInterval(() => {
        setProgress(prev => Math.min(prev + 10, 90));
      }, 500);

      const response: any = await apiClient.post(`/api/v1/import/${entityType}`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      clearInterval(progressInterval);
      setProgress(100);

      const result: ImportResult = response.data || { success: previewData.length, failed: 0, errors: [] };
      setImportResult(result);
      onImportComplete?.(result);
      message.success(`成功导入 ${result.success} 条记录`);
    } catch (error: any) {
      message.error(`导入失败: ${error.message}`);
    } finally {
      setImporting(false);
    }
  };

  // 执行导出
  const handleExport = async () => {
    setExporting(true);

    try {
      const response = await apiClient.get(`/api/v1/export/${entityType}`, {
        params: { format: exportFormat },
        responseType: 'blob',
      });

      // 创建下载链接
      const url = window.URL.createObjectURL(new Blob([response as any]));
      const link = document.createElement('a');
      link.href = url;
      link.download = `${entityType}_export_${new Date().toISOString().split('T')[0]}.${exportFormat}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      message.success('导出成功');
    } catch (error: any) {
      message.error(`导出失败: ${error.message}`);
    } finally {
      setExporting(false);
    }
  };

  // 下载模板
  const handleDownloadTemplate = () => {
    window.open(config.templateUrl, '_blank');
  };

  return (
    <Card className="data-io-card">
      <Tabs defaultActiveKey="import">
        <TabPane 
          tab={<span><UploadOutlined /> 数据导入</span>} 
          key="import"
        >
          <Space direction="vertical" style={{ width: '100%' }} size="large">
            {/* 导入说明 */}
            <Alert
              type="info"
              showIcon
              icon={<InfoCircleOutlined />}
              message="导入说明"
              description={
                <div>
                  <p>支持导入 {config.name} 数据</p>
                  <p>必填字段: {config.requiredColumns.join(', ')}</p>
                  <Button 
                    type="link" 
                    icon={<DownloadOutlined />}
                    onClick={handleDownloadTemplate}
                  >
                    下载导入模板
                  </Button>
                </div>
              }
            />

            {/* 文件上传区 */}
            <Dragger
              accept=".xlsx,.csv"
              maxCount={1}
              fileList={fileList}
              beforeUpload={beforeUpload}
              onChange={handleUpload}
              customRequest={({ onSuccess }) => {
                setTimeout(() => onSuccess?.("ok"), 0);
              }}
            >
              <p className="ant-upload-drag-icon">
                <FileExcelOutlined style={{ color: '#52c41a', fontSize: 48 }} />
              </p>
              <p className="ant-upload-text">将文件拖到此处，或点击上传</p>
              <p className="ant-upload-hint">支持 Excel (.xlsx) 或 CSV (.csv) 格式，单个文件不超过10MB</p>
            </Dragger>

            {/* 预览数据 */}
            {previewData.length > 0 && (
              <Card title="数据预览" size="small">
                <Table
                  dataSource={previewData.slice(0, 5)}
                  columns={Object.keys(previewData[0] || {}).map(key => ({
                    title: key,
                    dataIndex: key,
                    key,
                    ellipsis: true,
                  }))}
                  pagination={false}
                  size="small"
                  scroll={{ x: true }}
                  footer={() => <Text type="secondary">显示前5条，共 {previewData.length} 条记录</Text>}
                />
              </Card>
            )}

            {/* 导入进度 */}
            {importing && (
              <Card size="small">
                <Progress percent={progress} status="active" />
                <Text type="secondary">正在导入数据...</Text>
              </Card>
            )}

            {/* 导入结果 */}
            {importResult && (
              <Alert
                type={importResult.failed > 0 ? 'warning' : 'success'}
                showIcon
                message="导入完成"
                description={
                  <Descriptions column={2} size="small">
                    <Descriptions.Item label="成功">
                      <Tag color="success">{importResult.success}</Tag>
                    </Descriptions.Item>
                    <Descriptions.Item label="失败">
                      <Tag color={importResult.failed > 0 ? 'error' : 'default'}>{importResult.failed}</Tag>
                    </Descriptions.Item>
                  </Descriptions>
                }
              />
            )}

            <Button 
              type="primary" 
              icon={<UploadOutlined />} 
              loading={importing}
              disabled={!fileList.length}
              onClick={handleImport}
              size="large"
              block
            >
              开始导入
            </Button>
          </Space>
        </TabPane>

        <TabPane 
          tab={<span><DownloadOutlined /> 数据导出</span>} 
          key="export"
        >
          <Space direction="vertical" style={{ width: '100%' }} size="large">
            <Alert
              type="info"
              showIcon
              message="导出说明"
              description={`导出当前系统中的所有${config.name}数据`}
            />

            <Card size="small" title="导出选项">
              <Space direction="vertical">
                <div>
                  <Text strong>选择格式:</Text>
                  <Radio.Group 
                    value={exportFormat} 
                    onChange={e => setExportFormat(e.target.value)}
                    style={{ marginLeft: 16 }}
                  >
                    <Radio.Button value="xlsx">
                      <FileExcelOutlined /> Excel
                    </Radio.Button>
                    <Radio.Button value="csv">
                      <FileTextOutlined /> CSV
                    </Radio.Button>
                  </Radio.Group>
                </div>
              </Space>
            </Card>

            <Button 
              type="primary" 
              icon={<DownloadOutlined />} 
              loading={exporting}
              onClick={handleExport}
              size="large"
              block
            >
              导出数据
            </Button>
          </Space>
        </TabPane>
      </Tabs>
    </Card>
  );
};

export default DataImportExport;
