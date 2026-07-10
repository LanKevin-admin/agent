"""
Web服务器 - FastAPI后端
提供Web界面的API接口，支持打包成EXE后通过浏览器访问
"""
import os
import sys
import logging
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
import uvicorn

from config.settings import config
from agent.skill_based_agent import SkillBasedAgent
from database.models import init_db, get_db
from database import operations as db_ops
from scheduler.task_scheduler import init_scheduler, task_scheduler

logger = logging.getLogger(__name__)

# 初始化数据库
init_db()

# 创建FastAPI应用
app = FastAPI(
    title="飞书RPA监控系统",
    description="AI驱动的RPA运行监控与智能分析系统",
    version="1.0.0"
)

# 配置CORS（允许前端跨域访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Agent实例（单例）- 使用新的SkillBasedAgent
agent = SkillBasedAgent()

# 初始化定时任务调度器
scheduler = init_scheduler(agent)
logger.info("[WebServer] 定时任务调度器已启动")


# ==================== 数据模型 ====================

class ConfigUpdateRequest(BaseModel):
    """配置更新请求"""
    feishu_app_id: Optional[str] = None
    feishu_app_secret: Optional[str] = None
    feishu_chat_id: Optional[str] = None
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    business_emails: Optional[str] = None
    tech_emails: Optional[str] = None
    ai_api_key: Optional[str] = None
    ai_model: Optional[str] = None
    wecom_webhook: Optional[str] = None


class AnalysisRequest(BaseModel):
    """日志分析请求"""
    start_date: str  # YYYY-MM-DD
    end_date: str  # YYYY-MM-DD
    start_time: Optional[str] = None  # HH:MM
    end_time: Optional[str] = None  # HH:MM
    query_text: Optional[str] = None  # 自然语言查询
    session_id: Optional[str] = None  # 会话ID


class TaskCreateRequest(BaseModel):
    """定时任务创建请求"""
    task_name: str
    task_type: str  # analyze/report/sync等
    cron_expression: str  # Cron表达式
    query_text: Optional[str] = None
    description: Optional[str] = None
    enabled: bool = True


# ==================== API路由 ====================

@app.get("/")
async def root():
    """首页 - 返回前端静态页面"""
    web_dir = os.path.join(os.path.dirname(__file__), "web", "dist")
    index_file = os.path.join(web_dir, "index.html")
    
    if os.path.exists(index_file):
        return FileResponse(index_file)
    else:
        return {
            "message": "飞书RPA监控系统API",
            "version": "1.0.0",
            "status": "running",
            "note": "前端未构建，请访问 /docs 查看API文档"
        }


@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "agent": True,
            "feishu": bool(config.feishu.APP_ID and config.feishu.APP_SECRET and config.feishu.TARGET_CHAT_ID),
            "ai": bool(config.ai.API_KEY and config.ai.API_BASE),
            "email": bool(config.email.SMTP_USER and config.email.SMTP_PASSWORD),
            "wecom": bool(config.wecom.WEBHOOK_URL)
        },
        "chat_id": mask_sensitive_data(config.feishu.TARGET_CHAT_ID, 6),
        "ai_model": config.ai.MODEL or "",
        "report_dir": config.report.OUTPUT_DIR or "./reports"
    }


def mask_sensitive_data(data: str, show_chars: int = 4) -> str:
    """
    脱敏处理：只显示前几位和后几位

    Args:
        data: 原始数据
        show_chars: 显示的字符数（设为0则完全隐藏）

    Returns:
        脱敏后的数据

    Examples:
        "sk-abc123xyz789" -> "sk-a****xyz789"
        "cli_1234567890" -> "cli_****7890"
        "password123", 0 -> "****"
    """
    if not data:
        return ""

    # 完全隐藏
    if show_chars == 0:
        return "****"

    # 数据太短，显示***
    if len(data) <= show_chars * 2:
        return "****"

    return data[:show_chars] + "****" + data[-show_chars:]


@app.get("/api/config")
async def get_config():
    """获取当前配置（敏感信息脱敏）"""
    return {
        "feishu": {
            "app_id": mask_sensitive_data(config.feishu.APP_ID, 4),
            "app_secret": mask_sensitive_data(config.feishu.APP_SECRET, 4),
            "chat_id": mask_sensitive_data(config.feishu.TARGET_CHAT_ID, 6)
        },
        "email": {
            "smtp_host": config.email.SMTP_HOST,
            "smtp_port": config.email.SMTP_PORT,
            "smtp_user": config.email.SMTP_USER,
            "smtp_password": mask_sensitive_data(config.email.SMTP_PASSWORD, 0),  # 密码完全隐藏
            "business_emails": ",".join(config.email.BUSINESS_EMAILS),
            "tech_emails": ",".join(config.email.TECH_EMAILS)
        },
        "ai": {
            "api_key": mask_sensitive_data(config.ai.API_KEY, 4),
            "api_base": config.ai.API_BASE,
            "model": config.ai.MODEL
        },
        "wecom": {
            "webhook": mask_sensitive_data(config.wecom.WEBHOOK_URL, 8)
        }
    }


