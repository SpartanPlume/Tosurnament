echo "Installing necessary packages... (Your sudo password might be needed)"
sudo pacman -S jq --needed
echo "Installing necessary packages... DONE"

DB_NAME=$(jq -r '.DB_NAME' constants.json)
DB_MESSAGE_NAME=$(jq -r '.DB_MESSAGE_NAME' constants.json)
DB_USERNAME=$(jq -r '.DB_USERNAME' constants.json)
DB_PASSWORD=$(jq -r '.DB_PASSWORD' constants.json)

python_dependencies=(
    mysqlclient
    requests
    httplib2
    oauth2client
    google-api-python-client
    asyncio
    pycrypto
    cryptography
    discord.py
    Pygments
    blessings
    mysqldb_wrapper
    dateparser
    Babel
    flask-cors
)

echo "Intalling necessary python dependencies..."
for dependency in "${python_dependencies[@]}"
do
    sudo python3 -m pip install -U $dependency
done
echo "Intalling necessary python dependencies... DONE"

echo "Setting up mysql database... (Your mysql root user's password might be needed)"
sudo mysql <<EOF
CREATE USER IF NOT EXISTS '$DB_USERNAME' IDENTIFIED BY '$DB_PASSWORD';
CREATE DATABASE IF NOT EXISTS $DB_NAME;
CREATE DATABASE IF NOT EXISTS $DB_MESSAGE_NAME;
GRANT ALL PRIVILEGES ON $DB_NAME.* TO '$DB_USERNAME';
GRANT ALL PRIVILEGES ON $DB_MESSAGE_NAME.* TO '$DB_USERNAME';
FLUSH PRIVILEGES;
EOF
echo "Setting up mysql database... DONE"
