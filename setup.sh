echo "Installing necessary packages... (Your sudo password might be needed)"
sudo pacman -S jq --needed
echo "Installing necessary packages... DONE"

DB_NAME=$(jq -r '.MYSQL_DATABASE' constants.json)
DB_MESSAGE_NAME=$(jq -r '.MYSQL_MESSAGE_DATABASE' constants.json)
DB_USERNAME=$(jq -r '.MYSQL_USER' constants.json)
DB_PASSWORD=$(jq -r '.MYSQL_PASSWORD' constants.json)

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
