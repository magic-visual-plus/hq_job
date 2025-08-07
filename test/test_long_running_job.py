#!/usr/bin/env python3
"""
测试长时间运行的任务状态更新
"""

import time
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'hq_job'))

from hq_job.job_engine_local import JobEngineLocal
from hq_job.job_engine import JobDescription

def test_long_running_job():
    """测试长时间运行的任务"""
    print("=== 测试长时间运行的任务 ===")
    
    # 创建引擎
    engine = JobEngineLocal()
    
    # 创建一个会运行几秒钟的任务
    job_desc = JobDescription(
        command="python",
        args=["test/script.py"],
        working_dir=".",
        output_dir="./test"
    )
    
    # 提交任务
    job_id = engine.run(job_desc)
    print(f"提交任务: {job_id}")
    
    # 监控任务状态变化
    for i in range(5):
        status = engine.status(job_id)
        print(f"第 {i+1} 次检查 - 任务 {job_id} 状态: {status}")
        
        if status in ['completed', 'failed', 'error']:
            print(f"任务已完成，最终状态: {status}")
            break
        elif status == 'running':
            print("任务正在运行中...")
        elif status == 'postprocessing':
            print("任务正在后处理中...")
        else:
            print(f"任务状态: {status}")
        
        time.sleep(1)
    
    # 获取最终日志
    logs = engine.log(job_id)
    print("\n任务日志:")
    print(logs)
    
    # 检查状态文件
    status_file = f"jobs/job_{job_id}/status.json"
    if os.path.exists(status_file):
        with open(status_file, 'r', encoding='utf-8') as f:
            import json
            status_data = json.load(f)
            print(f"\n状态文件内容: {status_data['status']}")

if __name__ == "__main__":
    test_long_running_job() 