import React, { useState, useEffect } from 'react';
import {
  Card, Table, Button, Modal, Form, Input, Select, Space, 
  Tag, Typography, Tree, Checkbox, Tabs, message, Popconfirm,
  Tooltip, Badge, Drawer, Transfer, Switch, Divider
} from 'antd';
import {
  PlusOutlined, EditOutlined, DeleteOutlined, SafetyOutlined,
  UserOutlined, TeamOutlined, LockOutlined, KeyOutlined,
  CheckCircleOutlined, CloseCircleOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import type { DataNode } from 'antd/es/tree';
import { useTranslation } from 'react-i18next';
import apiClient from '../api/client';
import './RBAC.scss';

const { Title, Text } = Typography;
const { TabPane } = Tabs;

// 权限类型定义
interface Permission {
  id: number;
  code: string;
  name: string;
  description: string;
  module: string;
  type: 'menu' | 'button' | 'api';
}

interface Role {
  id: number;
  code: string;
  name: string;
  description: string;
  permissions: number[];
  userCount: number;
  isSystem: boolean;
  createdAt: string;
}

interface User {
  id: number;
  username: string;
  email: string;
  roles: number[];
  isActive: boolean;
  lastLogin: string;
}

// 预定义的权限模块
const PERMISSION_MODULES = [
  { key: 'farm', label: '羊场管理', icon: '🏠' },
  { key: 'animal', label: '种羊管理', icon: '🐑' },
  { key: 'breeding', label: '育种分析', icon: '🧬' },
  { key: 'health', label: '健康管理', icon: '💊' },
  { key: 'report', label: '报表管理', icon: '📊' },
  { key: 'system', label: '系统管理', icon: '⚙️' },
];

// 预定义的权限操作
const PERMISSION_ACTIONS = [
  { key: 'view', label: '查看' },
  { key: 'create', label: '创建' },
  { key: 'update', label: '编辑' },
  { key: 'delete', label: '删除' },
  { key: 'export', label: '导出' },
  { key: 'import', label: '导入' },
];

export const RBACManager: React.FC = () => {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState('roles');
  const [roles, setRoles] = useState<Role[]>([]);
  const [permissions, setPermissions] = useState<Permission[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(false);
  
  // Modal states
  const [roleModalVisible, setRoleModalVisible] = useState(false);
  const [permissionDrawerVisible, setPermissionDrawerVisible] = useState(false);
  const [editingRole, setEditingRole] = useState<Role | null>(null);
  const [selectedPermissions, setSelectedPermissions] = useState<number[]>([]);
  
  const [form] = Form.useForm();

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      // 模拟加载数据
      setRoles([
        { id: 1, code: 'admin', name: '系统管理员', description: '拥有所有权限', permissions: [1,2,3,4,5,6,7,8], userCount: 2, isSystem: true, createdAt: '2024-01-01' },
        { id: 2, code: 'manager', name: '场长', description: '管理羊场和种羊', permissions: [1,2,3,4], userCount: 5, isSystem: false, createdAt: '2024-01-15' },
        { id: 3, code: 'breeder', name: '育种员', description: '负责育种分析', permissions: [1,3,5,6], userCount: 8, isSystem: false, createdAt: '2024-02-01' },
        { id: 4, code: 'viewer', name: '访客', description: '只读权限', permissions: [1], userCount: 15, isSystem: true, createdAt: '2024-01-01' },
      ]);
      
      setPermissions([
        { id: 1, code: 'farm:view', name: '查看羊场', description: '查看羊场信息', module: 'farm', type: 'menu' },
        { id: 2, code: 'farm:manage', name: '管理羊场', description: '创建、编辑、删除羊场', module: 'farm', type: 'button' },
        { id: 3, code: 'animal:view', name: '查看种羊', description: '查看种羊信息', module: 'animal', type: 'menu' },
        { id: 4, code: 'animal:manage', name: '管理种羊', description: '创建、编辑、删除种羊', module: 'animal', type: 'button' },
        { id: 5, code: 'breeding:view', name: '查看育种分析', description: '查看育种值和分析结果', module: 'breeding', type: 'menu' },
        { id: 6, code: 'breeding:run', name: '运行育种分析', description: '执行育种值估计', module: 'breeding', type: 'button' },
        { id: 7, code: 'report:view', name: '查看报表', description: '查看系统报表', module: 'report', type: 'menu' },
        { id: 8, code: 'system:manage', name: '系统管理', description: '系统配置和用户管理', module: 'system', type: 'menu' },
      ]);
    } catch (error) {
      message.error('加载数据失败');
    } finally {
      setLoading(false);
    }
  };

  // 角色表格列
  const roleColumns: ColumnsType<Role> = [
    {
      title: '角色名称',
      dataIndex: 'name',
      key: 'name',
      render: (name, record) => (
        <Space>
          <Tag color={record.isSystem ? 'gold' : 'blue'}>
            <TeamOutlined /> {name}
          </Tag>
          {record.isSystem && <Tag color="orange">系统</Tag>}
        </Space>
      ),
    },
    {
      title: '角色代码',
      dataIndex: 'code',
      key: 'code',
      render: code => <Text code>{code}</Text>,
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
    },
    {
      title: '用户数',
      dataIndex: 'userCount',
      key: 'userCount',
      render: count => <Badge count={count} showZero color="#1890ff" />,
    },
    {
      title: '权限数',
      key: 'permissions',
      render: (_, record) => (
        <Tag color="green">{record.permissions.length} 项</Tag>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 200,
      render: (_, record) => (
        <Space>
          <Tooltip title="编辑角色">
            <Button 
              type="text" 
              icon={<EditOutlined />}
              onClick={() => handleEditRole(record)}
              disabled={record.isSystem}
            />
          </Tooltip>
          <Tooltip title="配置权限">
            <Button 
              type="text" 
              icon={<KeyOutlined />}
              onClick={() => handleConfigPermissions(record)}
            />
          </Tooltip>
          <Popconfirm
            title="确定删除此角色吗？"
            onConfirm={() => handleDeleteRole(record.id)}
            disabled={record.isSystem}
          >
            <Button 
              type="text" 
              danger 
              icon={<DeleteOutlined />}
              disabled={record.isSystem}
            />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  // 权限表格列
  const permissionColumns: ColumnsType<Permission> = [
    {
      title: '权限名称',
      dataIndex: 'name',
      key: 'name',
      render: name => <Text strong>{name}</Text>,
    },
    {
      title: '权限代码',
      dataIndex: 'code',
      key: 'code',
      render: code => <Text code>{code}</Text>,
    },
    {
      title: '所属模块',
      dataIndex: 'module',
      key: 'module',
      render: module => {
        const mod = PERMISSION_MODULES.find(m => m.key === module);
        return <Tag>{mod?.icon} {mod?.label || module}</Tag>;
      },
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      render: type => {
        const typeConfig = {
          menu: { color: 'blue', text: '菜单' },
          button: { color: 'green', text: '按钮' },
          api: { color: 'purple', text: 'API' },
        };
        const cfg = typeConfig[type as keyof typeof typeConfig];
        return <Tag color={cfg?.color}>{cfg?.text}</Tag>;
      },
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
    },
  ];

  // 处理函数
  const handleAddRole = () => {
    setEditingRole(null);
    form.resetFields();
    setRoleModalVisible(true);
  };

  const handleEditRole = (role: Role) => {
    setEditingRole(role);
    form.setFieldsValue(role);
    setRoleModalVisible(true);
  };

  const handleDeleteRole = async (id: number) => {
    try {
      // await apiClient.delete(`/api/v1/roles/${id}`);
      setRoles(roles.filter(r => r.id !== id));
      message.success('删除成功');
    } catch (error) {
      message.error('删除失败');
    }
  };

  const handleConfigPermissions = (role: Role) => {
    setEditingRole(role);
    setSelectedPermissions(role.permissions);
    setPermissionDrawerVisible(true);
  };

  const handleSaveRole = async () => {
    try {
      const values = await form.validateFields();
      if (editingRole) {
        setRoles(roles.map(r => r.id === editingRole.id ? { ...r, ...values } : r));
        message.success('更新成功');
      } else {
        const newRole: Role = {
          id: Date.now(),
          ...values,
          permissions: [],
          userCount: 0,
          isSystem: false,
          createdAt: new Date().toISOString().split('T')[0],
        };
        setRoles([...roles, newRole]);
        message.success('创建成功');
      }
      setRoleModalVisible(false);
    } catch (error) {
      // validation error
    }
  };

  const handleSavePermissions = () => {
    if (editingRole) {
      setRoles(roles.map(r => 
        r.id === editingRole.id ? { ...r, permissions: selectedPermissions } : r
      ));
      message.success('权限配置已保存');
    }
    setPermissionDrawerVisible(false);
  };

  // 构建权限树
  const buildPermissionTree = (): DataNode[] => {
    const tree: DataNode[] = [];
    
    PERMISSION_MODULES.forEach(mod => {
      const modulePerms = permissions.filter(p => p.module === mod.key);
      if (modulePerms.length > 0) {
        tree.push({
          title: `${mod.icon} ${mod.label}`,
          key: `module:${mod.key}`,
          children: modulePerms.map(p => ({
            title: (
              <Space>
                <span>{p.name}</span>
                <Text type="secondary" style={{ fontSize: 12 }}>({p.code})</Text>
              </Space>
            ),
            key: p.id.toString(),
          })),
        });
      }
    });
    
    return tree;
  };

  return (
    <div className="rbac-manager">
      <Card>
        <div className="page-header">
          <div>
            <Title level={3}>
              <SafetyOutlined /> 权限管理
            </Title>
            <Text type="secondary">基于角色的访问控制 (RBAC)</Text>
          </div>
        </div>

        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          <TabPane 
            tab={<span><TeamOutlined /> 角色管理</span>} 
            key="roles"
          >
            <div className="table-toolbar">
              <Button 
                type="primary" 
                icon={<PlusOutlined />}
                onClick={handleAddRole}
              >
                新建角色
              </Button>
            </div>
            <Table
              columns={roleColumns}
              dataSource={roles}
              rowKey="id"
              loading={loading}
              pagination={false}
            />
          </TabPane>

          <TabPane 
            tab={<span><KeyOutlined /> 权限列表</span>} 
            key="permissions"
          >
            <Table
              columns={permissionColumns}
              dataSource={permissions}
              rowKey="id"
              loading={loading}
              pagination={false}
            />
          </TabPane>
        </Tabs>
      </Card>

      {/* 角色编辑弹窗 */}
      <Modal
        title={editingRole ? '编辑角色' : '新建角色'}
        open={roleModalVisible}
        onOk={handleSaveRole}
        onCancel={() => setRoleModalVisible(false)}
        okText="保存"
        cancelText="取消"
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="code"
            label="角色代码"
            rules={[{ required: true, message: '请输入角色代码' }]}
          >
            <Input placeholder="如: manager" disabled={!!editingRole} />
          </Form.Item>
          <Form.Item
            name="name"
            label="角色名称"
            rules={[{ required: true, message: '请输入角色名称' }]}
          >
            <Input placeholder="如: 场长" />
          </Form.Item>
          <Form.Item
            name="description"
            label="角色描述"
          >
            <Input.TextArea rows={3} placeholder="描述角色的职责和权限范围" />
          </Form.Item>
        </Form>
      </Modal>

      {/* 权限配置抽屉 */}
      <Drawer
        title={`配置权限 - ${editingRole?.name || ''}`}
        placement="right"
        width={500}
        open={permissionDrawerVisible}
        onClose={() => setPermissionDrawerVisible(false)}
        footer={
          <Space style={{ float: 'right' }}>
            <Button onClick={() => setPermissionDrawerVisible(false)}>取消</Button>
            <Button type="primary" onClick={handleSavePermissions}>保存</Button>
          </Space>
        }
      >
        <Tree
          checkable
          defaultExpandAll
          treeData={buildPermissionTree()}
          checkedKeys={selectedPermissions.map(String)}
          onCheck={(checked) => {
            const keys = (checked as string[]).filter(k => !k.startsWith('module:'));
            setSelectedPermissions(keys.map(Number));
          }}
        />
      </Drawer>
    </div>
  );
};

export default RBACManager;
