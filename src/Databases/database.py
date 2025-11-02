# Fixed src/Databases/database.py
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, Index, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, joinedload
from datetime import datetime, timezone
import json
import os
from typing import List, Optional, Dict, Any

# ============================================
# DATABASE MODELS
# ============================================

Base = declarative_base()

class Project(Base):
    """Store comprehensive project information"""
    __tablename__ = 'projects'
    
    id = Column(Integer, primary_key=True)
    
    # Basic info
    name = Column(String(255), nullable=False, index=True)
    file_path = Column(String(500), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    
    # Dates - FIXED: Use timezone-aware datetime
    date_created = Column(DateTime, index=True)
    date_modified = Column(DateTime, index=True)
    date_scanned = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Metrics
    lines_of_code = Column(Integer, default=0)
    word_count = Column(Integer, default=0) #for text documents
    file_count = Column(Integer, default=0)
    total_size_bytes = Column(Integer, default=0)
    
    # Type classification
    project_type = Column(String(50), index=True)
    collaboration_type = Column(String(50))
    
    # Importance and ranking
    importance_score = Column(Float, default=0.0)
    user_rank = Column(Integer, nullable=True)
    is_featured = Column(Boolean, default=False)
    is_hidden = Column(Boolean, default=False)
    
    # Languages & Frameworks (stored as JSON)
    _languages = Column('languages', Text)
    _frameworks = Column('frameworks', Text)
    _skills = Column('skills', Text)
    _tags = Column('tags', Text)
    
    # Success metrics
    success_evidence = Column(Text, nullable=True)
    thumbnail_path = Column(String(500), nullable=True)
    
    # User customizations
    custom_description = Column(Text, nullable=True)
    user_role = Column(String(100), nullable=True)
    
    # Relationships
    files = relationship('File', back_populates='project', cascade='all, delete-orphan', lazy='select')
    contributors = relationship('Contributor', back_populates='project', cascade='all, delete-orphan', lazy='select')
    keywords = relationship('Keyword', back_populates='project', cascade='all, delete-orphan', lazy='select')
    
    # Timestamps - FIXED: Use timezone-aware datetime
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Indexes
    __table_args__ = (
        Index('idx_project_type_date', 'project_type', 'date_modified'),
        Index('idx_importance_featured', 'importance_score', 'is_featured'),
    )
    
    # Properties for JSON fields
    @property
    def languages(self) -> List[str]:
        return json.loads(self._languages) if self._languages else []
    
    @languages.setter
    def languages(self, value: List[str]):
        self._languages = json.dumps(value) if isinstance(value, list) else value
    
    @property
    def frameworks(self) -> List[str]:
        return json.loads(self._frameworks) if self._frameworks else []
    
    @frameworks.setter
    def frameworks(self, value: List[str]):
        self._frameworks = json.dumps(value) if isinstance(value, list) else value
    
    @property
    def skills(self) -> List[str]:
        return json.loads(self._skills) if self._skills else []
    
    @skills.setter
    def skills(self, value: List[str]):
        self._skills = json.dumps(value) if isinstance(value, list) else value
    
    @property
    def tags(self) -> List[str]:
        return json.loads(self._tags) if self._tags else []
    
    @tags.setter
    def tags(self, value: List[str]):
        self._tags = json.dumps(value) if isinstance(value, list) else value
    
    @property
    def success_metrics(self) -> Dict[str, Any]:
        return json.loads(self.success_evidence) if self.success_evidence else {}
    
    @success_metrics.setter
    def success_metrics(self, value: Dict[str, Any]):
        self.success_evidence = json.dumps(value) if isinstance(value, dict) else value
    
    def to_dict(self, include_counts=False) -> Dict[str, Any]:
        """
        Convert to dictionary for API responses
        
        FIXED: Made relationship counts optional and safe
        Use include_counts=True only when session is active
        """
        result = {
            'id': self.id,
            'name': self.name,
            'file_path': self.file_path,
            'description': self.description,
            'date_created': self.date_created.isoformat() if self.date_created else None,
            'date_modified': self.date_modified.isoformat() if self.date_modified else None,
            'date_scanned': self.date_scanned.isoformat() if self.date_scanned else None,
            'lines_of_code': self.lines_of_code,
            'word_count': self.word_count,  
            'file_count': self.file_count,
            'total_size_bytes': self.total_size_bytes,
            'project_type': self.project_type,
            'collaboration_type': self.collaboration_type,
            'importance_score': self.importance_score,
            'user_rank': self.user_rank,
            'is_featured': self.is_featured,
            'is_hidden': self.is_hidden,
            'languages': self.languages,
            'frameworks': self.frameworks,
            'skills': self.skills,
            'tags': self.tags,
            'success_metrics': self.success_metrics,
            'thumbnail_path': self.thumbnail_path,
            'custom_description': self.custom_description,
            'user_role': self.user_role,
        }
        
        # Only include counts if explicitly requested and relationships are loaded
        if include_counts:
            try:
                result['file_count_actual'] = len(self.files) if self.files else 0
                result['contributor_count'] = len(self.contributors) if self.contributors else 0
            except:
                # If relationships aren't loaded, skip counts
                pass
        
        return result


class File(Base):
    """Store detailed file information"""
    __tablename__ = 'files'
    
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, index=True)
    
    # File info
    file_path = Column(String(500), nullable=False)
    file_name = Column(String(255), nullable=False, index=True)
    file_type = Column(String(50), index=True)
    file_size = Column(Integer)
    relative_path = Column(String(500))
    
    # Dates
    file_created = Column(DateTime)
    file_modified = Column(DateTime)
    
    # Content analysis
    lines_of_code = Column(Integer, default=0)
    is_duplicate = Column(Boolean, default=False)
    duplicate_of_id = Column(Integer, ForeignKey('files.id'), nullable=True)
    
    # Ownership
    owner = Column(String(255), nullable=True)
    _editors = Column('editors', Text)
    
    # Relationships
    project = relationship('Project', back_populates='files')
    duplicate_of = relationship('File', remote_side=[id], backref='duplicates')
    
    @property
    def editors(self) -> List[str]:
        return json.loads(self._editors) if self._editors else []
    
    @editors.setter
    def editors(self, value: List[str]):
        self._editors = json.dumps(value) if isinstance(value, list) else value
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'project_id': self.project_id,
            'file_path': self.file_path,
            'file_name': self.file_name,
            'file_type': self.file_type,
            'file_size': self.file_size,
            'relative_path': self.relative_path,
            'file_created': self.file_created.isoformat() if self.file_created else None,
            'file_modified': self.file_modified.isoformat() if self.file_modified else None,
            'lines_of_code': self.lines_of_code,
            'is_duplicate': self.is_duplicate,
            'owner': self.owner,
            'editors': self.editors,
        }


