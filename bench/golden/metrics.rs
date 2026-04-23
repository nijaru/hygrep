use prometheus::{Counter, register_counter};
use lazy_static::lazy_static;

lazy_static! {
    pub static ref HTTP_REQUESTS_TOTAL: Counter = register_counter!(
        "http_requests_total",
        "Total number of HTTP requests"
    ).unwrap();
}

pub fn track_request() {
    HTTP_REQUESTS_TOTAL.inc();
}\n