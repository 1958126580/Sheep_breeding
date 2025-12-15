# ============================================================================
# 国际顶级肉羊育种系统 - CRUD基础服务
# International Top-tier Sheep Breeding System - Base CRUD Service
#
# 文件: base.py
# 功能: 提供通用CRUD操作的基类
# ============================================================================

from typing import TypeVar, Generic, Type, Optional, List, Any, Dict
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from pydantic import BaseModel
import logging

from database import Base

logger = logging.getLogger(__name__)

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseService(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    通用CRUD服务基类
    
    提供标准的创建、读取、更新、删除操作
    
    使用示例:
    ```python
    class FarmService(BaseService[Farm, FarmCreate, FarmUpdate]):
        def __init__(self, db: Session):
            super().__init__(Farm, db)
    ```
    """
    
    def __init__(self, model: Type[ModelType], db: Session):
        """
        初始化服务
        
        Args:
            model: SQLAlchemy模型类
            db: 数据库会话
        """
        self.model = model
        self.db = db
    
    # ========================================================================
    # 创建操作
    # ========================================================================
    
    def create(self, obj_in: CreateSchemaType, **kwargs) -> ModelType:
        """
        创建新记录
        
        Args:
            obj_in: Pydantic创建模型
            **kwargs: 额外字段
        
        Returns:
            创建的模型实例
        """
        obj_data = obj_in.model_dump() if hasattr(obj_in, 'model_dump') else obj_in.dict()
        obj_data.update(kwargs)
        
        db_obj = self.model(**obj_data)
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        
        logger.info(f"创建 {self.model.__name__}: id={db_obj.id}")
        return db_obj
    
    def create_batch(self, objects_in: List[CreateSchemaType], **kwargs) -> List[ModelType]:
        """
        批量创建记录
        
        Args:
            objects_in: Pydantic创建模型列表
            **kwargs: 每条记录的额外字段
        
        Returns:
            创建的模型实例列表
        """
        db_objects = []
        for obj_in in objects_in:
            obj_data = obj_in.model_dump() if hasattr(obj_in, 'model_dump') else obj_in.dict()
            obj_data.update(kwargs)
            db_obj = self.model(**obj_data)
            db_objects.append(db_obj)
        
        self.db.add_all(db_objects)
        self.db.commit()
        
        for obj in db_objects:
            self.db.refresh(obj)
        
        logger.info(f"批量创建 {self.model.__name__}: count={len(db_objects)}")
        return db_objects
    
    # ========================================================================
    # 读取操作
    # ========================================================================
    
    def get(self, id: int) -> Optional[ModelType]:
        """
        根据ID获取单条记录
        
        Args:
            id: 记录ID
        
        Returns:
            模型实例或None
        """
        return self.db.query(self.model).filter(
            self.model.id == id,
            self.model.is_deleted == False
        ).first()
    
    def get_or_404(self, id: int) -> ModelType:
        """
        根据ID获取记录，不存在则抛出异常
        
        Args:
            id: 记录ID
        
        Returns:
            模型实例
        
        Raises:
            ValueError: 记录不存在
        """
        obj = self.get(id)
        if not obj:
            raise ValueError(f"{self.model.__name__} not found with id={id}")
        return obj
    
    def get_by_field(self, field: str, value: Any) -> Optional[ModelType]:
        """
        根据字段值获取单条记录
        
        Args:
            field: 字段名
            value: 字段值
        
        Returns:
            模型实例或None
        """
        return self.db.query(self.model).filter(
            getattr(self.model, field) == value,
            self.model.is_deleted == False
        ).first()
    
    def get_multi(
        self,
        skip: int = 0,
        limit: int = 20,
        order_by: str = "id",
        order_desc: bool = True,
        filters: Dict[str, Any] = None
    ) -> List[ModelType]:
        """
        获取多条记录
        
        Args:
            skip: 跳过条数
            limit: 返回条数
            order_by: 排序字段
            order_desc: 是否降序
            filters: 过滤条件字典
        
        Returns:
            模型实例列表
        """
        query = self.db.query(self.model).filter(self.model.is_deleted == False)
        
        # 应用过滤条件
        if filters:
            for field, value in filters.items():
                if value is not None and hasattr(self.model, field):
                    query = query.filter(getattr(self.model, field) == value)
        
        # 排序
        if hasattr(self.model, order_by):
            order_column = getattr(self.model, order_by)
            query = query.order_by(desc(order_column) if order_desc else asc(order_column))
        
        return query.offset(skip).limit(limit).all()
    
    def count(self, filters: Dict[str, Any] = None) -> int:
        """
        统计记录数
        
        Args:
            filters: 过滤条件
        
        Returns:
            记录数量
        """
        query = self.db.query(self.model).filter(self.model.is_deleted == False)
        
        if filters:
            for field, value in filters.items():
                if value is not None and hasattr(self.model, field):
                    query = query.filter(getattr(self.model, field) == value)
        
        return query.count()
    
    def exists(self, id: int) -> bool:
        """
        检查记录是否存在
        
        Args:
            id: 记录ID
        
        Returns:
            是否存在
        """
        return self.db.query(self.model).filter(
            self.model.id == id,
            self.model.is_deleted == False
        ).count() > 0
    
    # ========================================================================
    # 更新操作
    # ========================================================================
    
    def update(self, id: int, obj_in: UpdateSchemaType) -> Optional[ModelType]:
        """
        更新记录
        
        Args:
            id: 记录ID
            obj_in: Pydantic更新模型
        
        Returns:
            更新后的模型实例
        """
        db_obj = self.get(id)
        if not db_obj:
            return None
        
        update_data = obj_in.model_dump(exclude_unset=True) if hasattr(obj_in, 'model_dump') else obj_in.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        
        self.db.commit()
        self.db.refresh(db_obj)
        
        logger.info(f"更新 {self.model.__name__}: id={id}")
        return db_obj
    
    def update_field(self, id: int, field: str, value: Any) -> Optional[ModelType]:
        """
        更新单个字段
        
        Args:
            id: 记录ID
            field: 字段名
            value: 新值
        
        Returns:
            更新后的模型实例
        """
        db_obj = self.get(id)
        if not db_obj:
            return None
        
        if hasattr(db_obj, field):
            setattr(db_obj, field, value)
            self.db.commit()
            self.db.refresh(db_obj)
        
        return db_obj
    
    # ========================================================================
    # 删除操作
    # ========================================================================
    
    def delete(self, id: int, soft: bool = True, user_id: int = None) -> bool:
        """
        删除记录
        
        Args:
            id: 记录ID
            soft: 是否软删除
            user_id: 删除者ID
        
        Returns:
            是否成功
        """
        db_obj = self.get(id)
        if not db_obj:
            return False
        
        if soft:
            db_obj.soft_delete(user_id)
        else:
            self.db.delete(db_obj)
        
        self.db.commit()
        
        logger.info(f"删除 {self.model.__name__}: id={id}, soft={soft}")
        return True
    
    def restore(self, id: int) -> Optional[ModelType]:
        """
        恢复软删除的记录
        
        Args:
            id: 记录ID
        
        Returns:
            恢复后的模型实例
        """
        db_obj = self.db.query(self.model).filter(
            self.model.id == id,
            self.model.is_deleted == True
        ).first()
        
        if db_obj:
            db_obj.restore()
            self.db.commit()
            self.db.refresh(db_obj)
            logger.info(f"恢复 {self.model.__name__}: id={id}")
        
        return db_obj
