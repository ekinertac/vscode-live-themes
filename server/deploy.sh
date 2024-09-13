SERVER_USER="deployer"
SERVER_IP="167.172.112.188"
SERVER_DIR="/home/deployer/vscode-live-themes"

ssh $SERVER_USER@$SERVER_IP "
    cd $SERVER_DIR
    git pull
    sudo ln -sfn $SERVER_DIR/server/nginx.conf /etc/nginx/sites-enabled/vscode-live-themes.conf
    sudo systemctl reload nginx
    sudo certbot --nginx -d vscode-live-themes.ekinertac.com
"