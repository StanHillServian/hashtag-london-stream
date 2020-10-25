# gcloud config set project PROJECT_ID
export GOOGLE_CLOUD_PROJECT="servian-task"

sudo pip3 install -r requirements.txt
python3 pubsub-to-bigquery.py