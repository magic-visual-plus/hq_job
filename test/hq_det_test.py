from hq_job.job_engine_local import JobEngineLocal, JobDescription


engine = JobEngineLocal("jobs")

engine.run(
    JobDescription(
        command="python scripts/run_train_dino.py",
        args=["/root/autodl-tmp/chengdu_v2_dataset", "/root/autodl-tmp/model/dino/dino-4scale_r50_8xb2-12e_coco_20221202_182705-55b2bba2.pth"],
        working_dir="/root/hq_det",
        output_dir="/root/hq_det/output",
    )
)