import React from 'react';
import { Spin, Result, Button } from 'antd';
import { LoadingOutlined, ReloadOutlined } from '@ant-design/icons';
import './Loading.scss';

// Modern loading spinner
export const LoadingSpinner: React.FC<{ tip?: string; size?: 'small' | 'default' | 'large' }> = ({ 
  tip = '加载中...', 
  size = 'default' 
}) => {
  const iconSize = size === 'small' ? 24 : size === 'large' ? 48 : 36;
  
  return (
    <div className="loading-container">
      <Spin 
        indicator={<LoadingOutlined style={{ fontSize: iconSize }} spin />} 
        tip={tip}
        size={size}
      />
    </div>
  );
};

// Page loading overlay
export const PageLoading: React.FC = () => (
  <div className="page-loading">
    <div className="loading-content">
      <div className="pulse-ring"></div>
      <div className="pulse-ring delay-1"></div>
      <div className="pulse-ring delay-2"></div>
      <LoadingOutlined className="loading-icon" />
      <p>正在加载页面...</p>
    </div>
  </div>
);

// Skeleton loading for cards
export const CardSkeleton: React.FC<{ count?: number }> = ({ count = 4 }) => (
  <div className="card-skeleton-container">
    {Array.from({ length: count }).map((_, index) => (
      <div key={index} className="card-skeleton">
        <div className="skeleton-header shimmer"></div>
        <div className="skeleton-body">
          <div className="skeleton-line shimmer"></div>
          <div className="skeleton-line short shimmer"></div>
        </div>
      </div>
    ))}
  </div>
);

// Error boundary fallback
export const ErrorFallback: React.FC<{ 
  error?: Error; 
  resetErrorBoundary?: () => void 
}> = ({ error, resetErrorBoundary }) => (
  <Result
    status="error"
    title="出错了"
    subTitle={error?.message || "页面加载失败，请重试"}
    extra={
      <Button 
        type="primary" 
        icon={<ReloadOutlined />} 
        onClick={resetErrorBoundary}
      >
        重新加载
      </Button>
    }
  />
);

// Empty state
export const EmptyState: React.FC<{ 
  description?: string;
  action?: React.ReactNode;
}> = ({ description = '暂无数据', action }) => (
  <Result
    status="info"
    title="暂无数据"
    subTitle={description}
    extra={action}
  />
);

export default LoadingSpinner;
