# Tosurnament

## Setup

### Secrets

Create a `secrets` folder in the `docker` folder and add the following files in it:
- `db_password.txt`: Password for your db

Example of content for any file:
```
mysuperpassword123
```

## Tests

To be able to run the tests, a running database is needed. The script for to initialize it is `scripts/init.db`.

After that, you can run `cargo test` to run all tests except the expensive ones.  
To also run the expensive tests, use `cargo test -- --include-ignored` instead.
