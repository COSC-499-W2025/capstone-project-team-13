# src/database.py
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import json
import os

# ============================================
# DATABASE 1: PROJECT DATA
# ============================================

Base1 = declarative_base()

class Project(Base1):
    """Store basic project information"""
    __tablename__ = 'projects'
    
    id = Column(Integer, primary_key=True)
    
    # Basic info
    name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    
    # Dates
    date_created = Column(DateTime)
    date_modified = Column(DateTime)
    
    # Metrics
    lines_of_code = Column(Integer, default=0)
    file_count = Column(Integer, default=0)
    
    # Type
    project_type = Column(String(50))  # 'visual/media', 'code', or 'text'
    
    # Languages & Frameworks (stored as JSON)
    _languages = Column('languages', Text)  # JSON array: ["Python", "JavaScript"]
    _frameworks = Column('frameworks', Text)  # JSON array: ["Django", "React"]
    
    # Relationships
    files = relationship('File', back_populates='project', cascade='all, delete-orphan')
    contributors = relationship('Contributor', back_populates='project', cascade='all, delete-orphan')
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Properties for automatic JSON conversion
    @property
    def languages(self):
        """Get languages as list"""
        return json.loads(self._languages) if self._languages else []
    
    @languages.setter
    def languages(self, value):
        """Set languages from list"""
        self._languages = json.dumps(value) if isinstance(value, list) else value
    
    @property
    def frameworks(self):
        """Get frameworks as list"""
        return json.loads(self._frameworks) if self._frameworks else []
    
    @frameworks.setter
    def frameworks(self, value):
        """Set frameworks from list"""
        self._frameworks = json.dumps(value) if isinstance(value, list) else value
    

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'file_path': self.file_path,
            'date_created': self.date_created.isoformat() if self.date_created else None,
            'date_modified': self.date_modified.isoformat() if self.date_modified else None,
            'lines_of_code': self.lines_of_code,
            'file_count': self.file_count,
            'project_type': self.project_type,
            'languages': self.languages,
            'frameworks': self.frameworks,
        }


class File(Base1):
    """Store file information per project"""
    __tablename__ = 'files'
    
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False)
    
    # File info
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(50))  # Extension: .py, .jpg, .txt, etc.
    file_size = Column(Integer)  # Size in bytes
    
    # Dates
    file_created = Column(DateTime)
    file_modified = Column(DateTime)
    
    # Relationship
    project = relationship('Project', back_populates='files')
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'project_id': self.project_id,
            'file_path': self.file_path,
            'file_type': self.file_type,
            'file_size': self.file_size,
            'file_created': self.file_created.isoformat() if self.file_created else None,
            'file_modified': self.file_modified.isoformat() if self.file_modified else None,
        }


class Contributor(Base1):
    """Store contributor information (for Git repos)"""
    __tablename__ = 'contributors'
    
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False)
    
    # Contributor info
    name = Column(String(255))
    contributor_identifier = Column(String(255))  # Email, username, etc.
    commit_count = Column(Integer, default=0)
    
    # Relationship
    project = relationship('Project', back_populates='contributors')
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'project_id': self.project_id,
            'name': self.name,
            'contributor_identifier': self.contributor_identifier,
            'commit_count': self.commit_count,
        }

# ============================================
# DATABASE MANAGER
# ============================================

class DatabaseManager:
    """Manages database"""
    
    def __init__(self, data_db_path='data/projects_data.db'):
        """Initialize database"""
        
        # Create data directory if it doesn't exist
        os.makedirs('data', exist_ok=True)
        
        # Database 1: Project Data
        self.data_engine = create_engine(f'sqlite:///{data_db_path}')
        Base1.metadata.create_all(self.data_engine)
        self.DataSession = sessionmaker(bind=self.data_engine)
        
    
    def get_data_session(self):
        """Get a session for project data database"""
        return self.DataSession()
    
    # ============ DATABASE 1: PROJECT DATA OPERATIONS ============
    
    def create_project(self, project_data):
        """Create a new project in data database"""
        session = self.get_data_session()
        try:
            # JSON conversion now handled by model properties
            project = Project(**project_data)
            session.add(project)
            session.commit()
            session.refresh(project)
            return project
        finally:
            session.close()
    
    def get_project(self, project_id):
        """Get a project by ID"""
        session = self.get_data_session()
        try:
            return session.query(Project).filter(Project.id == project_id).first()
        finally:
            session.close()
    
    def get_all_projects(self):
        """Get all projects"""
        session = self.get_data_session()
        try:
            return session.query(Project).all()
        finally:
            session.close()
    
    def update_project(self, project_id, updates):
        """Update a project"""
        session = self.get_data_session()
        try:
            project = session.query(Project).filter(Project.id == project_id).first()
            if project:
                # JSON conversion now handled by model properties
                for key, value in updates.items():
                    setattr(project, key, value)
                project.updated_at = datetime.utcnow()
                session.commit()
                session.refresh(project)
            return project
        finally:
            session.close()
    
    def delete_project(self, project_id):
        """Delete a project"""
        session = self.get_data_session()
        try:
            project = session.query(Project).filter(Project.id == project_id).first()
            if project:
                session.delete(project)
                session.commit()
                return True
            return False
        finally:
            session.close()
    
    # ---- FILE OPERATIONS ----
    
    def add_file_to_project(self, file_data):
        """Add a file to a project"""
        session = self.get_data_session()
        try:
            file_obj = File(**file_data)
            session.add(file_obj)
            session.commit()
            session.refresh(file_obj)
            return file_obj
        finally:
            session.close()
    
    def get_files_for_project(self, project_id):
        """Get all files for a project"""
        session = self.get_data_session()
        try:
            return session.query(File).filter(File.project_id == project_id).all()
        finally:
            session.close()
    
    # ---- CONTRIBUTOR OPERATIONS ----
    
    def add_contributor_to_project(self, contributor_data):
        """Add a contributor to a project"""
        session = self.get_data_session()
        try:
            contributor = Contributor(**contributor_data)
            session.add(contributor)
            session.commit()
            session.refresh(contributor)
            return contributor
        finally:
            session.close()
    
    def get_contributors_for_project(self, project_id):
        """Get all contributors for a project"""
        session = self.get_data_session()
        try:
            return session.query(Contributor).filter(Contributor.project_id == project_id).all()
        finally:
            session.close()
    
    
    # ============ UTILITY OPERATIONS ============
    
    def clear_all_data(self):
        """Clear all data from both databases"""
        # Clear DB1
        session1 = self.get_data_session()
        try:
            session1.query(Contributor).delete()
            session1.query(File).delete()
            session1.query(Project).delete()
            session1.commit()
        finally:
            session1.close()
        
    
    def get_stats(self):
        """Get statistics from both databases"""
        session1 = self.get_data_session()
        
        try:
            stats = {
                'total_projects': session1.query(Project).count(),
                'total_files': session1.query(File).count(),
                'total_contributors': session1.query(Contributor).count(),
            }
            return stats
        finally:
            session1.close()


# Global database manager instance
db_manager = DatabaseManager()