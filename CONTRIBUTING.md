# Setup

This repository is using [prek](https://github.com/j178/prek) to handle pre-commit hooks,
so it's better to install the hooks before creating a PR to ensure a good code quality.

# Run tests

## Unit tests

To be able to run the tests, a running database and IRC server are needed.
To create them, just run:
- `scripts/init_db.sh`
- `scripts/init_irc.sh`

On WSL2 on Windows, you will need to run Docker Desktop with the WSL2 based engine first.

After that, you can run `cargo test` to run all tests except the expensive ones.
To also run the expensive tests, use `cargo test -- --include-ignored` instead.

### Debugging

To debug a test, you can run this command:
```shell
TEST_LOG=1 cargo test <test_name> -- --nocapture | bunyan
```
`bunyan` is a program to parse the generated output. You might need to install it, but it is not necessary for the debugging.

## Adding tests data

You can add tests data in `crates/libs/core/tests-data`.
Every table has a corresponding `.csv` file containing its tests data.

If you are adding a new `.csv` file, you need to run the script `./crates/libs/core/tests-data/generate_tests_data_sql.sh`.
