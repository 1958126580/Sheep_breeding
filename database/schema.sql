-- ============================================================================
-- 新星肉羊育种系统数据库Schema
-- NovaBreed Sheep System Database Schema
-- 
-- 数据库: PostgreSQL 14+
-- 编码: UTF-8
-- 作者: AdvancedGenomics Team
-- 版本: 1.0.0
-- ============================================================================

-- 启用必要的扩展
-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";      -- UUID生成
CREATE EXTENSION IF NOT EXISTS "pgcrypto";       -- 加密功能
CREATE EXTENSION IF NOT EXISTS "pg_trgm";        -- 文本搜索
CREATE EXTENSION IF NOT EXISTS "btree_gin";      -- GIN索引支持

-- ============================================================================
-- 用户与权限模块
-- User and Permission Module
-- ============================================================================

-- 机构表
-- Organizations table
CREATE TABLE organizations (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,                    -- 机构代码
    name_zh VARCHAR(200) NOT NULL,                       -- 机构名称（中文）
    name_en VARCHAR(200),                                -- 机构名称（英文）
    type VARCHAR(50) NOT NULL,                           -- 机构类型: research/farm/company
    country VARCHAR(100),                                -- 国家
    province VARCHAR(100),                               -- 省份
    city VARCHAR(100),                                   -- 城市
    address TEXT,                                        -- 详细地址
    contact_person VARCHAR(100),                         -- 联系人
    contact_phone VARCHAR(50),                           -- 联系电话
    contact_email VARCHAR(200),                          -- 联系邮箱
    status VARCHAR(20) DEFAULT 'active',                 -- 状态: active/inactive/suspended
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB                                       -- 额外元数据
);

-- 用户表
-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,               -- 用户名
    email VARCHAR(200) UNIQUE NOT NULL,                  -- 邮箱
    password_hash VARCHAR(255) NOT NULL,                 -- 密码哈希
    full_name VARCHAR(200) NOT NULL,                     -- 全名
    phone VARCHAR(50),                                   -- 电话
    language VARCHAR(10) DEFAULT 'zh-CN',                -- 首选语言: zh-CN/en-US
    status VARCHAR(20) DEFAULT 'active',                 -- 状态: active/inactive/locked
    last_login_at TIMESTAMP,                             -- 最后登录时间
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- 角色表
-- Roles table
CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,                   -- 角色名称
    description_zh TEXT,                                 -- 角色描述（中文）
    description_en TEXT,                                 -- 角色描述（英文）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 权限表
-- Permissions table
CREATE TABLE permissions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,                   -- 权限名称
    resource VARCHAR(100) NOT NULL,                      -- 资源类型
    action VARCHAR(50) NOT NULL,                         -- 操作: create/read/update/delete
    description_zh TEXT,
    description_en TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 角色权限关联表
-- Role-Permission mapping table
CREATE TABLE role_permissions (
    role_id INTEGER REFERENCES roles(id) ON DELETE CASCADE,
    permission_id INTEGER REFERENCES permissions(id) ON DELETE CASCADE,
    PRIMARY KEY (role_id, permission_id)
);

-- 用户角色关联表
-- User-Role mapping table
CREATE TABLE user_roles (
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    role_id INTEGER REFERENCES roles(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, role_id)
);

-- 用户机构关联表
-- User-Organization mapping table
CREATE TABLE user_organizations (
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    organization_id INTEGER REFERENCES organizations(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL,                           -- 在该机构的角色: admin/manager/member
    is_primary BOOLEAN DEFAULT FALSE,                    -- 是否为主要机构
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, organization_id)
);

-- ============================================================================
-- 种羊管理模块
-- Animal Management Module
-- ============================================================================

