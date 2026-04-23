mod database;
mod workers;
mod errors;

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    env_logger::init();
    let pool = database::init_db_pool().await?;
    println!("Connected to DB");
    
    // Start HTTP server and workers...
    Ok(())
}\n