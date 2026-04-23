use celery::Celery;
use log::{info, error};

#[celery::task]
pub async fn process_background_jobs(job_id: String, payload: String) -> celery::TaskResult<()> {
    info!("Processing background job: {}", job_id);
    // Simulate long running task
    tokio::time::sleep(std::time::Duration::from_secs(5)).await;
    if payload.is_empty() {
        error!("Empty payload for job {}", job_id);
        return Err(celery::error::TaskError::ExpectedError("Empty payload".into()));
    }
    info!("Job {} completed", job_id);
    Ok(())
}\n