class Contributor(Base):
    """Store contributor information"""
    __tablename__ = 'contributors'
    
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, index=True)
    
    # Contributor info
    name = Column(String(255), nullable=False, index=True)
    contributor_identifier = Column(String(255))
    commit_count = Column(Integer, default=0)
    
    # Contribution metrics
    lines_added = Column(Integer, default=0)
    lines_deleted = Column(Integer, default=0)
    contribution_percent = Column(Float, default=0.0)
    
    # Relationships
    project = relationship('Project', back_populates='contributors')
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'project_id': self.project_id,
            'name': self.name,
            'contributor_identifier': self.contributor_identifier,
            'commit_count': self.commit_count,
            'lines_added': self.lines_added,
            'lines_deleted': self.lines_deleted,
            'contribution_percent': self.contribution_percent,
        }


class Keyword(Base):
    """Store extracted keywords for projects"""
    __tablename__ = 'keywords'
    
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False, index=True)
    
    keyword = Column(String(255), nullable=False, index=True)
    score = Column(Float, default=0.0)
    category = Column(String(50))
    
    # Relationships
    project = relationship('Project', back_populates='keywords')
    
    __table_args__ = (
        Index('idx_project_keyword', 'project_id', 'keyword'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'project_id': self.project_id,
            'keyword': self.keyword,
            'score': self.score,
            'category': self.category,
        }


# ============================================
# DATABASE MANAGER
# ============================================

class DatabaseManager:
    """Manages database operations with proper connection handling"""
    
    def __init__(self, db_path: str = 'data/projects.db'):
        """Initialize database manager - FIXED: Proper engine disposal"""
        os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else 'data', exist_ok=True)
        
        # Create engine with proper settings for Windows
        self.engine = create_engine(
            f'sqlite:///{db_path}',
            connect_args={'check_same_thread': False},
            pool_pre_ping=True  # Verify connections before using
        )
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
    
    def close(self):
        """FIXED: Properly close all connections"""
        self.engine.dispose()
    
    def __enter__(self):
        """Context manager support"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """FIXED: Ensure cleanup on exit"""
        self.close()
    
    def get_session(self):
        """Get a new session"""
        return self.Session()
    
    # ============ PROJECT OPERATIONS ============
    
    def create_project(self, project_data: Dict[str, Any]) -> Project:
        """Create a new project"""
        session = self.get_session()
        try:
            project = Project(**project_data)
            session.add(project)
            session.commit()
            session.refresh(project)
            return project
        finally:
            session.close()
    
    def get_project(self, project_id: int) -> Optional[Project]:
        """Get project by ID with eager loading"""
        session = self.get_session()
        try:
            return session.query(Project).options(
                joinedload(Project.files),
                joinedload(Project.contributors),
                joinedload(Project.keywords)
            ).filter(Project.id == project_id).first()
        finally:
            session.close()
    
    def get_project_by_path(self, file_path: str) -> Optional[Project]:
        """Get project by file path"""
        session = self.get_session()
        try:
            return session.query(Project).filter(Project.file_path == file_path).first()
        finally:
            session.close()
    
    def get_all_projects(self, include_hidden: bool = False) -> List[Project]:
        """Get all projects"""
        session = self.get_session()
        try:
            query = session.query(Project)
            if not include_hidden:
                query = query.filter(Project.is_hidden == False)
            return query.all()
        finally:
            session.close()
    
    def get_featured_projects(self) -> List[Project]:
        """Get featured projects"""
        session = self.get_session()
        try:
            return session.query(Project).filter(
                Project.is_featured == True,
                Project.is_hidden == False
            ).order_by(Project.importance_score.desc()).all()
        finally:
            session.close()
    
    def update_project(self, project_id: int, updates: Dict[str, Any]) -> Optional[Project]:
        """Update project - FIXED: Proper timezone handling"""
        session = self.get_session()
        try:
            project = session.query(Project).filter(Project.id == project_id).first()
            if project:
                for key, value in updates.items():
                    setattr(project, key, value)
                project.updated_at = datetime.now(timezone.utc)
                session.commit()
                session.refresh(project)
            return project
        finally:
            session.close()
    
    def delete_project(self, project_id: int) -> bool:
        """Delete project"""
        session = self.get_session()
        try:
            project = session.query(Project).filter(Project.id == project_id).first()
            if project:
                session.delete(project)
                session.commit()
                return True
            return False
        finally:
            session.close()
    
    # ============ FILE OPERATIONS ============
    
    def add_file_to_project(self, file_data: Dict[str, Any]) -> File:
        """Add file to project"""
        session = self.get_session()
        try:
            file_obj = File(**file_data)
            session.add(file_obj)
            session.commit()
            session.refresh(file_obj)
            return file_obj
        finally:
            session.close()
    
    def get_files_for_project(self, project_id: int) -> List[File]:
        """Get all files for project"""
        session = self.get_session()
        try:
            return session.query(File).filter(File.project_id == project_id).all()
        finally:
            session.close()
    
    # ============ CONTRIBUTOR OPERATIONS ============
    
    def add_contributor_to_project(self, contributor_data: Dict[str, Any]) -> Contributor:
        """Add contributor to project"""
        session = self.get_session()
        try:
            contributor = Contributor(**contributor_data)
            session.add(contributor)
            session.commit()
            session.refresh(contributor)
            return contributor
        finally:
            session.close()
    
    def get_contributors_for_project(self, project_id: int) -> List[Contributor]:
        """Get all contributors for project"""
        session = self.get_session()
        try:
            return session.query(Contributor).filter(Contributor.project_id == project_id).all()
        finally:
            session.close()
    
    # ============ KEYWORD OPERATIONS ============
    
    def add_keyword(self, keyword_data: Dict[str, Any]) -> Keyword:
        """Add keyword to project"""
        session = self.get_session()
        try:
            keyword = Keyword(**keyword_data)
            session.add(keyword)
            session.commit()
            session.refresh(keyword)
            return keyword
        finally:
            session.close()
    
    def get_keywords_for_project(self, project_id: int) -> List[Keyword]:
        """Get all keywords for project"""
        session = self.get_session()
        try:
            return session.query(Keyword).filter(
                Keyword.project_id == project_id
            ).order_by(Keyword.score.desc()).all()
        finally:
            session.close()
    
    # ============ UTILITY OPERATIONS ============
    
    def clear_all_data(self):
        """Clear all data from database"""
        session = self.get_session()
        try:
            session.query(Keyword).delete()
            session.query(Contributor).delete()
            session.query(File).delete()
            session.query(Project).delete()
            session.commit()
        finally:
            session.close()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        session = self.get_session()
        try:
            return {
                'total_projects': session.query(Project).count(),
                'featured_projects': session.query(Project).filter(Project.is_featured == True).count(),
                'total_files': session.query(File).count(),
                'total_contributors': session.query(Contributor).count(),
                'total_keywords': session.query(Keyword).count(),
            }
        finally:
            session.close()


# Global database manager instance
db_manager = DatabaseManager()