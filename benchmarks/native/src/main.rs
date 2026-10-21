//! Standalone native kernel timings: same epochs/flags as benchmark_backends.py.
//! No Python interpreter and no Swiss dependency. Run only after other timed jobs.
use libephemeris_core::api::{self, SessionBuilder};
use std::{error::Error, hint::black_box, path::Path, time::Instant};

fn measure(
    mut operation: impl FnMut() -> Result<(), Box<dyn Error>>,
) -> Result<Vec<f64>, Box<dyn Error>> {
    for _ in 0..3 {
        operation()?;
    }
    let mut samples = Vec::new();
    for _ in 0..20 {
        let started = Instant::now();
        operation()?;
        samples.push(started.elapsed().as_secs_f64());
    }
    Ok(samples)
}

fn main() -> Result<(), Box<dyn Error>> {
    let paths: Vec<String> = std::env::args().skip(1).collect();
    if paths.is_empty() {
        return Err("expected one or more LEB paths".into());
    }
    let file_count = paths.len();
    let started = Instant::now();
    let mut builder = SessionBuilder::isolated();
    for path in &paths {
        builder.leb_file(Path::new(path))?;
    }
    let session = builder.build()?;
    let setup = started.elapsed().as_secs_f64();
    let flags = api::FLG_SWIEPH | api::FLG_SPEED;
    let positions = measure(|| {
        for day in 0..10 {
            for body in 0..10 {
                black_box(session.calc_ut(2451545.0 + f64::from(day) * 31.125, body, flags)?);
            }
        }
        Ok(())
    })?;
    let houses = measure(|| {
        for day in 0..100 {
            black_box(session.houses_ex(
                2451545.0 + f64::from(day) * 0.125,
                0,
                41.9028,
                12.4964,
                b'P',
            )?);
        }
        Ok(())
    })?;
    println!(
        "{{\"file_count\":{file_count},\"setup_s\":{setup},\"calc_ut_100_samples_s\":{positions:?},\"houses_100_samples_s\":{houses:?}}}"
    );
    Ok(())
}
