FROM rust:1-slim-bookworm
WORKDIR /app
RUN apt-get update -y \
    && apt-get install -y --no-install-recommends openssl ca-certificates libssl-dev pkg-config \
    && apt-get autoremove -y \
    && apt-get clean -y \
    && rm -rf /var/lib/apt/lists/*

RUN cargo install cargo-tarpaulin

COPY . .
