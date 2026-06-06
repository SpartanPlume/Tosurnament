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
./tosurnament.sh PRD build
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
./tosurnament.sh TST build
./tosurnament.sh TST up -d
```

Then the commands to stop, restart and delete the containers are the same but with the `TST` parameter instead of `PRD`.

## Backup / Restore

### Backup

To backup the database, use `./scripts/backup_db.sh`.
It will create a `bak.sql` file at the root of the repository.

## Restore

To restore the database, use `./scripts/restore_db <sql_file>`.
To correctly restore a database, you need to only start the `db` part of tosurnament first with: `./tosurnament.sh <phase> up db -d`.
