# Tosurnament

## Setup

### Secrets

Create a `secrets` folder in the `docker` folder and add the following files in it:
- `db_password.txt`: Password for your db

Example of content for any file:
```
mysuperpassword123
```

### Start Tosurnament

To start Tosurnament, you will need to run 2 commands:
```shell
./tosurnament.sh build
./tosurnament.sh PRD up -d
```

To stop it, you can run the command:
```shell
./tosurnament.sh PRD stop
```
And to restart it:
```shell
./tosurnament.sh PRD start
```

If you want to remove the containers running Tosurnament, you can run this command:
```shell
./tosurnament.sh PRD down
```

### Test instance of Tosurnament

If you want to test Tosurnament in real conditions without impacting your deployed instance, you can start a test instance with:
```shell
./tosurnament.sh TST up -d
```

Then the commands to stop, restart and delete the containers are the same but with the `TST` parameter instead of `PRD`.

## Tests

### Unit tests

To be able to run the tests, a running database is needed. The script for to initialize it is `scripts/init_db.sh`.  
On WSL2 on Windows, you will need to run Docker Desktop with the WSL2 based engine.

After that, you can run `cargo test` to run all tests except the expensive ones.  
To also run the expensive tests, use `cargo test -- --include-ignored` instead.

#### Debugging

To debug a test, you can run this command:
```shell
TEST_LOG=1 cargo test <test_name> -- --nocapture | bunyan
```
`bunyan` is a program to parse the generated output. You might need to install it, but it is not necessary for the debugging.
