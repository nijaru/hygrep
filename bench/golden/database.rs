use sqlx::{postgres::PgPoolOptions, PgPool};
use std::env;

pub async fn init_db_pool() -> Result<PgPool, sqlx::Error> {
    let database_url = env::var("DATABASE_URL").expect("DATABASE_URL must be set");
    let pool = PgPoolOptions::new()
        .max_connections(50)
        .connect(&database_url)
        .await?;
    Ok(pool)
}\n