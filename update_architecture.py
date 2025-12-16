#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Replace simple architecture diagram with comprehensive one"""

# Read the file
with open('README.md', 'r', encoding='utf-8') as f:
    content = f.read()

# Define the new comprehensive diagram
new_diagram = '''```mermaid
graph TB
    subgraph clients["🖥️ 客户端层 Client Layer"]
        web["Web前端<br/>React + TypeScript<br/>状态管理: Redux"]
        mobile["移动端<br/>React Native<br/>iOS + Android"]
        admin["管理后台<br/>Ant Design Pro<br/>数据可视化"]
    end
    
    subgraph gateway["🌐 API网关层 API Gateway Layer"]
        nginx["Nginx<br/>负载均衡 + 反向代理"]
        auth["认证中心<br/>JWT + OAuth2.0"]
        ratelimit["限流控制<br/>Redis + Lua"]
        router["智能路由<br/>服务发现"]
    end
    
    subgraph microservices["⚙️ 微服务层 Microservices Layer"]
        direction TB
        
        subgraph core["核心业务服务"]
            user["用户服务<br/>User Service"]
            animal["种羊服务<br/>Animal Service"]
            pedigree["系谱服务<br/>Pedigree Service"]
        end
        
        subgraph data["数据管理服务"]
            phenotype["表型服务<br/>Phenotype Service"]
            genotype["基因组服务<br/>Genomic Service"]
            health["健康服务<br/>Health Service"]
        end
        
        subgraph breeding["育种分析服务"]
            ebv["育种值服务<br/>EBV Service"]
            selection["选种服务<br/>Selection Service"]
            mating["选配服务<br/>Mating Service"]
        end
        
        subgraph support["支撑服务"]
            iot["物联网服务<br/>IoT Service"]
            report["报表服务<br/>Report Service"]
            viz["可视化服务<br/>Visualization"]
            cloud["云服务<br/>Cloud Service"]
        end
    end
    
    subgraph compute["🔬 计算层 Computation Layer"]
        direction LR
        julia["Julia计算引擎<br/>高性能数值计算"]
        
        subgraph algorithms["核心算法"]
            blup["BLUP<br/>最佳线性无偏预测"]
            gblup["GBLUP<br/>基因组BLUP"]
            ssblup["ssGBLUP<br/>单步法GBLUP"]
            bayes["贝叶斯方法<br/>BayesA/B/C"]
        end
        
        subgraph advanced["高级分析"]
            gwas["GWAS<br/>全基因组关联分析"]
            gs["基因组选择<br/>Genomic Selection"]
            ocs["最优贡献选择<br/>OCS"]
        end
        
        subgraph performance["性能优化"]
            parallel["并行计算<br/>多线程/多进程"]
            gpu["GPU加速<br/>CUDA/OpenCL"]
            sparse["稀疏矩阵<br/>优化算法"]
        end
    end
    
    subgraph data_layer["💾 数据层 Data Layer"]
        direction TB
        
        subgraph databases["数据库集群"]
            postgres["PostgreSQL<br/>主数据库<br/>关系型数据"]
            timescale["TimescaleDB<br/>时序数据<br/>IoT传感器数据"]
            mongo["MongoDB<br/>文档数据库<br/>非结构化数据"]
        end
        
        subgraph storage["存储系统"]
            minio["MinIO<br/>对象存储<br/>文件/图片/视频"]
            redis["Redis<br/>缓存系统<br/>会话/热数据"]
        end
        
        subgraph messaging["消息队列"]
            rabbitmq["RabbitMQ<br/>消息中间件<br/>异步任务"]
            kafka["Kafka<br/>流式处理<br/>实时数据"]
        end
    end
    
    subgraph infrastructure["🏗️ 基础设施层 Infrastructure Layer"]
        direction LR
        
        subgraph monitoring["监控告警"]
            prometheus["Prometheus<br/>指标监控"]
            grafana["Grafana<br/>可视化面板"]
            elk["ELK Stack<br/>日志分析"]
        end
        
        subgraph deployment["部署运维"]
            docker["Docker<br/>容器化"]
            k8s["Kubernetes<br/>容器编排"]
            ci["CI/CD<br/>持续集成/部署"]
        end
        
        subgraph security["安全防护"]
            firewall["防火墙<br/>网络安全"]
            backup["备份系统<br/>数据备份"]
            encrypt["加密系统<br/>数据加密"]
        end
    end
    
    clients -->|HTTPS| gateway
    gateway --> microservices
    microservices --> compute
    compute --> data_layer
    data_layer -.-> infrastructure
    infrastructure -.-> monitoring
```'''

# Find and replace the diagram section
import re

# Pattern to match the mermaid diagram
pattern = r'```mermaid\s*flowchart TD.*?```'

# Replace with new diagram
content = re.sub(pattern, new_diagram, content, flags=re.DOTALL)

# Write back
with open('README.md', 'w', encoding='utf-8', newline='\r\n') as f:
    f.write(content)

print("Architecture diagram updated successfully!")
