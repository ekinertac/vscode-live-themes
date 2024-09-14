SERVER_USER="deployer"
SERVER_IP="167.172.112.188"
SERVER_DIR="/home/deployer/vscode-live-themes"

DEPLOY_SCRIPT="
    cd $SERVER_DIR
    git pull
    /home/deployer/vscode-live-themes/server/venv/bin/pip install -r requirements.txt
    sudo ln -sfn $SERVER_DIR/server/nginx.conf /etc/nginx/sites-enabled/vscode-live-themes.conf
    sudo systemctl reload nginx
    sudo certbot --nginx -d vscode-live-themes.ekinertac.com
"

ssh $SERVER_USER@$SERVER_IP "$DEPLOY_SCRIPT"