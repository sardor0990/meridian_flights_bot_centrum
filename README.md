https://telegra.ph/CICD-configuration-using-Github-and-Ubuntu-Server-01-30

🧱 CI/CD Setup for a NEW Project (Step-by-Step)

This assumes:

Ubuntu server
Docker + Docker Compose already installed
You deploy via GitHub Actions + SSH
0️⃣ One-time prerequisites (server)
Make sure these exist once per server:

docker --version
docker compose version
git --version
Folder structure (recommended):

~/Documents/projects/
  docker-compose.yml
  your_new_project/
1️⃣ Create project locally
mkdir your_new_project
cd your_new_project
git init
Add:

main.py
requirements.txt
Dockerfile
.gitignore
.gitignore:

.env
__pycache__/
2️⃣ Create .env (DO NOT COMMIT)
touch .env
Example:

BOT_TOKEN=xxxx
⚠️ .env stays:

on server
or local for testing
never in GitHub
3️⃣ Dockerfile (standard)
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
4️⃣ Add service to docker-compose.yml (server)
Edit:

~/Documents/projects/docker-compose.yml
Add:

your_new_project:
  build: ./your_new_project
  container_name: your_new_project
  restart: unless-stopped
  env_file:
    - ./your_new_project/.env
  volumes:
    - ./your_new_project/logs:/app/logs
    - ./your_new_project/data:/app/data
  networks:
    - bot_network
⚠️ No ports needed for Telegram bots (polling)

5️⃣ Copy project to server (first time only)
scp -r your_new_project tmebot@SERVER_IP:~/Documents/projects/
Then on server:

cd ~/Documents/projects/your_new_project
nano .env   # paste BOT_TOKEN
6️⃣ Test locally on server (before CI/CD)
cd ~/Documents/projects
docker compose build your_new_project
docker compose up -d your_new_project
docker logs your_new_project
✅ Bot must work before CI/CD

7️⃣ Create SSH key (if not already)
On your local machine:

ssh-keygen -t ed25519
Copy public key to server:

ssh-copy-id tmebot@SERVER_IP
Private key stays local.

8️⃣ Add GitHub Secrets
GitHub → Repo → Settings → Secrets → Actions

Add:

NameValueSERVER_IPserver IPSERVER_USERtmebotSSH_PRIVATE_KEYcontents of id_ed25519

9️⃣ Create GitHub Actions workflow
Create file:

.github/workflows/deploy.yml

name: Deploy your_new_project

on:
  push:
    branches:
      - master

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Deploy via SSH
        uses: appleboy/ssh-action@v1.0.0
        with:
          host: ${{ secrets.SERVER_IP }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            cd ~/Documents/projects/your_new_project
            git pull origin master

            cd ~/Documents/projects
            docker compose build your_new_project
            docker compose up -d your_new_project
🔟 Push & deploy
git add .
git commit -m "Initial CI/CD setup"
git branch -M master
git remote add origin git@github.com:USER/REPO.git
git push -u origin master
🎉 Deployment runs automatically.

🧠 Mental checklist (save this)
When adding a new project, ask:

 Dockerfile exists?
 .env exists on server?
 Service added to docker-compose.yml?
 Project folder exists on server?
 GitHub Secrets added?
 deploy.yml uses correct service name?
If all yes → CI/CD will work.
