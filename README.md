# Tosurnament
Discord bot to help in Discord/spreadsheet relationships

## How to use Tosurnament in your tournament ?

You can check out [the tutorial](https://github.com/SpartanPlume/Tosurnament/wiki/Tutorial) to know how to setup the Tosurnament Bot in your Discord server.

You can also check [the commands](https://github.com/SpartanPlume/Tosurnament/wiki/Tosurnament-commands) directly if you are an experienced user.

## How to add a new language / more translations to Tosurnament ?

First, you need to clone the repository. Then, in the folder `backend/bot/replies`, you will see multiple subfolders with `en.json` file in them. You need to copy this file in the same folder, rename it to the language code in the language you want to translate (`fr.json` for French for example). Now you only need to translate every entries, **but beware** of:
- entries containing `$`, you must not modify the path name to another language (example: `$./no_staff_notification Some other text`, `$./no_staff_notification` must not be changed, but what is after should be changed)
- entries containing `%`, you must not modify the number following them
After you're done translating, just open a Pull Request in this repo and I will check it.

## How to host your own Tosurnament bot ?

Prerequisite:

- Linux on where you want to host the bot (server or on your personal computer)
- mysql/mariadb installed
- python3.8 or later installed
- Clone the repo =)

### Creating the bot (if not already done)

1. Go to the [discord developer portal](https://discord.com/developers/applications)
2. Click the `New Application` button and fill the form

### Get the bot token

1. After selecting the newly created application, click the `Bot` tab in the left
2. Click the `Copy` button below `TOKEN`. You might need to click the `Reset Token` button first.
3. Paste the copied token in the `BOT_TOKEN` field of the `constants.json` file present in the repository

### Get your osu api

1. This can be a little annoying to get, but you need to go to https://osu.ppy.sh/p/api/, login, then close the tab, copy paste the url in the adress bar, and do Shift+ENTER, it should lead you to the correct page and here you can generate/get your osu api key.
2. Paste the copied api key in the `OSU_API_KEY` field of the `constants.json` file present in the repository

### Get your discord ID

1. Activate developer mode in discord if not already done: `Settings -> Appearance -> Advanced -> Developer Mode`
2. Right-click on your name in any channel and click `Copy ID`
3. Paste the copied id in the `BOT_OWNER_ID` field of the `constants.json` file present in the repository

### Set the bot prefix

You can set the bot prefix to anything you want by changing the `COMMAND_PREFIX` field in `constants.json`.

### Set the database username and password

Change the `DB_USERNAME` and `DB_PASSWORD` to anything you want in `constants.json`. You don't need to create the user, it will be created automatically by the `setup.sh` script.

### Set the challonge username and api key (optional)

1. Go to https://challonge.com/settings/developer and copy your API key.
2. Paste the copied id in the `CHALLONGE_API_KEY` field in `constants.json`.
3. Put your challonge username in the `CHALLONGE_USERNAME` field in `constants.json`.

### Use the setup.sh script

Go to the root of the repository and do `./setup.sh`. It will install all the required python dependencies and setup the database.

### Get an encryption key

To get an encryption key you need to:
1. Open a python shell (`python3`)
2. `from cryptography.fernet import Fernet`
3. `Fernet.generate_key()`
4. Copy the generated key and paste it in the `ENCRYPTION_KEY` field in `constants.json`.

## Start the API

You have 2 options to start the api (it works the same way for the bot, see below): create a service or manually use the script.  
Still, the better option is the service, as it will restart even if the script gets killed.

### Option 1: Manual

Change directory to the `backend` folder and use `python3 start_api.py`.

### Option 2: Service

1. Install gunicorn: `pip3 install gunicorn`
2. Create a new service file. For exmaple: `/etc/systemd/system/tosurnament-api.service`
3. Fill the file with:

```ini
[Unit]
Description=Tosurnament api
Requires=mysqld.service
After=mysqld.service

[Service]
WorkingDirectory=/path/to/dir/tosurnament/backend
ExecStart=/usr/local/bin/gunicorn -b localhost:5001 -w 1 start_api:app --access-logfile log/api.log --access-logformat \
'"%(r)s" - %(s)s'
Restart=always

[Install]
WantedBy=multi-user.target
```
4. Modify `WorkingDirectory` with the path to the `backend` directory.
5. Start the service with `sudo systemctl start tosurnament-api`, where `tosurnament-api` is the name of your service file (without the `.service` extension).

## Start the bot

### Option 1: Manual

Just use the `tosurnament.sh` script at the root of the repository.

### Option 2: Service

1. Create a new service file. For example: `/etc/systemd/system/tosurnament.service`
2. Fill the file with:
```ini
[Unit]
Description=Tosurnament bot service
After=mysqld.service
StartLimitIntervalSec=0

[Service]
Restart=always
RestartSec=1
ExecStart=/path/to/tosurnament.sh

[Install]
WantedBy=multi-user.target
```
3. Modify `ExecStart` with the path to the `tosurnament.sh` script.
4. Start the service with `sudo systemctl start tosurnament`, where `tosurnament` is the name of your service file (without the `.service` extension).

## Start the dashboard (optional, only used for setup for now)

### Prerequisites

- yarn or npm
- Caddy or any server
- a setup domain

### Set your discord client id, secret and redirect uri

1. Go to the [discord developer portal](https://discord.com/developers/applications)
2. Select your bot application and click `OAuth2` on the left
3. Copy your `CLIENT ID` and paste it in the `DISCORD_CLIENT_ID` field in `constants.json`
4. Click `Reset Secret` and copy and paste it in the `DISCORD_CLIENT_SECRET` field in `constants.json`
5. Add your redirect uri, it must be your dashboard url followed by `/redirect`. For example: `https://mydashboard.com/redirect`  
Copy it and paste it in the `DISCORD_REDIRECT_URI` field in `constants.json`

### Caddy setup

1. In your Caddyfile (`/etc/caddy/Caddyfile` usually), add the following lines:
```
my.api.url {
        handle {
               reverse_proxy * http://localhost:5001
        }
}

my.dashboard.url {
        handle {
               reverse_proxy * http://localhost:3000
        }
}
```
2. Change the urls to use your domain
3. Use `caddy reload`

## Start the auth (not recommended in selfhost)

TODO

### Start the dashboard

1. In your repository, change directory to `frontend/dashboard`
2. Do `yarn`
3. Do `yarn build`
4. Do `yarn start`

Setup is done. You should be able to access your dashboard using the url you put instead of `my.dashboard.url`.

## Getting updates

If the update only changes the bot, you just need to use the `;update` command.

Else, you need to stop the services. To do that, use `sudo systemctl stop myservice`. Your should stop the bot first, then the api, or the bot might try to do a query while the api is down.  
Then, you pull the changes in the cloned repository (`git pull`).
And finally, you do `sudo systemctl daemon-reload` and restart the services with `sudo systemctl start myservice`.