-- 品种表
-- Breeds table
CREATE TABLE breeds (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,                    -- 品种代码
    name_zh VARCHAR(100) NOT NULL,                       -- 品种名称（中文）
    name_en VARCHAR(100),                                -- 品种名称（英文）
    description_zh TEXT,
    description_en TEXT,
    origin_country VARCHAR(100),                         -- 原产国
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 动物表
-- Animals table
CREATE TABLE animals (
    id SERIAL PRIMARY KEY,
    animal_id VARCHAR(100) UNIQUE NOT NULL,              -- 动物唯一标识
    organization_id INTEGER REFERENCES organizations(id),
    breed_id INTEGER REFERENCES breeds(id),
    name VARCHAR(200),                                   -- 动物名称
    sex VARCHAR(10) NOT NULL,                            -- 性别: male/female
    birth_date DATE,                                     -- 出生日期
    birth_weight DECIMAL(8,2),                           -- 出生重(kg)
    birth_type VARCHAR(20),                              -- 出生类型: single/twin/triplet
    coat_color VARCHAR(50),                              -- 毛色
    ear_tag VARCHAR(100),                                -- 耳标号
    electronic_id VARCHAR(100),                          -- 电子标识
    status VARCHAR(20) DEFAULT 'alive',                  -- 状态: alive/dead/sold/culled
    death_date DATE,                                     -- 死亡日期
    death_reason TEXT,                                   -- 死亡原因
    location VARCHAR(200),                               -- 当前位置
    owner VARCHAR(200),                                  -- 所有者
    photo_url TEXT,                                      -- 照片URL
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB,
    
    -- 全文搜索索引
    search_vector tsvector GENERATED ALWAYS AS (
        to_tsvector('simple', coalesce(animal_id, '') || ' ' || 
                              coalesce(name, '') || ' ' || 
                              coalesce(ear_tag, ''))
    ) STORED
);

-- 系谱表
-- Pedigree table
CREATE TABLE pedigree (
    animal_id INTEGER PRIMARY KEY REFERENCES animals(id) ON DELETE CASCADE,
    sire_id INTEGER REFERENCES animals(id),              -- 父亲ID
    dam_id INTEGER REFERENCES animals(id),               -- 母亲ID
    generation INTEGER,                                  -- 世代数
    inbreeding_coefficient DECIMAL(10,6),                -- 近交系数
    pedigree_completeness DECIMAL(5,2),                  -- 系谱完整度(%)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 确保不能自己是自己的父母
    CONSTRAINT no_self_parent CHECK (
        animal_id != sire_id AND animal_id != dam_id
    )
);

-- 动物分组表
-- Animal groups table
CREATE TABLE animal_groups (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER REFERENCES organizations(id),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    group_type VARCHAR(50),                              -- 分组类型: breeding/selection/management
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 动物分组成员表
-- Animal group members table
CREATE TABLE animal_group_members (
    group_id INTEGER REFERENCES animal_groups(id) ON DELETE CASCADE,
    animal_id INTEGER REFERENCES animals(id) ON DELETE CASCADE,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (group_id, animal_id)
);

-- ============================================================================
-- 表型数据模块
-- Phenotype Data Module
-- ============================================================================

-- 性状定义表
-- Trait definitions table
CREATE TABLE traits (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,                    -- 性状代码
    name_zh VARCHAR(200) NOT NULL,                       -- 性状名称（中文）
    name_en VARCHAR(200),                                -- 性状名称（英文）
    category VARCHAR(50) NOT NULL,                       -- 类别: growth/reproduction/carcass/quality
    data_type VARCHAR(20) NOT NULL,                      -- 数据类型: continuous/binary/categorical
    unit VARCHAR(50),                                    -- 单位
    min_value DECIMAL(15,4),                             -- 最小值
    max_value DECIMAL(15,4),                             -- 最大值
    description_zh TEXT,
    description_en TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- 表型记录表（使用TimescaleDB优化时序数据）
-- Phenotype records table (optimized with TimescaleDB for time-series data)
CREATE TABLE phenotype_records (
    id BIGSERIAL PRIMARY KEY,
    animal_id INTEGER NOT NULL REFERENCES animals(id) ON DELETE CASCADE,
    trait_id INTEGER NOT NULL REFERENCES traits(id),
    value DECIMAL(15,4) NOT NULL,                        -- 性状值
    measurement_date DATE NOT NULL,                      -- 测量日期
    age_days INTEGER,                                    -- 测量时日龄
    contemporary_group VARCHAR(100),                     -- 同期群
    measurement_method VARCHAR(100),                     -- 测量方法
    technician VARCHAR(100),                             -- 测量人员
    location VARCHAR(200),                               -- 测量地点
    quality_flag VARCHAR(20) DEFAULT 'normal',           -- 质量标记: normal/suspect/outlier
    notes TEXT,                                          -- 备注
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- 为TimescaleDB创建超表（如果使用TimescaleDB）
-- Create hypertable for TimescaleDB (if using TimescaleDB)
-- SELECT create_hypertable('phenotype_records', 'measurement_date', if_not_exists => TRUE);

-- 表型数据质量控制表
-- Phenotype quality control table
CREATE TABLE phenotype_quality_control (
    id SERIAL PRIMARY KEY,
    phenotype_record_id BIGINT REFERENCES phenotype_records(id) ON DELETE CASCADE,
    qc_type VARCHAR(50) NOT NULL,                        -- QC类型: range_check/outlier_detection/consistency
    qc_result VARCHAR(20) NOT NULL,                      -- QC结果: pass/warning/fail
    qc_message TEXT,                                     -- QC消息
    performed_by INTEGER REFERENCES users(id),
    performed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 基因组数据模块
-- Genomic Data Module
-- ============================================================================

-- 基因型文件表
-- Genotype files table
CREATE TABLE genotype_files (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER REFERENCES organizations(id),
    file_name VARCHAR(500) NOT NULL,
    file_path TEXT NOT NULL,                             -- MinIO对象存储路径
    file_format VARCHAR(50) NOT NULL,                    -- 文件格式: plink/vcf/hapmap
    file_size BIGINT,                                    -- 文件大小(bytes)
    num_animals INTEGER,                                 -- 动物数量
    num_markers INTEGER,                                 -- 标记数量
    chip_type VARCHAR(100),                              -- 芯片类型
    genome_build VARCHAR(50),                            -- 基因组版本: OAR3.1/OAR4.0
    upload_status VARCHAR(20) DEFAULT 'pending',         -- 上传状态: pending/processing/completed/failed
    qc_status VARCHAR(20),                               -- QC状态: pending/passed/failed
    uploaded_by INTEGER REFERENCES users(id),
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,
    metadata JSONB
);

-- SNP标记信息表
-- SNP markers table
CREATE TABLE snp_markers (
    id SERIAL PRIMARY KEY,
    marker_name VARCHAR(100) UNIQUE NOT NULL,            -- 标记名称
    chromosome VARCHAR(10) NOT NULL,                     -- 染色体
    position BIGINT NOT NULL,                            -- 物理位置(bp)
    allele_a VARCHAR(10),                                -- 等位基因A
    allele_b VARCHAR(10),                                -- 等位基因B
    genome_build VARCHAR(50),                            -- 基因组版本
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 基因型质量指标表
-- Genotype quality metrics table
CREATE TABLE genotype_quality_metrics (
    id SERIAL PRIMARY KEY,
    genotype_file_id INTEGER REFERENCES genotype_files(id) ON DELETE CASCADE,
    animal_id INTEGER REFERENCES animals(id),
    call_rate DECIMAL(5,4),                              -- 检出率
    heterozygosity DECIMAL(5,4),                         -- 杂合度
    sex_check_result VARCHAR(20),                        -- 性别检查结果: pass/fail
    parent_check_result VARCHAR(20),                     -- 亲子鉴定结果: pass/fail/na
    duplicate_check_result VARCHAR(20),                  -- 重复样本检查: pass/fail
    qc_status VARCHAR(20) DEFAULT 'pending',             -- QC状态: pending/passed/failed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- ============================================================================
-- 育种值与遗传评估模块
-- Breeding Value and Genetic Evaluation Module
-- ============================================================================

-- 育种值评估运行记录表
-- Breeding value evaluation runs table
CREATE TABLE breeding_value_runs (
    id SERIAL PRIMARY KEY,
    run_name VARCHAR(200) NOT NULL,
    organization_id INTEGER REFERENCES organizations(id),
    trait_id INTEGER REFERENCES traits(id),
    method VARCHAR(50) NOT NULL,                         -- 方法: BLUP/GBLUP/ssGBLUP/BayesA/BayesB等
    model_specification TEXT NOT NULL,                   -- 模型规格（JSON格式）
    num_animals INTEGER,                                 -- 参与评估的动物数量
    num_records INTEGER,                                 -- 表型记录数量
    num_markers INTEGER,                                 -- 标记数量（基因组方法）
    use_gpu BOOLEAN DEFAULT FALSE,                       -- 是否使用GPU
    num_threads INTEGER DEFAULT 1,                       -- 线程数
    status VARCHAR(20) DEFAULT 'pending',                -- 状态: pending/running/completed/failed
    started_by INTEGER REFERENCES users(id),
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    computation_time_seconds INTEGER,                    -- 计算耗时(秒)
    log_file_path TEXT,                                  -- 日志文件路径
    error_message TEXT,                                  -- 错误信息
    metadata JSONB
);

-- 育种值结果表
-- Breeding values table
CREATE TABLE breeding_values (
    id BIGSERIAL PRIMARY KEY,
    run_id INTEGER NOT NULL REFERENCES breeding_value_runs(id) ON DELETE CASCADE,
    animal_id INTEGER NOT NULL REFERENCES animals(id) ON DELETE CASCADE,
    trait_id INTEGER NOT NULL REFERENCES traits(id),
    ebv DECIMAL(15,6),                                   -- 估计育种值(EBV)
    reliability DECIMAL(5,4),                            -- 可靠性
    gebv DECIMAL(15,6),                                  -- 基因组育种值(GEBV)
    genomic_reliability DECIMAL(5,4),                    -- 基因组可靠性
    deregressed_ebv DECIMAL(15,6),                       -- 去回归EBV
    parent_average DECIMAL(15,6),                        -- 父母平均
    percentile_rank DECIMAL(5,2),                        -- 百分位排名
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE (run_id, animal_id, trait_id)
);

-- 遗传参数表
-- Genetic parameters table
CREATE TABLE genetic_parameters (
    id SERIAL PRIMARY KEY,
    run_id INTEGER REFERENCES breeding_value_runs(id) ON DELETE CASCADE,
    trait_id INTEGER REFERENCES traits(id),
    trait2_id INTEGER REFERENCES traits(id),             -- 用于遗传相关（可为NULL）
    parameter_type VARCHAR(50) NOT NULL,                 -- 参数类型: heritability/genetic_correlation/phenotypic_correlation
    value DECIMAL(10,6) NOT NULL,
    standard_error DECIMAL(10,6),                        -- 标准误
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE (run_id, trait_id, trait2_id, parameter_type)
);

-- ============================================================================
-- 选配与决策支持模块
-- Mating and Decision Support Module
-- ============================================================================

-- 选配方案表
-- Mating plans table
CREATE TABLE mating_plans (
    id SERIAL PRIMARY KEY,
    plan_name VARCHAR(200) NOT NULL,
    organization_id INTEGER REFERENCES organizations(id),
    breeding_season VARCHAR(50),                         -- 配种季节
    objective TEXT,                                      -- 育种目标
    constraint_type VARCHAR(50),                         -- 约束类型: inbreeding/contribution
    max_inbreeding DECIMAL(5,4),                         -- 最大近交系数
    optimization_method VARCHAR(50),                     -- 优化方法: OCS/linear_programming
    status VARCHAR(20) DEFAULT 'draft',                  -- 状态: draft/approved/executed
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- 选配对表
-- Mating pairs table
CREATE TABLE mating_pairs (
    id SERIAL PRIMARY KEY,
    plan_id INTEGER REFERENCES mating_plans(id) ON DELETE CASCADE,
    sire_id INTEGER NOT NULL REFERENCES animals(id),
    dam_id INTEGER NOT NULL REFERENCES animals(id),
    expected_inbreeding DECIMAL(10,6),                   -- 预期近交系数
    expected_merit DECIMAL(15,6),                        -- 预期育种值
    priority INTEGER,                                    -- 优先级
    status VARCHAR(20) DEFAULT 'planned',                -- 状态: planned/executed/cancelled
    execution_date DATE,                                 -- 执行日期
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT different_parents CHECK (sire_id != dam_id)
);

-- 选种候选表
-- Selection candidates table
CREATE TABLE selection_candidates (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER REFERENCES organizations(id),
    animal_id INTEGER REFERENCES animals(id),
    selection_year INTEGER NOT NULL,
    selection_type VARCHAR(50) NOT NULL,                 -- 选择类型: breeding/replacement/culling
    composite_index DECIMAL(15,6),                       -- 综合指数
    rank_within_sex INTEGER,                             -- 同性别内排名
    selection_decision VARCHAR(20),                      -- 选择决策: selected/rejected/pending
    decision_date DATE,
    decided_by INTEGER REFERENCES users(id),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE (animal_id, selection_year, selection_type)
);

-- 近交系数表
-- Inbreeding coefficients table
CREATE TABLE inbreeding_coefficients (
    id SERIAL PRIMARY KEY,
    animal_id INTEGER UNIQUE REFERENCES animals(id) ON DELETE CASCADE,
    pedigree_inbreeding DECIMAL(10,6),                   -- 基于系谱的近交系数
    genomic_inbreeding DECIMAL(10,6),                    -- 基于基因组的近交系数
    roh_inbreeding DECIMAL(10,6),                        -- 基于ROH的近交系数
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 数据共享与协作模块
-- Data Sharing and Collaboration Module
-- ============================================================================

-- 数据共享协议表
-- Data sharing agreements table
CREATE TABLE data_sharing_agreements (
    id SERIAL PRIMARY KEY,
    provider_org_id INTEGER REFERENCES organizations(id),
    consumer_org_id INTEGER REFERENCES organizations(id),
    agreement_name VARCHAR(200) NOT NULL,
    data_type VARCHAR(50) NOT NULL,                      -- 数据类型: phenotype/genotype/breeding_values
    access_level VARCHAR(20) NOT NULL,                   -- 访问级别: read/write/full
    start_date DATE NOT NULL,
    end_date DATE,
    status VARCHAR(20) DEFAULT 'active',                 -- 状态: active/expired/revoked
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB,
    
    CONSTRAINT different_organizations CHECK (provider_org_id != consumer_org_id)
);

-- 数据访问日志表
-- Data access logs table
CREATE TABLE data_access_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    organization_id INTEGER REFERENCES organizations(id),
    resource_type VARCHAR(50) NOT NULL,                  -- 资源类型
    resource_id INTEGER NOT NULL,                        -- 资源ID
    action VARCHAR(50) NOT NULL,                         -- 操作: view/create/update/delete
    ip_address INET,                                     -- IP地址
    user_agent TEXT,                                     -- 用户代理
    accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 系统配置与日志
-- System Configuration and Logs
-- ============================================================================

-- 系统配置表
-- System configuration table
CREATE TABLE system_config (
    key VARCHAR(100) PRIMARY KEY,
    value TEXT NOT NULL,
    description TEXT,
    updated_by INTEGER REFERENCES users(id),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 审计日志表
-- Audit logs table
CREATE TABLE audit_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    table_name VARCHAR(100),
    record_id INTEGER,
    old_values JSONB,
    new_values JSONB,
    ip_address INET,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 索引创建
-- Index Creation
-- ============================================================================

-- 用户模块索引
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_status ON users(status);
CREATE INDEX idx_user_organizations_org ON user_organizations(organization_id);

-- 动物模块索引
CREATE INDEX idx_animals_org ON animals(organization_id);
CREATE INDEX idx_animals_breed ON animals(breed_id);
CREATE INDEX idx_animals_status ON animals(status);
CREATE INDEX idx_animals_search ON animals USING GIN(search_vector);
CREATE INDEX idx_pedigree_sire ON pedigree(sire_id);
CREATE INDEX idx_pedigree_dam ON pedigree(dam_id);

-- 表型数据索引
CREATE INDEX idx_phenotype_animal ON phenotype_records(animal_id);
CREATE INDEX idx_phenotype_trait ON phenotype_records(trait_id);
CREATE INDEX idx_phenotype_date ON phenotype_records(measurement_date);
CREATE INDEX idx_phenotype_animal_trait ON phenotype_records(animal_id, trait_id);

-- 基因组数据索引
CREATE INDEX idx_genotype_files_org ON genotype_files(organization_id);
CREATE INDEX idx_genotype_files_status ON genotype_files(upload_status, qc_status);
CREATE INDEX idx_snp_markers_chr_pos ON snp_markers(chromosome, position);

-- 育种值索引
CREATE INDEX idx_breeding_value_runs_org ON breeding_value_runs(organization_id);
CREATE INDEX idx_breeding_value_runs_status ON breeding_value_runs(status);
CREATE INDEX idx_breeding_values_run ON breeding_values(run_id);
CREATE INDEX idx_breeding_values_animal ON breeding_values(animal_id);
CREATE INDEX idx_breeding_values_trait ON breeding_values(trait_id);

-- 选配决策索引
CREATE INDEX idx_mating_plans_org ON mating_plans(organization_id);
CREATE INDEX idx_mating_pairs_plan ON mating_pairs(plan_id);
CREATE INDEX idx_selection_candidates_org ON selection_candidates(organization_id);
CREATE INDEX idx_selection_candidates_year ON selection_candidates(selection_year);

-- 日志索引
CREATE INDEX idx_data_access_logs_user ON data_access_logs(user_id);
CREATE INDEX idx_data_access_logs_time ON data_access_logs(accessed_at);
CREATE INDEX idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_time ON audit_logs(created_at);

-- ============================================================================
-- 触发器函数
-- Trigger Functions
-- ============================================================================

-- 更新updated_at时间戳的触发器函数
-- Trigger function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 为需要的表创建触发器
-- Create triggers for tables that need updated_at
CREATE TRIGGER update_organizations_updated_at BEFORE UPDATE ON organizations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_animals_updated_at BEFORE UPDATE ON animals
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_pedigree_updated_at BEFORE UPDATE ON pedigree
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_phenotype_records_updated_at BEFORE UPDATE ON phenotype_records
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- 初始数据插入
-- Initial Data Insertion
-- ============================================================================

-- 插入默认角色
-- Insert default roles
INSERT INTO roles (name, description_zh, description_en) VALUES
    ('super_admin', '超级管理员', 'Super Administrator'),
    ('org_admin', '机构管理员', 'Organization Administrator'),
    ('breeder', '育种员', 'Breeder'),
    ('technician', '技术员', 'Technician'),
    ('viewer', '查看者', 'Viewer');

-- 插入默认权限
-- Insert default permissions
INSERT INTO permissions (name, resource, action, description_zh, description_en) VALUES
    ('manage_users', 'users', 'all', '管理用户', 'Manage users'),
    ('manage_organizations', 'organizations', 'all', '管理机构', 'Manage organizations'),
    ('manage_animals', 'animals', 'all', '管理动物', 'Manage animals'),
    ('view_animals', 'animals', 'read', '查看动物', 'View animals'),
    ('manage_phenotypes', 'phenotypes', 'all', '管理表型数据', 'Manage phenotypes'),
    ('view_phenotypes', 'phenotypes', 'read', '查看表型数据', 'View phenotypes'),
    ('manage_genotypes', 'genotypes', 'all', '管理基因型数据', 'Manage genotypes'),
    ('view_genotypes', 'genotypes', 'read', '查看基因型数据', 'View genotypes'),
    ('run_evaluations', 'breeding_values', 'create', '运行遗传评估', 'Run genetic evaluations'),
    ('view_breeding_values', 'breeding_values', 'read', '查看育种值', 'View breeding values'),
    ('manage_mating_plans', 'mating_plans', 'all', '管理选配方案', 'Manage mating plans'),
    ('view_mating_plans', 'mating_plans', 'read', '查看选配方案', 'View mating plans');

-- 插入常见肉羊品种
-- Insert common meat sheep breeds
INSERT INTO breeds (code, name_zh, name_en, origin_country) VALUES
    ('DOR', '杜泊羊', 'Dorper', 'South Africa'),
    ('SUF', '萨福克羊', 'Suffolk', 'United Kingdom'),
    ('TEX', '特克赛尔羊', 'Texel', 'Netherlands'),
    ('CHAR', '夏洛莱羊', 'Charollais', 'France'),
    ('HU', '湖羊', 'Hu Sheep', 'China'),
    ('SMALL_TAIL_HAN', '小尾寒羊', 'Small Tail Han Sheep', 'China'),
    ('TAN', '滩羊', 'Tan Sheep', 'China');

-- 插入常见性状定义
-- Insert common trait definitions
INSERT INTO traits (code, name_zh, name_en, category, data_type, unit) VALUES
    ('BW', '出生重', 'Birth Weight', 'growth', 'continuous', 'kg'),
    ('WW', '断奶重', 'Weaning Weight', 'growth', 'continuous', 'kg'),
    ('ADG', '日增重', 'Average Daily Gain', 'growth', 'continuous', 'g/day'),
    ('BF', '背膘厚', 'Backfat Thickness', 'carcass', 'continuous', 'mm'),
    ('LMA', '眼肌面积', 'Loin Muscle Area', 'carcass', 'continuous', 'cm²'),
    ('CW', '胴体重', 'Carcass Weight', 'carcass', 'continuous', 'kg'),
    ('DP', '屠宰率', 'Dressing Percentage', 'carcass', 'continuous', '%'),
    ('LS', '产羔数', 'Litter Size', 'reproduction', 'continuous', 'lambs'),
    ('WR', '断奶率', 'Weaning Rate', 'reproduction', 'continuous', '%'),
    ('FEC', '粪便虫卵数', 'Fecal Egg Count', 'health', 'continuous', 'eggs/g');

-- ============================================================================
-- 视图创建
-- View Creation
-- ============================================================================

-- 动物完整信息视图
-- Complete animal information view
CREATE OR REPLACE VIEW v_animals_complete AS
SELECT 
    a.id,
    a.animal_id,
    a.name,
    a.sex,
    a.birth_date,
    EXTRACT(YEAR FROM AGE(COALESCE(a.death_date, CURRENT_DATE), a.birth_date)) AS age_years,
    a.status,
    b.name_zh AS breed_name_zh,
    b.name_en AS breed_name_en,
    o.name_zh AS organization_name_zh,
    o.name_en AS organization_name_en,
    p.sire_id,
    p.dam_id,
    sire.animal_id AS sire_animal_id,
    dam.animal_id AS dam_animal_id,
    p.inbreeding_coefficient,
    ic.genomic_inbreeding,
    a.created_at,
    a.updated_at
FROM animals a
LEFT JOIN breeds b ON a.breed_id = b.id
LEFT JOIN organizations o ON a.organization_id = o.id
LEFT JOIN pedigree p ON a.id = p.animal_id
LEFT JOIN animals sire ON p.sire_id = sire.id
LEFT JOIN animals dam ON p.dam_id = dam.id
LEFT JOIN inbreeding_coefficients ic ON a.id = ic.animal_id;

-- 最新育种值视图
-- Latest breeding values view
CREATE OR REPLACE VIEW v_latest_breeding_values AS
SELECT DISTINCT ON (bv.animal_id, bv.trait_id)
    bv.animal_id,
    a.animal_id AS animal_code,
    a.name AS animal_name,
    bv.trait_id,
    t.name_zh AS trait_name_zh,
    t.name_en AS trait_name_en,
    bv.ebv,
    bv.gebv,
    bv.reliability,
    bv.genomic_reliability,
    bv.percentile_rank,
    bvr.method,
    bvr.completed_at
FROM breeding_values bv
JOIN animals a ON bv.animal_id = a.id
JOIN traits t ON bv.trait_id = t.id
JOIN breeding_value_runs bvr ON bv.run_id = bvr.id
WHERE bvr.status = 'completed'
ORDER BY bv.animal_id, bv.trait_id, bvr.completed_at DESC;

-- ============================================================================
-- 数据库注释
-- Database Comments
-- ============================================================================

COMMENT ON TABLE organizations IS '机构表 - Organizations table';
COMMENT ON TABLE users IS '用户表 - Users table';
COMMENT ON TABLE animals IS '动物表 - Animals table';
COMMENT ON TABLE pedigree IS '系谱表 - Pedigree table';
COMMENT ON TABLE phenotype_records IS '表型记录表 - Phenotype records table';
COMMENT ON TABLE genotype_files IS '基因型文件表 - Genotype files table';
COMMENT ON TABLE breeding_value_runs IS '育种值评估运行记录表 - Breeding value evaluation runs table';
COMMENT ON TABLE breeding_values IS '育种值结果表 - Breeding values table';
COMMENT ON TABLE mating_plans IS '选配方案表 - Mating plans table';

-- ============================================================================
-- 羊场管理模块 (新增)
-- Farm Management Module (NEW)
-- ============================================================================

-- 羊场信息表
-- Farms table
CREATE TABLE farms (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER REFERENCES organizations(id),
    code VARCHAR(50) UNIQUE NOT NULL,                    -- 羊场代码
    name VARCHAR(200) NOT NULL,                          -- 羊场名称
    farm_type VARCHAR(50) NOT NULL,                      -- 类型: breeding/commercial/mixed
    capacity INTEGER,                                     -- 设计存栏量
    current_stock INTEGER DEFAULT 0,                     -- 当前存栏量
    area_hectares DECIMAL(10,2),                         -- 占地面积(公顷)
    address TEXT,                                         -- 详细地址
    longitude DECIMAL(10,7),                             -- 经度
    latitude DECIMAL(10,7),                              -- 纬度
    manager_name VARCHAR(100),                           -- 场长姓名
    manager_phone VARCHAR(50),                           -- 联系电话
    established_date DATE,                               -- 建场日期
    certification VARCHAR(200),                          -- 资质认证
    status VARCHAR(20) DEFAULT 'active',                 -- 状态: active/inactive
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- 羊舍表
-- Barns table
CREATE TABLE barns (
    id SERIAL PRIMARY KEY,
    farm_id INTEGER REFERENCES farms(id) ON DELETE CASCADE,
    code VARCHAR(50) NOT NULL,                           -- 羊舍编号
    name VARCHAR(100) NOT NULL,                          -- 羊舍名称
    barn_type VARCHAR(50) NOT NULL,                      -- 类型: ram/ewe/lamb/fattening
    capacity INTEGER NOT NULL,                           -- 设计容量
    current_count INTEGER DEFAULT 0,                     -- 当前数量
    area_sqm DECIMAL(8,2),                               -- 面积(平方米)
    ventilation_type VARCHAR(50),                        -- 通风类型
    heating_available BOOLEAN DEFAULT FALSE,             -- 是否有供暖
    status VARCHAR(20) DEFAULT 'active',                 -- 状态
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB,
    
    UNIQUE (farm_id, code)
);

-- 动物位置表
-- Animal location table
CREATE TABLE animal_locations (
    id BIGSERIAL PRIMARY KEY,
    animal_id INTEGER REFERENCES animals(id) ON DELETE CASCADE,
    farm_id INTEGER REFERENCES farms(id),
    barn_id INTEGER REFERENCES barns(id),
    pen_number VARCHAR(50),                              -- 栏位号
    entry_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    exit_date TIMESTAMP,
    exit_reason VARCHAR(100),                            -- 转出原因
    
    CONSTRAINT current_location_unique UNIQUE (animal_id, exit_date)
);

-- ============================================================================
-- 饲养管理模块 (新增)
-- Feeding Management Module (NEW)
-- ============================================================================

-- 饲料类型表
-- Feed types table
CREATE TABLE feed_types (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,                    -- 饲料代码
    name VARCHAR(200) NOT NULL,                          -- 饲料名称
    category VARCHAR(50) NOT NULL,                       -- 类别: roughage/concentrate/supplement
    unit VARCHAR(20) DEFAULT 'kg',                       -- 单位
    price_per_unit DECIMAL(10,2),                        -- 单价
    nutritional_values JSONB,                            -- 营养成分
    storage_requirements TEXT,                           -- 储存要求
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 饲料配方表
-- Feed formulas table
CREATE TABLE feed_formulas (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER REFERENCES organizations(id),
    name VARCHAR(200) NOT NULL,                          -- 配方名称
    target_animal_type VARCHAR(50) NOT NULL,             -- 目标动物: ram/pregnant_ewe/lactating_ewe/lamb/fattening
    target_weight_range NUMRANGE,                        -- 目标体重范围(kg)
    daily_amount_kg DECIMAL(6,3),                        -- 日喂量(kg)
    ingredients JSONB NOT NULL,                          -- 配方成分 [{feed_type_id, percentage, amount}]
    nutritional_summary JSONB,                           -- 营养汇总
    cost_per_kg DECIMAL(8,2),                            -- 每公斤成本
    notes TEXT,                                          -- 备注
    is_active BOOLEAN DEFAULT TRUE,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 饲喂计划表
-- Feeding plans table
CREATE TABLE feeding_plans (
    id SERIAL PRIMARY KEY,
    farm_id INTEGER REFERENCES farms(id),
    barn_id INTEGER REFERENCES barns(id),
    formula_id INTEGER REFERENCES feed_formulas(id),
    plan_name VARCHAR(200),
    start_date DATE NOT NULL,
    end_date DATE,
    feeding_times_per_day INTEGER DEFAULT 2,
    feeding_schedule VARCHAR(200),                       -- 饲喂时间表
    is_active BOOLEAN DEFAULT TRUE,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 饲喂记录表
-- Feeding records table
CREATE TABLE feeding_records (
    id BIGSERIAL PRIMARY KEY,
    feeding_plan_id INTEGER REFERENCES feeding_plans(id),
    barn_id INTEGER REFERENCES barns(id),
    feed_date DATE NOT NULL,
    feed_time TIME,
    formula_id INTEGER REFERENCES feed_formulas(id),
    amount_kg DECIMAL(8,3) NOT NULL,                     -- 实际饲喂量
    animal_count INTEGER,                                -- 饲喂头数
    leftover_kg DECIMAL(8,3) DEFAULT 0,                  -- 剩余量
    recorded_by INTEGER REFERENCES users(id),
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    metadata JSONB
);

-- 饲料库存表
-- Feed inventory table
CREATE TABLE feed_inventory (
    id SERIAL PRIMARY KEY,
    farm_id INTEGER REFERENCES farms(id),
    feed_type_id INTEGER REFERENCES feed_types(id),
    batch_number VARCHAR(100),                           -- 批次号
    quantity_kg DECIMAL(12,2) NOT NULL,                  -- 库存量
    purchase_date DATE,
    expiry_date DATE,
    purchase_price DECIMAL(10,2),
    supplier VARCHAR(200),
    storage_location VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 健康管理模块 (新增)
-- Health Management Module (NEW)
-- ============================================================================

-- 疾病字典表
-- Disease dictionary table
CREATE TABLE diseases (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,                    -- 疾病代码
    name_zh VARCHAR(200) NOT NULL,                       -- 疾病名称(中文)
    name_en VARCHAR(200),                                -- 疾病名称(英文)
    category VARCHAR(50) NOT NULL,                       -- 类别: infectious/parasitic/nutritional/other
    symptoms TEXT,                                       -- 症状
    treatment TEXT,                                      -- 治疗方法
    prevention TEXT,                                     -- 预防措施
    quarantine_days INTEGER,                             -- 隔离天数
    is_reportable BOOLEAN DEFAULT FALSE,                 -- 是否需要上报
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 健康检查记录表
-- Health check records table
CREATE TABLE health_records (
    id BIGSERIAL PRIMARY KEY,
    animal_id INTEGER NOT NULL REFERENCES animals(id) ON DELETE CASCADE,
    check_date DATE NOT NULL,
    check_type VARCHAR(50) NOT NULL,                     -- 类型: routine/diagnostic/emergency
    body_temperature DECIMAL(4,1),                       -- 体温(℃)
    body_weight DECIMAL(8,2),                            -- 体重(kg)
    body_condition_score DECIMAL(3,1),                   -- 体况评分(1-5)
    respiratory_rate INTEGER,                            -- 呼吸频率
    heart_rate INTEGER,                                  -- 心率
    appetite VARCHAR(20),                                -- 食欲: good/fair/poor
    fecal_condition VARCHAR(50),                         -- 粪便状态
    symptoms TEXT,                                       -- 症状描述
    disease_id INTEGER REFERENCES diseases(id),
    diagnosis TEXT,                                      -- 诊断结果
    treatment TEXT,                                      -- 治疗方案
    medication TEXT,                                     -- 用药情况
    veterinarian VARCHAR(100),                           -- 兽医
    follow_up_date DATE,                                 -- 复查日期
    is_quarantined BOOLEAN DEFAULT FALSE,               -- 是否隔离
    quarantine_location VARCHAR(200),
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- 疫苗类型表
-- Vaccine types table
CREATE TABLE vaccine_types (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,                    -- 疫苗代码
    name VARCHAR(200) NOT NULL,                          -- 疫苗名称
    target_disease VARCHAR(200),                         -- 预防疾病
    manufacturer VARCHAR(200),                           -- 生产厂家
    dosage VARCHAR(100),                                 -- 剂量
    injection_route VARCHAR(50),                         -- 接种途径: subcutaneous/intramuscular
    immunity_duration_days INTEGER,                      -- 免疫有效期(天)
    booster_interval_days INTEGER,                       -- 加强免疫间隔(天)
    storage_temperature VARCHAR(50),                     -- 储存温度
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 免疫接种记录表
-- Vaccination records table
CREATE TABLE vaccination_records (
    id BIGSERIAL PRIMARY KEY,
    animal_id INTEGER NOT NULL REFERENCES animals(id) ON DELETE CASCADE,
    vaccine_type_id INTEGER REFERENCES vaccine_types(id),
    vaccination_date DATE NOT NULL,
    batch_number VARCHAR(100),                           -- 疫苗批号
    dosage VARCHAR(50),                                  -- 实际剂量
    injection_site VARCHAR(50),                          -- 接种部位
    reaction VARCHAR(200),                               -- 过敏反应
    next_vaccination_date DATE,                          -- 下次接种日期
    administered_by VARCHAR(100),                        -- 接种人员
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- 驱虫记录表
-- Deworming records table
CREATE TABLE deworming_records (
    id BIGSERIAL PRIMARY KEY,
    animal_id INTEGER REFERENCES animals(id) ON DELETE CASCADE,
    barn_id INTEGER REFERENCES barns(id),               -- 支持群体驱虫
    deworming_date DATE NOT NULL,
    drug_name VARCHAR(200) NOT NULL,                     -- 驱虫药名称
    drug_batch VARCHAR(100),                             -- 药品批号
    dosage VARCHAR(50),                                  -- 剂量
    administration_route VARCHAR(50),                    -- 给药途径
    target_parasites VARCHAR(200),                       -- 目标寄生虫
    withdrawal_days INTEGER,                             -- 休药期(天)
    next_deworming_date DATE,                            -- 下次驱虫日期
    administered_by VARCHAR(100),
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 防疫计划表
-- Immunization plans table
CREATE TABLE immunization_plans (
    id SERIAL PRIMARY KEY,
    farm_id INTEGER REFERENCES farms(id),
    plan_name VARCHAR(200) NOT NULL,
    year INTEGER NOT NULL,
    status VARCHAR(20) DEFAULT 'draft',                  -- draft/approved/executing/completed
    items JSONB NOT NULL,                                -- 计划项目列表
    created_by INTEGER REFERENCES users(id),
    approved_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 繁殖管理模块 (新增)
-- Reproduction Management Module (NEW)
-- ============================================================================

-- 发情记录表
-- Estrus records table
CREATE TABLE estrus_records (
    id BIGSERIAL PRIMARY KEY,
    animal_id INTEGER NOT NULL REFERENCES animals(id) ON DELETE CASCADE,
    estrus_date DATE NOT NULL,
    detection_method VARCHAR(50),                        -- 检测方法: visual/teaser_ram/hormone
    estrus_signs TEXT,                                   -- 发情表现
    intensity VARCHAR(20),                               -- 强度: weak/moderate/strong
    is_synchronized BOOLEAN DEFAULT FALSE,              -- 是否同期发情
    synchronization_protocol VARCHAR(200),              -- 同期发情方案
    recorded_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 配种记录表
-- Breeding records table
CREATE TABLE breeding_records (
    id BIGSERIAL PRIMARY KEY,
    dam_id INTEGER NOT NULL REFERENCES animals(id),
    sire_id INTEGER NOT NULL REFERENCES animals(id),
    breeding_date DATE NOT NULL,
    breeding_type VARCHAR(50) NOT NULL,                  -- 类型: natural/ai/embryo_transfer
    ai_technician VARCHAR(100),                          -- 配种员
    semen_batch VARCHAR(100),                            -- 精液批号
    semen_dose INTEGER,                                  -- 精液剂量
    breeding_score VARCHAR(20),                          -- 配种评分
    estrus_record_id INTEGER REFERENCES estrus_records(id),
    notes TEXT,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT different_parents CHECK (dam_id != sire_id)
);

-- 妊娠检查记录表
-- Pregnancy check records table
CREATE TABLE pregnancy_records (
    id BIGSERIAL PRIMARY KEY,
    animal_id INTEGER NOT NULL REFERENCES animals(id),
    breeding_record_id INTEGER REFERENCES breeding_records(id),
    check_date DATE NOT NULL,
    check_method VARCHAR(50),                            -- 方法: ultrasound/palpation/blood_test
    pregnancy_status VARCHAR(20) NOT NULL,               -- 状态: pregnant/not_pregnant/uncertain
    estimated_fetus_count INTEGER,                       -- 预估胎儿数
    fetus_age_days INTEGER,                              -- 胎龄(天)
    expected_lambing_date DATE,                          -- 预产期
    notes TEXT,
    checked_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 产羔记录表
-- Lambing records table
CREATE TABLE lambing_records (
    id BIGSERIAL PRIMARY KEY,
    dam_id INTEGER NOT NULL REFERENCES animals(id),
    sire_id INTEGER REFERENCES animals(id),
    breeding_record_id INTEGER REFERENCES breeding_records(id),
    lambing_date DATE NOT NULL,
    lambing_time TIME,
    lambing_type VARCHAR(20),                            -- 类型: natural/assisted/cesarean
    gestation_days INTEGER,                              -- 妊娠天数
    litter_size INTEGER NOT NULL,                        -- 窝产仔数
    born_alive INTEGER,                                  -- 产活仔数
    born_dead INTEGER DEFAULT 0,                         -- 死胎数
    lamb_weights JSONB,                                  -- 羔羊出生重列表
    dam_condition VARCHAR(50),                           -- 母羊状态
    complications TEXT,                                  -- 难产/并发症
    assisted_by VARCHAR(100),                            -- 助产人员
    notes TEXT,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 断奶记录表
-- Weaning records table
CREATE TABLE weaning_records (
    id BIGSERIAL PRIMARY KEY,
    animal_id INTEGER NOT NULL REFERENCES animals(id),
    lambing_record_id INTEGER REFERENCES lambing_records(id),
    weaning_date DATE NOT NULL,
    weaning_age_days INTEGER,                            -- 断奶日龄
    weaning_weight DECIMAL(6,2),                         -- 断奶重(kg)
    weaning_method VARCHAR(50),                          -- 断奶方式
    post_weaning_group_id INTEGER REFERENCES animal_groups(id),
    notes TEXT,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 生长发育模块 (新增)
-- Growth Development Module (NEW)
-- ============================================================================

-- 生长测定记录表
-- Growth measurement records table
CREATE TABLE growth_records (
    id BIGSERIAL PRIMARY KEY,
    animal_id INTEGER NOT NULL REFERENCES animals(id) ON DELETE CASCADE,
    measurement_date DATE NOT NULL,
    age_days INTEGER,                                    -- 日龄
    body_weight DECIMAL(8,2),                            -- 体重(kg)
    body_height DECIMAL(6,2),                            -- 体高(cm)
    body_length DECIMAL(6,2),                            -- 体长(cm)
    chest_girth DECIMAL(6,2),                            -- 胸围(cm)
    chest_depth DECIMAL(6,2),                            -- 胸深(cm)
    chest_width DECIMAL(6,2),                            -- 胸宽(cm)
    hip_width DECIMAL(6,2),                              -- 臀宽(cm)
    cannon_circumference DECIMAL(6,2),                   -- 管围(cm)
    backfat_thickness DECIMAL(5,2),                      -- 背膘厚(mm) - 超声波
    loin_eye_area DECIMAL(6,2),                          -- 眼肌面积(cm²) - 超声波
    ultrasound_used BOOLEAN DEFAULT FALSE,
    measurement_method VARCHAR(50),                      -- 测定方法
    recorded_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- 日增重计算视图
-- Daily gain calculation view
CREATE OR REPLACE VIEW v_average_daily_gain AS
SELECT 
    g1.animal_id,
    g1.measurement_date AS start_date,
    g2.measurement_date AS end_date,
    g1.body_weight AS start_weight,
    g2.body_weight AS end_weight,
    g2.age_days - g1.age_days AS days_interval,
    CASE 
        WHEN (g2.age_days - g1.age_days) > 0 
        THEN ROUND(((g2.body_weight - g1.body_weight) / (g2.age_days - g1.age_days))::numeric * 1000, 2)
        ELSE NULL 
    END AS adg_grams
FROM growth_records g1
JOIN growth_records g2 ON g1.animal_id = g2.animal_id 
    AND g2.measurement_date > g1.measurement_date
    AND g2.body_weight > g1.body_weight;

-- ============================================================================
-- 物联网集成模块 (新增)
-- IoT Integration Module (NEW)
-- ============================================================================

-- 物联网设备表
-- IoT devices table
CREATE TABLE iot_devices (
    id SERIAL PRIMARY KEY,
    farm_id INTEGER REFERENCES farms(id),
    barn_id INTEGER REFERENCES barns(id),
    device_type VARCHAR(50) NOT NULL,                    -- 类型: scale/rfid_reader/temperature_sensor/camera
    device_sn VARCHAR(100) UNIQUE NOT NULL,              -- 设备序列号
    device_name VARCHAR(200),                            -- 设备名称
    manufacturer VARCHAR(100),                           -- 生产厂家
    model VARCHAR(100),                                  -- 型号
    ip_address INET,                                     -- IP地址
    mac_address MACADDR,                                 -- MAC地址
    location VARCHAR(200),                               -- 安装位置
    status VARCHAR(20) DEFAULT 'offline',                -- 状态: online/offline/error
    last_heartbeat TIMESTAMP,                            -- 最后心跳时间
    firmware_version VARCHAR(50),                        -- 固件版本
    config JSONB,                                        -- 配置信息
    installed_at DATE,                                   -- 安装日期
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 物联网数据表（高频时序数据）
-- IoT data table (high-frequency time-series)
CREATE TABLE iot_data (
    id BIGSERIAL,
    time TIMESTAMPTZ NOT NULL,
    device_id INTEGER NOT NULL REFERENCES iot_devices(id),
    metric_type VARCHAR(50) NOT NULL,                    -- 指标类型: weight/temperature/humidity/activity
    metric_value DECIMAL(15,4) NOT NULL,                 -- 指标值
    unit VARCHAR(20),                                    -- 单位
    animal_id INTEGER REFERENCES animals(id),            -- 关联动物(如称重数据)
    quality VARCHAR(20) DEFAULT 'good',                  -- 数据质量: good/suspect/error
    metadata JSONB,
    
    PRIMARY KEY (id, time)
);

-- 为TimescaleDB创建超表（如果使用）
-- CREATE SELECT create_hypertable('iot_data', 'time', if_not_exists => TRUE);

-- 自动称重记录表
-- Auto weighing records table
CREATE TABLE auto_weighing_records (
    id BIGSERIAL PRIMARY KEY,
    device_id INTEGER REFERENCES iot_devices(id),
    animal_id INTEGER REFERENCES animals(id),
    rfid_tag VARCHAR(100),                               -- 电子耳标
    weighing_time TIMESTAMPTZ NOT NULL,
    weight_kg DECIMAL(8,2) NOT NULL,
    weight_unit VARCHAR(10) DEFAULT 'kg',
    is_valid BOOLEAN DEFAULT TRUE,
    validation_status VARCHAR(50),                       -- 校验状态
    synced_to_growth BOOLEAN DEFAULT FALSE,             -- 是否已同步到生长记录
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 新增模块索引
-- New Module Indexes
-- ============================================================================

-- 羊场管理索引
CREATE INDEX idx_farms_org ON farms(organization_id);
CREATE INDEX idx_barns_farm ON barns(farm_id);
CREATE INDEX idx_animal_locations_animal ON animal_locations(animal_id);
CREATE INDEX idx_animal_locations_farm ON animal_locations(farm_id);

-- 饲养管理索引
CREATE INDEX idx_feeding_records_date ON feeding_records(feed_date);
CREATE INDEX idx_feeding_records_barn ON feeding_records(barn_id);
CREATE INDEX idx_feed_inventory_farm ON feed_inventory(farm_id);

-- 健康管理索引
CREATE INDEX idx_health_records_animal ON health_records(animal_id);
CREATE INDEX idx_health_records_date ON health_records(check_date);
CREATE INDEX idx_vaccination_records_animal ON vaccination_records(animal_id);
CREATE INDEX idx_vaccination_records_date ON vaccination_records(vaccination_date);

-- 繁殖管理索引
CREATE INDEX idx_breeding_records_dam ON breeding_records(dam_id);
CREATE INDEX idx_breeding_records_sire ON breeding_records(sire_id);
CREATE INDEX idx_breeding_records_date ON breeding_records(breeding_date);
CREATE INDEX idx_pregnancy_records_animal ON pregnancy_records(animal_id);
CREATE INDEX idx_lambing_records_dam ON lambing_records(dam_id);
CREATE INDEX idx_lambing_records_date ON lambing_records(lambing_date);

-- 生长发育索引
CREATE INDEX idx_growth_records_animal ON growth_records(animal_id);
CREATE INDEX idx_growth_records_date ON growth_records(measurement_date);
CREATE INDEX idx_growth_records_animal_date ON growth_records(animal_id, measurement_date);

-- 物联网索引
CREATE INDEX idx_iot_devices_farm ON iot_devices(farm_id);
CREATE INDEX idx_iot_devices_status ON iot_devices(status);
CREATE INDEX idx_iot_data_device ON iot_data(device_id);
CREATE INDEX idx_iot_data_time ON iot_data(time DESC);
CREATE INDEX idx_auto_weighing_animal ON auto_weighing_records(animal_id);
CREATE INDEX idx_auto_weighing_time ON auto_weighing_records(weighing_time);

-- ============================================================================
-- 新增模块表注释
-- New Module Table Comments  
-- ============================================================================

COMMENT ON TABLE farms IS '羊场信息表 - Farms table';
COMMENT ON TABLE barns IS '羊舍表 - Barns table';
COMMENT ON TABLE animal_locations IS '动物位置表 - Animal location table';
COMMENT ON TABLE feed_types IS '饲料类型表 - Feed types table';
COMMENT ON TABLE feed_formulas IS '饲料配方表 - Feed formulas table';
COMMENT ON TABLE feeding_plans IS '饲喂计划表 - Feeding plans table';
COMMENT ON TABLE feeding_records IS '饲喂记录表 - Feeding records table';
COMMENT ON TABLE feed_inventory IS '饲料库存表 - Feed inventory table';
COMMENT ON TABLE diseases IS '疾病字典表 - Disease dictionary table';
COMMENT ON TABLE health_records IS '健康检查记录表 - Health check records table';
COMMENT ON TABLE vaccine_types IS '疫苗类型表 - Vaccine types table';
COMMENT ON TABLE vaccination_records IS '免疫接种记录表 - Vaccination records table';
COMMENT ON TABLE deworming_records IS '驱虫记录表 - Deworming records table';
COMMENT ON TABLE immunization_plans IS '防疫计划表 - Immunization plans table';
COMMENT ON TABLE estrus_records IS '发情记录表 - Estrus records table';
COMMENT ON TABLE breeding_records IS '配种记录表 - Breeding records table';
COMMENT ON TABLE pregnancy_records IS '妊娠检查记录表 - Pregnancy check records table';
COMMENT ON TABLE lambing_records IS '产羔记录表 - Lambing records table';
COMMENT ON TABLE weaning_records IS '断奶记录表 - Weaning records table';
COMMENT ON TABLE growth_records IS '生长测定记录表 - Growth measurement records table';
COMMENT ON TABLE iot_devices IS '物联网设备表 - IoT devices table';
COMMENT ON TABLE iot_data IS '物联网数据表 - IoT data table';
COMMENT ON TABLE auto_weighing_records IS '自动称重记录表 - Auto weighing records table';

-- ============================================================================
-- 新增触发器
-- New Triggers
-- ============================================================================

CREATE TRIGGER update_farms_updated_at BEFORE UPDATE ON farms
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_barns_updated_at BEFORE UPDATE ON barns
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_feed_formulas_updated_at BEFORE UPDATE ON feed_formulas
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_health_records_updated_at BEFORE UPDATE ON health_records
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_iot_devices_updated_at BEFORE UPDATE ON iot_devices
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- 完成
-- Completed
-- ============================================================================