@app.post("/api/config")
async def update_config(req: ConfigUpdateRequest):
    """更新配置"""
    try:
        # 获取.env文件路径，兼容EXE打包
        if getattr(sys, 'frozen', False):
            # EXE模式：写入EXE同目录
            env_file = os.path.join(os.path.dirname(sys.executable), ".env")
        else:
            # 开发模式：写入项目根目录
            env_file = os.path.join(os.path.dirname(__file__), ".env")
        
        # 读取现有配置
        with open(env_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        # 更新配置项
        updates = {
            "FEISHU_APP_ID": req.feishu_app_id,
            "FEISHU_APP_SECRET": req.feishu_app_secret,
            "FEISHU_CHAT_ID": req.feishu_chat_id,
            "SMTP_USER": req.smtp_user,
            "SMTP_PASSWORD": req.smtp_password,
            "BUSINESS_EMAILS": req.business_emails,
            "TECH_EMAILS": req.tech_emails,
            "AI_API_KEY": req.ai_api_key,
            "AI_MODEL": req.ai_model,
            "WECOM_WEBHOOK": req.wecom_webhook
        }

        # 更新.env文件
        new_lines = []
        for line in lines:
            updated = False
            for key, value in updates.items():
                if value is not None and line.startswith(f"{key}="):
                    new_lines.append(f"{key}={value}\n")
                    updated = True
                    break
            if not updated:
                new_lines.append(line)

        with open(env_file, "w", encoding="utf-8") as f:
            f.writelines(new_lines)

        return {"success": True, "message": "配置已更新，重启后生效"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analyze")
async def analyze_logs(req: AnalysisRequest, db: Session = Depends(get_db)):
    """分析RPA日志"""
    try:
        # 生成或使用现有session_id
        session_id = req.session_id or str(uuid.uuid4())

        # 构造Agent查询指令
        if req.query_text:
            query = req.query_text
        else:
            time_desc = f"{req.start_date}"
            if req.start_date != req.end_date:
                time_desc += f"到{req.end_date}"
            if req.start_time:
                time_desc += f" {req.start_time}之后"

            query = f"分析{time_desc}的RPA日志，生成领导汇报并推送"

        # 调用Agent
        result = agent.run(query)

        # 保存对话到数据库
        query_params = {
            "start_date": req.start_date,
            "end_date": req.end_date,
            "start_time": req.start_time,
            "end_time": req.end_time
        }
        db_ops.save_conversation(
            db=db,
            session_id=session_id,
            user_message=query,
            ai_response=result,
            query_params=query_params
        )

        return {
            "success": True,
            "result": result,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"分析失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/reports")
async def list_reports():
    """列出所有历史报告文件"""
    try:
        report_dir = config.report.OUTPUT_DIR
        if not os.path.exists(report_dir):
            return {"reports": []}

        reports = []
        for filename in os.listdir(report_dir):
            if filename.endswith(".txt"):
                filepath = os.path.join(report_dir, filename)
                stat = os.stat(filepath)
                reports.append({
                    "filename": filename,
                    "size": stat.st_size,
                    "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "download_url": f"/api/reports/{filename}"
                })

        # 按创建时间倒序
        reports.sort(key=lambda x: x["created_at"], reverse=True)
        return {"reports": reports}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/reports/{filename}")
async def download_report(filename: str):
    """下载报告文件"""
    filepath = os.path.join(config.report.OUTPUT_DIR, filename)

    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="文件不存在")

    return FileResponse(filepath, filename=filename)


# ==================== 对话历史API ====================

@app.get("/api/conversations/sessions")
async def list_sessions(db: Session = Depends(get_db)):
    """获取所有会话列表"""
    try:
        sessions = db_ops.get_all_sessions(db)
        return {"success": True, "sessions": sessions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/conversations/{session_id}")
async def get_session_history(session_id: str, db: Session = Depends(get_db)):
    """获取指定会话的对话历史"""
    try:
        history = db_ops.get_conversation_history(db, session_id)
        return {
            "success": True,
            "session_id": session_id,
            "messages": [conv.to_dict() for conv in reversed(history)]  # 按时间正序
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/conversations/{session_id}")
async def clear_session_history(session_id: str, db: Session = Depends(get_db)):
    """清空指定会话的历史记录"""
    try:
        db_ops.clear_session(db, session_id)
        return {"success": True, "message": "会话已清空"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 定时任务API ====================

@app.get("/api/tasks")
async def list_tasks(enabled_only: bool = False, db: Session = Depends(get_db)):
    """获取所有定时任务"""
    try:
        tasks = db_ops.get_all_tasks(db, enabled_only=enabled_only)
        return {
            "success": True,
            "tasks": [task.to_dict() for task in tasks]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/tasks")
async def create_task(req: TaskCreateRequest, db: Session = Depends(get_db)):
    """创建定时任务"""
    try:
        # 检查任务名是否重复
        existing = db_ops.get_task_by_name(db, req.task_name)
        if existing:
            raise HTTPException(status_code=400, detail="任务名称已存在")

        task = db_ops.create_task(
            db=db,
            task_name=req.task_name,
            task_type=req.task_type,
            cron_expression=req.cron_expression,
            query_text=req.query_text,
            description=req.description,
            enabled=req.enabled
        )

        # 如果任务启用，添加到调度器
        if task.enabled:
            scheduler.add_task(task)

        return {"success": True, "task": task.to_dict()}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tasks/{task_id}")
async def get_task_detail(task_id: int, db: Session = Depends(get_db)):
    """获取任务详情"""
    try:
        task = db_ops.get_task(db, task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        return {"success": True, "task": task.to_dict()}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/tasks/{task_id}")
async def update_task(task_id: int, req: TaskCreateRequest, db: Session = Depends(get_db)):
    """更新定时任务"""
    try:
        task = db_ops.update_task(
            db=db,
            task_id=task_id,
            task_name=req.task_name,
            task_type=req.task_type,
            cron_expression=req.cron_expression,
            query_text=req.query_text,
            description=req.description,
            enabled=req.enabled
        )
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")

        # 更新调度器中的任务
        scheduler.update_task(task)

        return {"success": True, "task": task.to_dict()}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/tasks/{task_id}")
async def delete_task(task_id: int, db: Session = Depends(get_db)):
    """删除定时任务"""
    try:
        # 从调度器移除
        scheduler.remove_task(task_id)

        # 从数据库删除
        db_ops.delete_task(db, task_id)

        return {"success": True, "message": "任务已删除"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/tasks/{task_id}/executions")
async def get_task_executions(task_id: int, limit: int = 50, db: Session = Depends(get_db)):
    """获取任务执行历史"""
    try:
        executions = db_ops.get_task_executions(db, task_id, limit=limit)
        return {
            "success": True,
            "executions": [exec.to_dict() for exec in executions]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 挂载前端静态文件（打包后会包含）
web_dist_dir = os.path.join(os.path.dirname(__file__), "web", "dist")
if os.path.exists(web_dist_dir):
    app.mount("/assets", StaticFiles(directory=os.path.join(web_dist_dir, "assets")), name="assets")

    @app.get("/")
    async def serve_index():
        """返回前端页面"""
        index_file = os.path.join(web_dist_dir, "index.html")
        return FileResponse(index_file)

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """SPA路由支持"""
        # API路由不处理
        if full_path.startswith("api/") or full_path.startswith("docs"):
            raise HTTPException(status_code=404)

        # 尝试返回文件
        file_path = os.path.join(web_dist_dir, full_path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)

        # 其他路由返回index.html（Vue Router处理）
        index_file = os.path.join(web_dist_dir, "index.html")
        return FileResponse(index_file)


def start_server(host: str = "127.0.0.1", port: int = 8888):
    """启动Web服务器"""
    import webbrowser
    import threading
    import time

    url = f"http://{host}:{port}"

    print("\n" + "=" * 60)
    print("  飞书RPA监控系统 Web服务")
    print("=" * 60)
    print(f"  访问地址: {url}")
    print(f"  API文档: {url}/docs")
    print("=" * 60)
    print("\n  提示：浏览器将自动打开，如未打开请手动访问上述地址")
    print("  关闭程序：按 Ctrl+C 或直接关闭窗口\n")
    print("=" * 60 + "\n")

    # 延迟2秒后自动打开浏览器
    def open_browser():
        time.sleep(2)
        try:
            webbrowser.open(url)
        except:
            pass

    threading.Thread(target=open_browser, daemon=True).start()

    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    start_server()
