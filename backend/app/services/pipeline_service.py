"""
数据处理管道服务
提供管道执行、沙箱隔离、依赖管理等功能
"""
import os
import sys
import json
import asyncio
import tempfile
import subprocess
import shutil
import time
import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.logger import logger
from app.models.pipeline import Pipeline, PipelineExecution, ExecutionStatus, PipelineStatus
from app.models.task import Task


class PipelineExecutor:
    """管道执行器 - 在隔离环境中执行用户脚本"""
    
    # 脚本模板：包装用户脚本，提供输入输出接口
    SCRIPT_TEMPLATE = '''
# -*- coding: utf-8 -*-
"""
Pipeline Executor Wrapper
自动生成的包装脚本，请勿手动修改
"""
import sys
import json
import traceback

# 读取输入数据
input_file = sys.argv[1]
output_file = sys.argv[2]

with open(input_file, 'r', encoding='utf-8') as f:
    input_data = json.load(f)

# 提供给用户脚本的上下文
task_id = input_data.get('task_id')
extracted_data = input_data.get('extracted_data', {{}})
ocr_text = input_data.get('ocr_text', '')
meta_info = input_data.get('meta_info', {{}})

# 用户脚本的输出变量
output_data = None
error_message = None

try:
    # ========== 用户脚本开始 ==========
{user_script}
    # ========== 用户脚本结束 ==========
    
except Exception as e:
    error_message = str(e)
    traceback.print_exc()

# 写入输出数据
result = {{
    'success': error_message is None,
    'output_data': output_data,
    'error_message': error_message
}}

with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)
'''

    def __init__(self, work_dir: Optional[str] = None):
        """
        初始化执行器
        
        Args:
            work_dir: 工作目录，默认使用临时目录
        """
        self.work_dir = work_dir or tempfile.mkdtemp(prefix='pipeline_')
        self.venv_cache_dir = os.path.join(
            tempfile.gettempdir(), 
            'pipeline_venvs'
        )
        os.makedirs(self.venv_cache_dir, exist_ok=True)
    
    def _get_venv_path(self, pipeline_id: str) -> str:
        """获取管道的虚拟环境路径"""
        return os.path.join(self.venv_cache_dir, f"venv_{pipeline_id}")
    
    def _get_python_executable(self, venv_path: str) -> str:
        """获取虚拟环境的Python可执行文件路径"""
        if sys.platform == 'win32':
            return os.path.join(venv_path, 'Scripts', 'python.exe')
        return os.path.join(venv_path, 'bin', 'python')
    
    async def setup_environment(
        self, 
        pipeline_id: str, 
        requirements: Optional[str] = None,
        force_recreate: bool = False
    ) -> str:
        """
        设置执行环境（创建虚拟环境并安装依赖）
        
        Args:
            pipeline_id: 管道ID
            requirements: 依赖包列表
            force_recreate: 是否强制重建环境
            
        Returns:
            虚拟环境路径
        """
        venv_path = self._get_venv_path(pipeline_id)
        python_exe = self._get_python_executable(venv_path)
        
        # 检查是否需要创建虚拟环境
        if force_recreate and os.path.exists(venv_path):
            shutil.rmtree(venv_path)
        
        if not os.path.exists(venv_path):
            logger.info(f"创建虚拟环境: {venv_path}")
            
            # 创建虚拟环境（使用系统site-packages以继承证书）
            process = await asyncio.create_subprocess_exec(
                sys.executable, '-m', 'venv', '--system-site-packages', venv_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                raise RuntimeError(f"创建虚拟环境失败: {stderr.decode()}")
            
            # 升级pip（使用trusted-host绕过SSL问题）
            await asyncio.create_subprocess_exec(
                python_exe, '-m', 'pip', 'install', '--upgrade', 'pip',
                '--trusted-host', 'pypi.org',
                '--trusted-host', 'pypi.python.org', 
                '--trusted-host', 'files.pythonhosted.org',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
        
        # 安装依赖
        if requirements and requirements.strip():
            logger.info(f"安装依赖包: {pipeline_id}")
            
            # 写入requirements.txt
            req_file = os.path.join(venv_path, 'requirements.txt')
            with open(req_file, 'w', encoding='utf-8') as f:
                f.write(requirements)
            
            # 安装依赖（使用trusted-host绕过SSL问题）
            process = await asyncio.create_subprocess_exec(
                python_exe, '-m', 'pip', 'install', '-r', req_file,
                '--trusted-host', 'pypi.org',
                '--trusted-host', 'pypi.python.org',
                '--trusted-host', 'files.pythonhosted.org',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                logger.error(f"安装依赖失败: {stderr.decode()}")
                raise RuntimeError(f"安装依赖失败: {stderr.decode()}")
            
            logger.info(f"依赖安装完成: {stdout.decode()}")
        
        return venv_path
    
    async def execute(
        self,
        pipeline: Pipeline,
        input_data: Dict[str, Any],
        timeout: Optional[int] = None
    ) -> Tuple[bool, Optional[Dict[str, Any]], str, str, Optional[str]]:
        """
        执行管道脚本
        
        Args:
            pipeline: 管道对象
            input_data: 输入数据
            timeout: 超时时间（秒）
            
        Returns:
            (成功标志, 输出数据, stdout, stderr, 错误信息)
        """
        timeout = timeout or pipeline.timeout_seconds or 300
        
        # 创建临时工作目录
        exec_dir = tempfile.mkdtemp(prefix=f'exec_{pipeline.id}_')
        
        try:
            # 1. 设置环境
            venv_path = await self.setup_environment(
                pipeline.id, 
                pipeline.requirements
            )
            python_exe = self._get_python_executable(venv_path)
            
            # 2. 准备脚本文件
            # 缩进用户脚本（4个空格）
            indented_script = '\n'.join(
                '    ' + line if line.strip() else line
                for line in pipeline.script_content.split('\n')
            )
            
            wrapped_script = self.SCRIPT_TEMPLATE.format(
                user_script=indented_script
            )
            
            script_file = os.path.join(exec_dir, 'pipeline_script.py')
            with open(script_file, 'w', encoding='utf-8') as f:
                f.write(wrapped_script)
            
            # 3. 准备输入输出文件
            input_file = os.path.join(exec_dir, 'input.json')
            output_file = os.path.join(exec_dir, 'output.json')
            
            with open(input_file, 'w', encoding='utf-8') as f:
                json.dump(input_data, f, ensure_ascii=False, indent=2)
            
            # 4. 准备环境变量
            env = os.environ.copy()
            # 设置 UTF-8 编码，避免 Windows 上的 GBK 编码问题
            env['PYTHONIOENCODING'] = 'utf-8'
            env['PYTHONUTF8'] = '1'
            if pipeline.env_variables:
                env.update(pipeline.env_variables)
            
            # 5. 执行脚本
            logger.info(f"开始执行管道脚本: {pipeline.id}")
            
            process = await asyncio.create_subprocess_exec(
                python_exe, script_file, input_file, output_file,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=exec_dir,
                env=env
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return False, None, '', '', f'执行超时（{timeout}秒）'
            
            stdout_str = stdout.decode('utf-8', errors='replace')
            stderr_str = stderr.decode('utf-8', errors='replace')
            
            # 6. 读取输出结果
            if os.path.exists(output_file):
                with open(output_file, 'r', encoding='utf-8') as f:
                    result = json.load(f)
                
                success = result.get('success', False)
                output_data = result.get('output_data')
                error_message = result.get('error_message')
                
                return success, output_data, stdout_str, stderr_str, error_message
            else:
                return False, None, stdout_str, stderr_str, '脚本未生成输出文件'
            
        except Exception as e:
            logger.error(f"管道执行异常: {str(e)}")
            return False, None, '', '', str(e)
        
        finally:
            # 清理临时目录
            try:
                shutil.rmtree(exec_dir)
            except Exception as e:
                logger.warning(f"清理临时目录失败: {str(e)}")
    
    def cleanup_venv(self, pipeline_id: str):
        """清理管道的虚拟环境"""
        venv_path = self._get_venv_path(pipeline_id)
        if os.path.exists(venv_path):
            shutil.rmtree(venv_path)
            logger.info(f"已清理虚拟环境: {venv_path}")


class PipelineService:
    """管道服务 - 管理管道的CRUD和执行"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.executor = PipelineExecutor()
    
    async def get_pipeline_by_rule(self, rule_id: str) -> Optional[Pipeline]:
        """根据规则ID获取管道"""
        stmt = select(Pipeline).where(
            Pipeline.rule_id == rule_id,
            Pipeline.status == "active"
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def create_execution(
        self,
        pipeline: Pipeline,
        task: Task
    ) -> PipelineExecution:
        """创建执行记录"""
        # 准备输入数据
        input_data = {
            'task_id': task.id,
            'extracted_data': task.extracted_data or {},
            'ocr_text': task.ocr_text or '',
            'meta_info': {
                'file_name': task.file_name,
                'page_count': task.page_count,
                'rule_id': task.rule_id,
                'rule_version': task.rule_version,
                'confidence_scores': task.confidence_scores or {},
                'created_at': task.created_at.isoformat() if task.created_at else None,
            }
        }
        
        execution = PipelineExecution(
            pipeline_id=pipeline.id,
            task_id=task.id,
            status=ExecutionStatus.PENDING,
            input_data=input_data
        )
        
        self.db.add(execution)
        await self.db.commit()
        await self.db.refresh(execution)
        
        return execution
    
    async def run_execution(
        self,
        execution: PipelineExecution,
        pipeline: Pipeline
    ) -> PipelineExecution:
        """执行管道"""
        start_time = time.time()
        
        # 更新状态为执行中
        execution.status = ExecutionStatus.RUNNING
        execution.started_at = datetime.utcnow()
        await self.db.commit()
        
        try:
            # 执行脚本
            success, output_data, stdout, stderr, error_msg = await self.executor.execute(
                pipeline=pipeline,
                input_data=execution.input_data,
                timeout=pipeline.timeout_seconds
            )
            
            # 计算耗时
            duration_ms = int((time.time() - start_time) * 1000)
            
            # 更新执行记录
            execution.duration_ms = duration_ms
            execution.stdout = stdout
            execution.stderr = stderr
            execution.completed_at = datetime.utcnow()
            
            if success:
                execution.status = ExecutionStatus.SUCCESS
                execution.output_data = output_data
                logger.info(f"管道执行成功: {execution.id}, 耗时: {duration_ms}ms")
            else:
                execution.status = ExecutionStatus.FAILED
                execution.error_message = error_msg
                logger.error(f"管道执行失败: {execution.id}, 错误: {error_msg}")
            
            await self.db.commit()
            await self.db.refresh(execution)
            
            return execution
            
        except Exception as e:
            execution.status = ExecutionStatus.FAILED
            execution.error_message = str(e)
            execution.completed_at = datetime.utcnow()
            await self.db.commit()
            
            logger.error(f"管道执行异常: {execution.id}, 错误: {str(e)}")
            raise
    
    async def process_task(self, task: Task) -> Optional[Dict[str, Any]]:
        """
        处理任务的管道执行
        
        Args:
            task: 任务对象
            
        Returns:
            处理后的数据，如果没有管道则返回None
        """
        # 获取规则关联的管道
        pipeline = await self.get_pipeline_by_rule(task.rule_id)
        
        if not pipeline:
            logger.debug(f"任务 {task.id} 没有关联的管道")
            return None
        
        logger.info(f"开始执行管道: task={task.id}, pipeline={pipeline.id}")
        
        # 创建执行记录
        execution = await self.create_execution(pipeline, task)
        
        # 执行管道
        execution = await self.run_execution(execution, pipeline)
        
        if execution.status == ExecutionStatus.SUCCESS:
            return execution.output_data
        else:
            # 执行失败，抛出异常让调用方处理
            raise RuntimeError(f"管道执行失败: {execution.error_message}")


# 便捷函数
async def get_pipeline_service(db: AsyncSession) -> PipelineService:
    """获取管道服务实例"""
    return PipelineService(db)
